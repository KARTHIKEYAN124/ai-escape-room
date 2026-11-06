import unittest
from unittest.mock import patch
from types import SimpleNamespace
from llm import explain_error, list_models, generate

class ProviderError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

class ErrorTests(unittest.TestCase):
    @patch('llm.time.sleep')
    @patch('google.genai.Client')
    def test_transient_failure_retries_same_request_once(self, mock, sleep):
        request = mock.return_value.__enter__.return_value.models.generate_content
        request.side_effect = [ProviderError(503, 'private'), SimpleNamespace(text='A painting waits.')]
        self.assertEqual(generate('fake', 'gemini-test', 'look', 'game'), 'A painting waits.')
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args_list[0], request.call_args_list[1])
        sleep.assert_called_once_with(1)
        self.assertEqual(mock.call_args.kwargs['http_options'].retry_options.attempts, 1)

    @patch('llm.time.sleep')
    @patch('google.genai.Client')
    def test_persistent_outage_stops_after_two_attempts(self, mock, sleep):
        request = mock.return_value.__enter__.return_value.models.generate_content
        request.side_effect = ProviderError(503, 'private')
        with self.assertRaises(ProviderError):
            generate('fake', 'gemini-test', 'look', 'game')
        self.assertEqual(request.call_count, 2)

    @patch('llm.time.sleep')
    @patch('google.genai.Client')
    def test_client_errors_are_not_retried(self, mock, sleep):
        for code in (400, 401, 403, 404, 429):
            request = mock.return_value.__enter__.return_value.models.generate_content
            request.reset_mock()
            request.side_effect = ProviderError(code, 'private')
            with self.assertRaises(ProviderError):
                generate('fake', 'gemini-test', 'look', 'game')
            self.assertEqual(request.call_count, 1)
        sleep.assert_not_called()

    @patch('google.genai.Client')
    def test_model_discovery_filters_and_normalizes(self, mock):
        client = mock.return_value.__enter__.return_value
        client.models.list.return_value = [
            SimpleNamespace(name='models/chat-test', supported_actions=['generateContent']),
            SimpleNamespace(name='models/embedding-test', supported_actions=['embedContent']),
            SimpleNamespace(name='models/no-actions', supported_actions=None),
            SimpleNamespace(name='models/antigravity-preview-05-2026', supported_actions=['generateContent']),
            SimpleNamespace(name='models/chat-test', supported_actions=['generateContent']),
        ]
        self.assertEqual(list_models('fake-key'), ['chat-test'])
        client.models.generate_content.assert_not_called()

    @patch('google.genai.Client')
    def test_interactions_agent_rejected_before_request(self, mock):
        with self.assertRaisesRegex(ValueError, 'Interactions agent selected') as caught:
            generate('fake', 'antigravity-preview-05-2026', 'hello', 'game')
        mock.assert_not_called()
        self.assertIn('requires a Gemini text model', explain_error(caught.exception))

    def test_safe_status_messages(self):
        for code in (400, 401, 403, 404, 429, 500, 503, 504):
            with self.subTest(code=code):
                text = explain_error(ProviderError(code, 'sensitive-key-in-provider-response'))
                self.assertIn(str(code), text)
                self.assertNotIn('sensitive-key', text)

    def test_invalid_key_reason(self):
        text = explain_error(ProviderError(400, 'API_KEY_INVALID sensitive-key'))
        self.assertIn('rejected the API key', text)
        self.assertNotIn('sensitive-key', text)

    def test_unknown_error_does_not_leak(self):
        self.assertNotIn('sensitive-key', explain_error(Exception('sensitive-key')))

    def test_certificate_error_is_actionable_without_raw_message(self):
        text = explain_error(Exception('CERTIFICATE_VERIFY_FAILED sensitive-key'))
        self.assertIn('certificate verification', text)
        self.assertIn('Diagnostic: Exception', text)
        self.assertNotIn('sensitive-key', text)

    def test_string_status_and_sdk_error(self):
        self.assertIn('quota', explain_error(ProviderError('429', 'secret')))
        self.assertIn('SDK compatibility', explain_error(AttributeError('secret')))
        self.assertIn('Diagnostic: AttributeError', explain_error(AttributeError('secret')))

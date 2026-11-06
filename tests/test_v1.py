import unittest
from unittest.mock import patch
from llm import narrate_v1_with_recovery

class NotFound(Exception):
    code = 404

class Forbidden(Exception):
    code = 403

class VersionOneTests(unittest.TestCase):
    @patch('llm.list_models')
    @patch('llm.narrate_v1', return_value='A desk waits.')
    def test_working_model_needs_no_discovery(self, narrate, discover):
        self.assertEqual(narrate_v1_with_recovery('key', 'chosen', [], 'look'), ('A desk waits.', 'chosen'))
        discover.assert_not_called()

    @patch('llm.list_models', return_value=['antigravity-agent', 'gemini-test-flash-image', 'gemini-test-flash'])
    @patch('llm.narrate_v1', side_effect=[NotFound(), 'You see a bookshelf.'])
    def test_stale_model_retries_same_history_once(self, narrate, discover):
        history = [{'role': 'assistant', 'content': 'Welcome'}]
        reply, model = narrate_v1_with_recovery('key', 'retired', history, 'bookshelf')
        self.assertEqual(model, 'gemini-test-flash')
        self.assertEqual(reply, 'You see a bookshelf.')
        self.assertEqual(narrate.call_count, 2)
        self.assertEqual(narrate.call_args.args[2:], (history, 'bookshelf'))
        self.assertEqual(len(history), 1)

    @patch('llm.list_models', return_value=['gemini-test-flash'])
    @patch('llm.narrate_v1', side_effect=NotFound())
    def test_retry_is_bounded(self, narrate, discover):
        with self.assertRaises(NotFound):
            narrate_v1_with_recovery('key', 'retired', [], 'look')
        self.assertEqual(narrate.call_count, 2)

    @patch('llm.list_models')
    @patch('llm.narrate_v1', side_effect=Forbidden())
    def test_access_error_does_not_switch_models(self, narrate, discover):
        with self.assertRaises(Forbidden):
            narrate_v1_with_recovery('key', 'chosen', [], 'look')
        discover.assert_not_called()

    @patch('llm.list_models', return_value=['antigravity-agent'])
    @patch('llm.narrate_v1', side_effect=NotFound())
    def test_no_compatible_model_preserves_failure(self, narrate, discover):
        with self.assertRaises(NotFound):
            narrate_v1_with_recovery('key', 'retired', [], 'look')
        self.assertEqual(narrate.call_count, 1)

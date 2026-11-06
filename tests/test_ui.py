import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class UITests(unittest.TestCase):
    @patch('llm.list_models', return_value=['gemini-test-flash'])
    @patch('llm.narrate_v1')
    def test_v1_recovers_model_and_continues_conversation(self, mock, discover):
        from test_v1 import NotFound
        mock.side_effect = [NotFound(), 'A brass lamp lights the desk.', 'The door opens. [ESCAPED]']
        app = AppTest.from_file('../app.py', default_timeout=15).run()
        app.selectbox[0].select('Version 1 · Interactive').run()
        app.radio[0].set_value('Gemini API').run()
        app.text_input[0].set_value('fake-key').run()
        app.text_input(key='model_id').set_value('retired-model').run()
        app.chat_input[0].set_value('examine desk').run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.text_input(key='model_id').value, 'gemini-test-flash')
        self.assertIn('Retried this turn successfully', app.warning[0].value)
        self.assertEqual(len(app.chat_message), 3)
        app.chat_input[0].set_value('open door').run()
        self.assertEqual(len(app.success), 1)
        self.assertTrue(app.chat_input[0].disabled)

    @patch('llm.describe_v2', side_effect=Exception('private-details'))
    @patch('llm.parse_action', side_effect=Exception('private-details'))
    def test_v2_fallback_notice_survives_rerun(self, parser, narrator):
        app = AppTest.from_file('../app.py', default_timeout=15).run()
        app.radio[0].set_value('Gemini API').run()
        app.text_input[0].set_value('fake-key').run()
        app.chat_input[0].set_value('examine desk').run()
        self.assertIn('offline command parser', app.warning[0].value)
        self.assertNotIn('private-details', app.warning[0].value)
        self.assertEqual(len(app.chat_message), 3)

    @patch('llm.list_models', return_value=['test-flash', 'test-pro'])
    def test_model_selection_updates_request_setting(self, mock):
        app = AppTest.from_file('../app.py', default_timeout=15).run()
        app.radio[0].set_value('Gemini API').run()
        app.text_input[0].set_value('fake-key').run()
        app.button(key='load_models').click().run()
        app.selectbox(key='available_model').select('test-flash').run()
        self.assertEqual(app.text_input(key='model_id').value, 'test-flash')
        app.text_input[0].set_value('different-fake-key').run()
        self.assertEqual(len(app.selectbox), 1)
        self.assertEqual(len(app.exception), 0)

    @patch('llm.narrate_v1')
    def test_provider_failure_is_actionable_and_preserves_history(self, mock):
        from test_errors import ProviderError
        mock.side_effect = ProviderError(429, 'private-key-must-not-appear')
        app = AppTest.from_file('../app.py', default_timeout=15).run()
        app.selectbox[0].select('Version 1 · Interactive').run()
        app.radio[0].set_value('Gemini API').run()
        app.text_input[0].set_value('fake-key-for-mocked-test').run()
        app.chat_input[0].set_value('examine desk').run()
        self.assertEqual(len(app.exception), 0)
        self.assertIn('429', app.error[0].value)
        self.assertNotIn('private-key', app.error[0].value)
        self.assertEqual(len(app.chat_message), 1)

    def test_play_restart_and_switch(self):
        app = AppTest.from_file('../app.py', default_timeout=15).run()
        self.assertEqual(len(app.exception), 0)
        for command in ['examine desk', 'examine bookshelf', 'enter 314 on drawer',
                        'take key', 'use key on painting', 'enter 7249 on door']:
            app.chat_input[0].set_value(command).run()
            self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.success), 1)
        self.assertTrue(app.chat_input[0].disabled)
        app.button[0].click().run()
        self.assertFalse(app.chat_input[0].disabled)
        self.assertEqual(len(app.chat_message), 1)
        app.selectbox[0].select('Version 1 · Interactive').run()
        app.chat_input[0].set_value('examine desk').run()
        self.assertEqual(len(app.exception), 0)

    def test_missing_key_does_not_submit(self):
        app = AppTest.from_file('../app.py', default_timeout=15).run()
        app.radio[0].set_value('Gemini API').run()
        app.text_input[0].set_value('').run()
        app.chat_input[0].set_value('examine desk').run()
        self.assertEqual(len(app.warning), 1)
        self.assertEqual(len(app.chat_message), 1)

if __name__ == '__main__': unittest.main()

import unittest
import os
import logging
from unittest.mock import patch, MagicMock
from llm_chat import generate_response, generate_suggestions

# Set up logging
logging.basicConfig(level=logging.DEBUG,
										format='%(asctime)s - %(levelname)s - %(message)s',
										filename='test-log.txt',
										filemode='w')

logger = logging.getLogger(__name__)

class TestLLMChat(unittest.TestCase):

		def setUp(self):
				logger.info(f"Starting test: {self._testMethodName}")

		def tearDown(self):
				logger.info(f"Finished test: {self._testMethodName}\n")

		@patch('llm_chat.requests.post')
		def test_generate_response(self, mock_post):
				logger.info("Running test_generate_response")
				# Mock the response from the API
				mock_response = MagicMock()
				mock_response.iter_lines.return_value = [
						b'data: {"choices":[{"delta":{"content":"Hello"}}]}',
						b'data: {"choices":[{"delta":{"content":" world"}}]}',
						b'data: [DONE]'
				]
				mock_post.return_value = mock_response

				messages = [{"role": "user", "content": "Hi"}]
				current_prompt = "You are a helpful assistant"

				logger.debug(f"Input messages: {messages}")
				logger.debug(f"Current prompt: {current_prompt}")

				result = list(generate_response(messages, current_prompt))
				logger.debug(f"Generated response: {result}")

				self.assertEqual(result, ["Hello", " world"])
				logger.info("test_generate_response passed")

		@patch('llm_chat.requests.post')
		def test_generate_suggestions(self, mock_post):
				logger.info("Running test_generate_suggestions")
				# Mock the response from the API
				mock_response = MagicMock()
				mock_response.json.return_value = {
						"choices": [
								{
										"message": {
												"content": '[{"text":"Tell me about Jesus","icon":"fas fa-cross"}]'
										}
								}
						]
				}
				mock_post.return_value = mock_response

				messages = [{"role": "user", "content": "Hi"}]
				current_prompt = "You are a helpful assistant"

				logger.debug(f"Input messages: {messages}")
				logger.debug(f"Current prompt: {current_prompt}")

				result = generate_suggestions(messages, current_prompt)
				logger.debug(f"Generated suggestions: {result}")

				self.assertEqual(result, [{"text":"Tell me about Jesus","icon":"fas fa-cross"}])
				logger.info("test_generate_suggestions passed")

		@unittest.skipIf('OPENROUTER_API_KEY' not in os.environ, "API key not available")
		def test_generate_response_integration(self):
				logger.info("Running test_generate_response_integration")
				messages = [{"role": "user", "content": "Hello, how are you?"}]
				current_prompt = "You are a helpful assistant"

				logger.debug(f"Input messages: {messages}")
				logger.debug(f"Current prompt: {current_prompt}")

				response = list(generate_response(messages, current_prompt))
				logger.debug(f"Generated response: {response}")

				self.assertTrue(len(response) > 0, "Response should not be empty")
				logger.info("test_generate_response_integration passed")

		@unittest.skipIf('OPENROUTER_API_KEY' not in os.environ, "API key not available")
		def test_generate_suggestions_integration(self):
				logger.info("Running test_generate_suggestions_integration")
				messages = [{"role": "user", "content": "Tell me about Jesus"}]
				current_prompt = "You are a Christian chatbot"

				logger.debug(f"Input messages: {messages}")
				logger.debug(f"Current prompt: {current_prompt}")

				suggestions = generate_suggestions(messages, current_prompt)
				logger.debug(f"Generated suggestions: {suggestions}")

				self.assertTrue(len(suggestions) > 0, "Should return at least one suggestion")
				self.assertIn('text', suggestions[0], "Suggestion should have 'text' field")
				self.assertIn('icon', suggestions[0], "Suggestion should have 'icon' field")
				logger.info("test_generate_suggestions_integration passed")

if __name__ == '__main__':
		unittest.main()
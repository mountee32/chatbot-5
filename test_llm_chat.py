import os
import json
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ['OPENROUTER_API_KEY']
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4"

def generate_response(messages, current_prompt):
		headers = {
				"Authorization": f"Bearer {OPENROUTER_API_KEY}",
				"HTTP-Referer": "https://your-app-url.com",
				"X-Title": "OpenRouter Chatbot",
				"Content-Type": "application/json"
		}

		system_message = {
				"role": "system",
				"content": current_prompt or "You can use Markdown syntax and emoticons in your responses. Common emoticons like :), :(, :D will be automatically converted to emojis."
		}

		messages = [system_message] + messages

		data = {
				"model": MODEL,
				"messages": messages,
				"stream": True
		}

		response = requests.post(API_URL, headers=headers, json=data, stream=True)

		for line in response.iter_lines():
				if line:
						line = line.decode('utf-8')
						if line.startswith('data: '):
								line = line[6:]
								if line.strip() == '[DONE]':
										break
								try:
										json_object = json.loads(line)
										content = json_object['choices'][0]['delta'].get('content', '')
										if content:
												yield content
								except json.JSONDecodeError:
										continue

def generate_suggestions(messages, current_prompt):
		headers = {
				"Authorization": f"Bearer {OPENROUTER_API_KEY}",
				"HTTP-Referer": "https://your-app-url.com",
				"X-Title": "OpenRouter Chatbot",
				"Content-Type": "application/json"
		}

		schema = {
				"type": "object",
				"properties": {
						"suggestions": {
								"type": "array",
								"items": {
										"type": "object",
										"properties": {
												"text": {"type": "string"},
												"icon": {"type": "string"}
										},
										"required": ["text", "icon"]
								}
						}
				},
				"required": ["suggestions"]
		}

		system_message = {
				"role": "system",
				"content": f"""You are a suggestion generator for a chatbot. The current context is:

				{current_prompt}

				Based on this context and the last message in the conversation, generate 2-4 relevant, short (max 10 words) suggestions for the user's next message. 

				Provide the suggestions in JSON format according to the following schema:

				{json.dumps(schema, indent=2)}

				Use 'fas fa-' prefix for FontAwesome icons in the 'icon' field."""
		}

		# Use only the last message from the chat history
		last_message = messages[-1] if messages else {"role": "user", "content": ""}

		full_messages = [system_message, last_message]

		data = {
				"model": MODEL,
				"messages": full_messages,
				"max_tokens": 250
		}

		logger.info("Sending request to API")

		try:
				response = requests.post(API_URL, headers=headers, json=data)
				response.raise_for_status()

				response_json = response.json()
				logger.debug(f"API Response: {json.dumps(response_json, indent=2)}")

				if 'choices' not in response_json:
						logger.error(f"Unexpected API response structure. Response: {json.dumps(response_json, indent=2)}")
						return []

				content = response_json['choices'][0]['message']['content']
				logger.info(f"Content from API: {content}")

				try:
						suggestions_data = json.loads(content)
						if isinstance(suggestions_data, dict) and 'suggestions' in suggestions_data:
								suggestions = suggestions_data['suggestions']
								logger.info(f"Parsed suggestions: {json.dumps(suggestions, indent=2)}")
								return suggestions
						else:
								logger.warning(f"Unexpected content structure. Content: {content}")
								return []
				except json.JSONDecodeError:
						logger.warning(f"Failed to parse suggestions as JSON. Content: {content}")
						return []

		except requests.RequestException as e:
				logger.error(f"Error making request to API: {str(e)}")
				return []

		except (KeyError, IndexError, TypeError) as e:
				logger.error(f"Error parsing API response: {str(e)}")
				logger.error(f"Response JSON: {json.dumps(response_json, indent=2)}")
				return []

# Example usage
if __name__ == "__main__":
		sample_messages = [
				{"role": "user", "content": "Hi, I'm ready to start!"},
				{"role": "assistant", "content": "Great! What would you like to learn about today?"}
		]
		sample_prompt = "You are a helpful assistant for a learning platform."

		logger.info("Generating suggestions...")
		suggestions = generate_suggestions(sample_messages, sample_prompt)
		logger.info(f"Final suggestions: {json.dumps(suggestions, indent=2)}")
import os
import json
import requests
import logging

OPENROUTER_API_KEY = os.environ['OPENROUTER_API_KEY']
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o"

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

	system_message = {
			"role": "system",
			"content": f"""You are a suggestion generator for a chatbot. The current context is:

			{current_prompt}

			Based on this context and the last message in the conversation, generate 2-4 relevant, short (max 10 words) suggestions for the user's next message. Return the suggestions as a JSON array of objects, where each object has a 'text' field for the suggestion text and an 'icon' field for an appropriate FontAwesome icon class. Use 'fas fa-' prefix for FontAwesome icons."""
	}

	# Use only the last message from the chat history
	last_message = messages[-1] if messages else {"role": "user", "content": ""}

	full_messages = [system_message, last_message]

	data = {
			"model": MODEL,
			"messages": full_messages,
			"max_tokens": 250
	}

	try:
			response = requests.post(API_URL, headers=headers, json=data)
			response.raise_for_status()

			response_json = response.json()
			content = response_json['choices'][0]['message']['content']

			try:
					suggestions_json = json.loads(content)
					return suggestions_json
			except json.JSONDecodeError:
					logging.warning(f"Failed to parse suggestions as JSON. Using fallback method.")
					fallback_suggestion = {
							"text": content[:50] + "..." if len(content) > 50 else content,
							"icon": "fas fa-comment"
					}
					return [fallback_suggestion]

	except requests.RequestException as e:
			logging.error(f"Error making request to API: {str(e)}")
			return []

	except (KeyError, IndexError) as e:
			logging.error(f"Error parsing API response: {str(e)}")
			return []
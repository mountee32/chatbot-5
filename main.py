import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import requests
import json

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ['OPENROUTER_API_KEY']
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4"

conversation_history = []
current_prompt = ""

def load_menu_config():
    with open('menu_config.json', 'r') as f:
        return json.load(f)

menu_config = load_menu_config()

def generate_response(messages):
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

def generate_suggestions(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://your-app-url.com",
        "X-Title": "OpenRouter Chatbot",
        "Content-Type": "application/json"
    }

    prompt = messages + [{"role": "system", "content": "Generate 4 short, diverse suggestions for the user's next message.  You can use Markdown syntax and emoticons."}]

    data = {
        "model": MODEL,
        "messages": prompt,
        "max_tokens": 150
    }

    response = requests.post(API_URL, headers=headers, json=data)
    suggestions = response.json()['choices'][0]['message']['content'].split('\n')
    return [s.strip() for s in suggestions if s.strip()][:4]

@app.route('/')
def home():
    return render_template('index.html', menu_config=menu_config)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    conversation_history.append({"role": "user", "content": user_message})

    def generate():
        for content in generate_response(conversation_history):
            yield content

    return Response(stream_with_context(generate()), content_type='text/plain')

@app.route('/suggestions', methods=['GET'])
def get_suggestions():
    suggestions = generate_suggestions(conversation_history)
    return jsonify(suggestions)

@app.route('/set_prompt', methods=['POST'])
def set_prompt():
    global current_prompt
    current_prompt = request.json['prompt']
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
import os
import logging
import json
import time
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from llm_chat import generate_response, generate_suggestions

# Set up Python's logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='log.txt', filemode='a')

app = Flask(__name__)

conversation_history = []
current_prompt = ""
current_mode = ""

def load_menu_config():
    with open('menu_config.json', 'r') as f:
        return json.load(f)

menu_config = load_menu_config()

def log_event(event_type, data):
    log_entry = f"{time.time()} - {event_type} - {json.dumps(data)}\n"
    with open('log.txt', 'a') as f:
        f.write(log_entry)
    logging.info(f"Event: {event_type}, Data: {json.dumps(data, indent=2)}")

@app.route('/')
def home():
    log_event('page_load', {'page': 'home'})
    return render_template('index.html', menu_config=menu_config)

@app.route('/chat', methods=['POST'])
def chat():
    global conversation_history
    user_message = request.json['message']
    conversation_history.append({"role": "user", "content": user_message})

    log_event('user_message', {
        'message': user_message,
        'prompt': current_prompt,
        'mode': current_mode
    })

    def generate():
        assistant_message = ""
        for content in generate_response(conversation_history, current_prompt):
            assistant_message += content
            yield content

        conversation_history.append({"role": "assistant", "content": assistant_message})

        log_event('assistant_message', {
            'message': assistant_message,
            'prompt': current_prompt,
            'mode': current_mode
        })

    return Response(stream_with_context(generate()), content_type='text/plain')

@app.route('/suggestions', methods=['GET'])
def get_suggestions():
    global conversation_history
    suggestions_data = generate_suggestions(conversation_history, current_prompt)

    # Check if suggestions_data is a dictionary with a 'suggestions' key
    if isinstance(suggestions_data, dict) and 'suggestions' in suggestions_data:
        suggestions = suggestions_data['suggestions']
    else:
        suggestions = suggestions_data  # Assume it's already the correct format

    log_event('suggestions_generated', {
        'suggestions': suggestions,
        'conversation_history': conversation_history
    })
    logging.info(f"Generated suggestions: {json.dumps(suggestions, indent=2)}")
    return jsonify(suggestions)

@app.route('/set_prompt', methods=['POST'])
def set_prompt():
    global current_prompt, current_mode, conversation_history
    current_prompt = request.json['prompt']
    current_mode = request.json.get('mode', '')
    conversation_history = []  # Reset conversation history when changing prompts
    log_event('prompt_set', {
        'prompt': current_prompt,
        'mode': current_mode
    })
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
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

@app.route('/chat')
def chat():
    global current_prompt
    prompt = request.args.get('prompt', '')
    user_avatar = request.args.get('avatar', 'user_boy_male_young.svg')  
    assistant_avatar = request.args.get('avatar', 'default-avatar.svg')  
    icon = request.args.get('icon', 'fas fa-comment')
    title = request.args.get('title', 'Chat')
    current_prompt = prompt
    log_event('chat_page_load', {'prompt': prompt, 'user_avatar': user_avatar, 'assistant_avatar': assistant_avatar, 'icon': icon, 'title': title})
    return render_template('chat.html', prompt=prompt, user_avatar=user_avatar, assistant_avatar=assistant_avatar, icon=icon, title=title)

@app.route('/chat', methods=['POST'])
def chat_message():
    global conversation_history
    user_message = request.json['message']

    if user_message == "START_CHAT":
        # Generate an initial message from the AI assistant using the LLM
        system_message = {"role": "system", "content": current_prompt}
        initial_prompt = {"role": "user", "content": "Start a conversation based on your role. Introduce yourself and ask an engaging question to begin the interaction."}
        initial_conversation = [system_message, initial_prompt]

        initial_message = ""
        for content in generate_response(initial_conversation, current_prompt):
            initial_message += content

        conversation_history.append({"role": "assistant", "content": initial_message})

        log_event('chat_started', {
            'initial_message': initial_message,
            'prompt': current_prompt,
            'mode': current_mode
        })

        return initial_message

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

@app.route('/update_avatar', methods=['POST'])
def update_avatar():
    new_avatar = request.json['avatar']
    # Here you would typically update the user's avatar in your database
    # For this example, we'll just return a success message
    log_event('avatar_updated', {'new_avatar': new_avatar})
    return jsonify({"status": "success", "message": "Avatar updated successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
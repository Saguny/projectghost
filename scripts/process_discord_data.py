import json
import datetime
from pathlib import Path


INPUT_FILE = "data/discord_export.json" 
OUTPUT_FILE = "data/finetune_dataset.jsonl"


AI_USERNAME = "kaeeeeen" 

# Your username (The "User")
USER_USERNAME = "saguny"

# How many hours of silence before we consider it a "new conversation"?
SESSION_GAP_HOURS = 2


def load_discord_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_content(content):
    """Remove empty lines, extra whitespace, maybe custom cleaning here."""
    return content.strip()

def process_conversations(data):
    messages = data['messages']
    # Sort by timestamp just in case
    messages.sort(key=lambda x: x['timestamp'])

    conversations = []
    current_session = []
    last_time = None

    print(f"Processing {len(messages)} messages...")

    for msg in messages:
        # 1. Get basic info
        author = msg['author']['name']
        content = clean_content(msg['content'])
        
        # Skip empty messages (images/embeds without text)
        if not content:
            continue

        # 2. Map roles
        if author == AI_USERNAME:
            role = "assistant"
        elif author == USER_USERNAME:
            role = "user"
        else:
            # Skip messages from other people (group chats)
            continue

        # 3. Time Logic
        # timestamp format ex: "2023-10-27T21:44:47.143+00:00"
        # Simplify parsing for typical Discord format
        try:
            ts_str = msg['timestamp'].split('.')[0] # drop millis for safety
            ts = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
        except:
            # Fallback if format varies
            ts = datetime.datetime.now()

        # Check if we should start a new session
        if last_time:
            delta = ts - last_time
            if delta.total_seconds() > (SESSION_GAP_HOURS * 3600):
                # Save previous session if it has at least one pair
                if len(current_session) > 1:
                    conversations.append({"messages": current_session})
                current_session = []
        
        last_time = ts

        # 4. Add to current session
        # Combine consecutive messages from same user
        if current_session and current_session[-1]['role'] == role:
            current_session[-1]['content'] += "\n" + content
        else:
            current_session.append({"role": role, "content": content})

    # Don't forget the last one
    if len(current_session) > 1:
        conversations.append({"messages": current_session})

    return conversations

def save_jsonl(conversations, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for convo in conversations:
            f.write(json.dumps(convo) + "\n")
    print(f"Saved {len(conversations)} conversation sessions to {output_path}")

if __name__ == "__main__":
    try:
        data = load_discord_json(INPUT_FILE)
        convos = process_conversations(data)
        save_jsonl(convos, OUTPUT_FILE)
        
        # Preview one
        print("\nSample Conversation:")
        print(json.dumps(convos[0], indent=2))
        
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_FILE}. Make sure to export your Discord chat as JSON.")
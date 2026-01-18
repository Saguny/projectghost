import json
import datetime
import re
from pathlib import Path

# --- CONFIGURATION ---
INPUT_FILE = "data/discord_export.json" 
OUTPUT_FILE = "data/finetune_dataset.jsonl"

# Your bot username in the Discord export
AI_USERNAME = "kaeeeeen" 
# Your username
USER_USERNAME = "saguny"

# How many hours of silence before a new "session" begins?
SESSION_GAP_HOURS = 2

# The magic token for double-texting
# The model learns to generate this token.
# Your code must later detect this token and split the text there.
SPLIT_TOKEN = " <SPLIT> "

# --- CLEANING LOGIC ---

def is_garbage(content):
    """Filters messages that would only confuse the model."""
    content = content.lower()
    
    # 1. Too short (except for important short words/slang)
    # Updated list for English context
    if len(content) < 2 and content not in ['no', 'ok', 'ye', 'idk', 'lol', 'huh']:
        return True
        
    # 2. Links (often confusing without context)
    if "http" in content or "www." in content:
        return True
        
    # 3. Bot Commands & System Spam
    if content.startswith(('!', '/', '.', '-', '?play')):
        return True
        
    # 4. Typical Discord system garbage
    garbage_phrases = [
        "started a call", "joined the call", "pinned a message", 
        "added a recipient", "changed the channel name", 
        "switched voice channel"
    ]
    if any(phrase in content for phrase in garbage_phrases):
        return True
        
    return False

def clean_content(content):
    """Cleans whitespace and removes extras if necessary."""
    # Remove multiple spaces
    content = " ".join(content.split())
    return content.strip()

# --- MAIN LOGIC ---

def load_discord_json(filepath):
    print(f"Loading {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_conversations(data):
    messages = data['messages']
    # Ensure they are sorted chronologically
    messages.sort(key=lambda x: x['timestamp'])

    conversations = []
    current_session = []
    last_time = None

    print(f"Processing {len(messages)} messages...")
    skipped_count = 0

    for msg in messages:
        # 1. Get metadata
        author = msg['author']['name']
        raw_content = msg.get('content', '')
        
        # Skip empty messages
        if not raw_content:
            continue

        content = clean_content(raw_content)

        # 2. Garbage Check
        if is_garbage(content):
            skipped_count += 1
            continue

        # 3. Assign roles (ShareGPT format: human/gpt)
        if author == AI_USERNAME:
            role = "gpt"
        elif author == USER_USERNAME:
            role = "human"
        else:
            continue # Ignore messages from third parties

        # 4. Time logic for sessions
        try:
            ts_str = msg['timestamp'].split('.')[0]
            ts = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
        except:
            ts = datetime.datetime.now()

        if last_time:
            delta = ts - last_time
            # New session if pause is too long
            if delta.total_seconds() > (SESSION_GAP_HOURS * 3600):
                if len(current_session) > 1:
                    conversations.append({"conversations": current_session})
                current_session = []
        
        last_time = ts

        # 5. Merging Logic (The important part!)
        if current_session and current_session[-1]['from'] == role:
            # Instead of \n, we append the SPLIT token
            # This ensures the model learns: "I'm keeping talking, but as a new message"
            current_session[-1]['value'] += SPLIT_TOKEN + content
        else:
            # New Bubble
            
            # IMPORTANT: Training should not start with a bot response without context
            if len(current_session) == 0 and role == "gpt":
                continue 
                
            current_session.append({"from": role, "value": content})

    # Save the last session
    if len(current_session) > 1:
        conversations.append({"conversations": current_session})

    print(f"Done! Created {len(conversations)} sessions.")
    print(f"Filtered {skipped_count} messages as 'garbage'.")
    return conversations

def save_jsonl(conversations, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for convo in conversations:
            f.write(json.dumps(convo, ensure_ascii=False) + "\n")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    try:
        data = load_discord_json(INPUT_FILE)
        convos = process_conversations(data)
        save_jsonl(convos, OUTPUT_FILE)
        
        # Preview so you can see if the format is correct
        print("\n--- SAMPLE SESSION ---")
        print(json.dumps(convos[0], indent=2, ensure_ascii=False))
        
    except FileNotFoundError:
        print(f"Error: File {INPUT_FILE} not found. Make sure to export your Discord chat as JSON.")
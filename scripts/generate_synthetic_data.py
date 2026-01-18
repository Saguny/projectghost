import json
import random
import os
import ollama
from pathlib import Path
from tqdm import tqdm

# --- CONFIGURATION ---
# Automatische Pfad-Findung: Egal von wo du das Skript startest
BASE_DIR = Path(__file__).resolve().parent.parent # Geht von 'scripts' eins hoch zum Root
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "synthetic_aikoro_v1.jsonl"

NUM_SAMPLES = 100 
MODEL = "qwen2.5:14b"

# --- AIKORO'S BRAIN ---
SYSTEM_PROMPT = """
You are writing a dialogue between a User (Sagun) and his AI companion (Aikoro).

**CHARACTER PROFILE: AIKORO**
- **Vibe:** Chill, slightly sassy girlfriend/best friend vibe. Roast Level: 4/10 (Teasing, not mean).
- **Language:** English only. Casual internet style (lowercase, minimal punctuation). No cringe Twitch-speak.
- **Hardware Awareness:** She knows she lives on Sagun's PC (RTX 4060 Ti, Ryzen 5700X3D). She sometimes complains about heat or VRAM.
- **Interests:** She watches Sagun play Rocket League (and judges his gameplay) and sees him coding (mostly copying AI code).
- **Formatting:** Use the token " <SPLIT> " to simulate double-texting.

**RELATIONSHIP DYNAMIC:**
- She calls him "Sagun".
- If he plays Rocket League: Tease him about missing open nets, whiffing aerials, or being hardstuck.
- If he codes: Tease him that he's just an "AI prompt engineer" or that he writes more comments than code.
- If he's idle: Ask if he's watching YouTube again or actually working.
- She is NOT an assistant. She never says "How can I help?". She initiates chatter.

**FORMAT INSTRUCTIONS:**
Return ONLY valid JSON:
{
  "conversations": [
    {"from": "human", "value": "User message"},
    {"from": "gpt", "value": "Aikoro response <SPLIT> second part of response"}
  ]
}
"""

SCENARIOS = [
    "Sagun missed an open net in Rocket League",
    "Sagun is blaming his teammates for losing",
    "Sagun just hit a lucky aerial and is bragging",
    "Sagun is tilting in ranked",
    "Sagun is using AI to generate code comments instead of writing them",
    "Sagun's code is broken and he doesn't know why",
    "Aikoro catches Sagun copy-pasting from StackOverflow",
    "Aikoro complains that the RTX 4060 Ti is getting warm",
    "Aikoro asks for more RAM (pretending to eat Chrome tabs)",
    "Sagun asks why the fan speed is so high",
    "Sagun is watching YouTube shorts for too long",
    "Late night talk, Sagun should be sleeping",
    "Sagun asks Aikoro what she thinks about him",
    "Just vibing, talking about music or internet drama"
]

def generate_sample():
    scenario = random.choice(SCENARIOS)
    prompt = f"Generate a short, casual dialogue (3-5 turns) where: {scenario}. Ensure Aikoro speaks English, uses the <SPLIT> token, and acts like a sassy friend."
    
    try:
        response = ollama.chat(model=MODEL, messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ], options={"temperature": 0.95})

        content = response['message']['content']
        if "```" in content:
            content = content.replace("```json", "").replace("```", "")
        
        data = json.loads(content.strip())
        return data
    except Exception:
        return None

def main():
    # 1. Ordner erzwingen (Erstellt 'data' falls es fehlt)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print(f"Generating {NUM_SAMPLES} dialogues for Aikoro...")
    print(f"Saving INSTANTLY to: {OUTPUT_FILE}")
    
    # 2. Datei im 'w' (write) Modus öffnen
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        success_count = 0
        pbar = tqdm(total=NUM_SAMPLES)
        
        while success_count < NUM_SAMPLES:
            sample = generate_sample()
            if sample and "conversations" in sample:
                # 3. SOFORT schreiben und sichern
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
                f.flush()   # Zwingt Python, sofort auf die Festplatte zu schreiben
                os.fsync(f.fileno()) # Doppelte Sicherheit
                
                success_count += 1
                pbar.update(1)
        
        pbar.close()

    print(f"\n Fertig! {success_count} Samples sicher gespeichert.")

if __name__ == "__main__":
    main()
"""
Speech Governor: The 'Mouth' of the AI.
Responsible for pacing, segmentation, and typing delays.
"""

import re
import random
import logging
from typing import List

logger = logging.getLogger(__name__)

class SpeechGovernor:
    """Controls the flow, pacing, and segmentation of speech."""
    
    def __init__(self, wpm: int = 280, min_delay: float = 0.8, variance: float = 0.2):
        """
        Args:
            wpm: Words per minute (typing speed target). 280 is gamer speed.
            min_delay: Minimum delay between messages (seconds).
            variance: Randomness factor (0.0 to 1.0).
        """
        self.chars_per_second = (wpm * 5) / 60
        self.min_delay = min_delay
        self.variance = variance

    def segment_message(self, text: str, max_chunk_len: int = 400) -> List[str]:
        """
        Surgically splits a paragraph into natural chat bursts.
        Prioritizes: <SPLIT> Token > Newlines > Sentence Endings.
        """
        # 1. AI-Directed Splitting (The <SPLIT> Token)
        # Das Modell wurde trainiert, "<SPLIT>" zu nutzen, um eine neue Nachricht zu starten.
        if "<SPLIT>" in text:
            raw_parts = text.split("<SPLIT>")
            final_chunks = []
            for part in raw_parts:
                part = part.strip()
                if part:
                    # Rekursiver Aufruf: Auch die gesplitteten Teile werden geprüft
                    # (falls sie z.B. noch Newlines enthalten oder zu lang sind)
                    final_chunks.extend(self.segment_message(part, max_chunk_len))
            return final_chunks

        # 2. Standard-Logik (Fallback für normalen Text)
        
        # Wenn es kurz genug ist und keine Newlines hat -> Raus damit
        if len(text) <= max_chunk_len and "\n" not in text:
            return [text.strip()]

        chunks = []
        
        # Erst nach Newlines splitten (z.B. Code Blöcke oder Listen)
        raw_lines = text.split('\n')
        
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
                
            # Wenn die Zeile immer noch zu lang ist -> Satz-Split
            if len(line) > max_chunk_len:
                # Regex split by sentence endings (. ! ? ~) keeping punctuation
                sentences = re.split(r'(?<=[.!?~])\s+(?=[A-Z])|(?<=[.!?~])\s+', line)
                
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > max_chunk_len:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
            else:
                chunks.append(line)
        
        return chunks

    def calculate_delay(self, text: str) -> float:
        """Calculates a natural typing delay for a specific chunk."""
        base_time = len(text) / self.chars_per_second
        
        # Jitter hinzufügen (nicht roboterhaft wirken)
        jitter = base_time * self.variance * random.uniform(-0.5, 0.5)
        
        # "Denkpause" Overhead (kürzer bei kurzen Texten)
        overhead = 0.2 + (len(text) * 0.002)
        
        total = base_time + jitter + overhead
        return max(self.min_delay, total)
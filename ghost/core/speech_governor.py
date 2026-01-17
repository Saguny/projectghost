"""
Speech Governor: The 'Mouth' of the AI.
Responsible for pacing, segmentation, and typing delays.
"""

import re
import random
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class SpeechGovernor:
    """Controls the flow, pacing, and segmentation of speech."""
    
    def __init__(self, wpm: int = 200, min_delay: float = 1.0, variance: float = 0.2):
        """
        Args:
            wpm: Words per minute (typing speed target).
            min_delay: Minimum delay between messages (seconds).
            variance: Randomness factor (0.0 to 1.0) to make delays feel human.
        """
        self.chars_per_second = (wpm * 5) / 60  # Approx 5 chars per word
        self.min_delay = min_delay
        self.variance = variance

    def segment_message(self, text: str, max_chunk_len: int = 350) -> List[str]:
        """
        Surgically splits a paragraph into natural chat bursts.
        Prioritizes: Newlines > Sentence Endings > Clauses > Hard Limit.
        """
        # 1. If it's short enough, just send it
        if len(text) <= max_chunk_len and "\n" not in text:
            return [text.strip()]

        chunks = []
        
        # 2. Split by explicit newlines first (model's own formatting)
        raw_lines = text.split('\n')
        
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
                
            # 3. If line is still too long, split by sentence endings (. ! ? ~)
            # This regex splits but keeps the punctuation attached to the left side
            if len(line) > max_chunk_len:
                # Split by sentence boundaries, keeping delimiters
                sentences = re.split(r'(?<=[.!?~])\s+(?=[A-Z])|(?<=[.!?~])\s+', line)
                
                current_chunk = ""
                for sentence in sentences:
                    # If adding the next sentence exceeds limit, push current chunk
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
        
        # 4. Final safety pass: Hard chop anything that survived (rare)
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > 1900: # Discord absolute limit safety
                # Crude chop
                sub_chunks = [chunk[i:i+1900] for i in range(0, len(chunk), 1900)]
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        return final_chunks

    def calculate_delay(self, text: str) -> float:
        """Calculates a natural typing delay for a specific chunk."""
        base_time = len(text) / self.chars_per_second
        
        # Add randomness
        jitter = base_time * self.variance * random.uniform(-1, 1)
        
        # Thinking/Start-up overhead (longer pause for longer thoughts)
        overhead = 0.5 + (len(text) * 0.005)
        
        total = base_time + jitter + overhead
        return max(self.min_delay, total)
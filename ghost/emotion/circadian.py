"""Circadian rhythm simulation for time-aware emotional state."""

from datetime import datetime
import math


class CircadianRhythm:
    """Simulates circadian rhythm influence on emotional state."""
    
    def get_phase_description(self) -> str:
        """Get human-readable description of current time phase."""
        hour = datetime.now().hour
        
        if 5 <= hour < 9:
            return "Early Morning (Waking Up)"
        elif 9 <= hour < 12:
            return "Morning (Alert)"
        elif 12 <= hour < 14:
            return "Midday (Peak Energy)"
        elif 14 <= hour < 18:
            return "Afternoon (Active)"
        elif 18 <= hour < 22:
            return "Evening (Winding Down)"
        elif 22 <= hour < 24:
            return "Late Night (Low Energy)"
        else:  # 0-5
            return "Deep Night (Sleepy)"
    
    def get_emotional_influence(self) -> dict:
        """
        Get circadian influence on emotional state.
        Returns deltas for pleasure, arousal, dominance.
        """
        hour = datetime.now().hour
        
        # Arousal follows a sinusoidal curve peaking around 14:00
        arousal_peak_hour = 14
        arousal = math.sin((hour - arousal_peak_hour) * math.pi / 12)
        
        # Pleasure slightly higher during day
        pleasure = 0.2 if 8 <= hour < 20 else -0.1
        
        # Dominance higher when alert
        dominance = 0.3 if 9 <= hour < 18 else -0.2
        
        return {
            'pleasure': pleasure,
            'arousal': arousal,
            'dominance': dominance
        }
    
    def get_proactivity_modifier(self) -> float:
        """
        Get probability modifier for autonomous initiation.
        Higher during active hours, lower during sleep hours.
        """
        hour = datetime.now().hour
        
        if 9 <= hour < 22:
            return 1.0  # Normal probability during waking hours
        elif 22 <= hour < 24 or 0 <= hour < 6:
            return 0.1  # Very low probability late night
        else:  # 6-9
            return 0.5  # Moderate probability early morning
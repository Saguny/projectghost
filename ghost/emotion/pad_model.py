"""PAD (Pleasure-Arousal-Dominance) emotional model implementation."""

import logging
from ghost.core.interfaces import EmotionalState

logger = logging.getLogger(__name__)


class PADModel:
    """
    Pleasure-Arousal-Dominance emotional state model.
    
    - Pleasure: Positive (happy) vs Negative (sad) affect
    - Arousal: High energy vs Low energy
    - Dominance: Confident/controlling vs Submissive/uncertain
    
    All values range from -1.0 to 1.0
    """
    
    # Decay rate per update (prevents emotional states from persisting forever)
    DECAY_RATE = 0.05
    
    def __init__(
        self,
        initial_pleasure: float = 0.6,
        initial_arousal: float = 0.7,
        initial_dominance: float = 0.5
    ):
        self.pleasure = self._clamp(initial_pleasure)
        self.arousal = self._clamp(initial_arousal)
        self.dominance = self._clamp(initial_dominance)
    
    def update(
        self,
        pleasure_delta: float,
        arousal_delta: float,
        dominance_delta: float
    ) -> EmotionalState:
        """Update emotional state with deltas and apply decay."""
        # Apply decay towards neutral (0)
        self.pleasure = self._decay(self.pleasure)
        self.arousal = self._decay(self.arousal)
        self.dominance = self._decay(self.dominance)
        
        # Apply deltas
        self.pleasure = self._clamp(self.pleasure + pleasure_delta)
        self.arousal = self._clamp(self.arousal + arousal_delta)
        self.dominance = self._clamp(self.dominance + dominance_delta)
        
        return self.get_state()
    
    def get_state(self) -> EmotionalState:
        """Get current emotional state."""
        return EmotionalState(
            pleasure=self.pleasure,
            arousal=self.arousal,
            dominance=self.dominance
        )
    
    @staticmethod
    def _clamp(value: float) -> float:
        """Clamp value between -1 and 1."""
        return max(-1.0, min(1.0, value))
    
    @staticmethod
    def _decay(value: float) -> float:
        """Apply decay towards neutral (0)."""
        if value > 0:
            return max(0, value - PADModel.DECAY_RATE)
        elif value < 0:
            return min(0, value + PADModel.DECAY_RATE)
        return 0
    
    def analyze_sentiment(self, text: str) -> tuple[float, float, float]:
        """
        Analyze text sentiment and return PAD deltas.
        Simplified heuristic - in production, use sentiment analysis model.
        """
        text_lower = text.lower()
        
        pleasure_delta = 0.0
        arousal_delta = 0.0
        dominance_delta = 0.0
        
        # Positive keywords
        positive_words = ['happy', 'love', 'great', 'awesome', 'good', 'thanks', 'appreciate']
        negative_words = ['sad', 'hate', 'bad', 'terrible', 'angry', 'frustrated', 'annoyed']
        high_energy_words = ['exciting', 'intense', 'urgent', 'rush', 'crazy', 'wild']
        low_energy_words = ['tired', 'calm', 'boring', 'slow', 'sleepy', 'relaxed']
        dominant_words = ['sure', 'definitely', 'absolutely', 'confident', 'know']
        submissive_words = ['maybe', 'perhaps', 'uncertain', 'confused', 'unsure', 'help']
        
        # Count matches
        for word in positive_words:
            if word in text_lower:
                pleasure_delta += 0.1
        
        for word in negative_words:
            if word in text_lower:
                pleasure_delta -= 0.1
        
        for word in high_energy_words:
            if word in text_lower:
                arousal_delta += 0.1
        
        for word in low_energy_words:
            if word in text_lower:
                arousal_delta -= 0.1
        
        for word in dominant_words:
            if word in text_lower:
                dominance_delta += 0.05
        
        for word in submissive_words:
            if word in text_lower:
                dominance_delta -= 0.05
        
        return (
            self._clamp(pleasure_delta),
            self._clamp(arousal_delta),
            self._clamp(dominance_delta)
        )
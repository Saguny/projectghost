"""Emotional state management with PAD model and circadian rhythms.

This module implements emotional modeling using the PAD
(Pleasure-Arousal-Dominance) psychological model, enhanced with
circadian rhythm simulation for time-aware behavior.

Key Features:
- PAD emotional state tracking
- Sentiment analysis of messages
- Time-based emotional decay
- Circadian rhythm influence
- Persistent emotional state

Usage:
    from ghost.emotion import EmotionService, PADModel
    from ghost.core.config import PersonaConfig
    
    config = PersonaConfig()
    emotion_service = EmotionService(config, event_bus)
    
    # Update emotional state
    await emotion_service.update_state(
        pleasure_delta=0.2,
        arousal_delta=0.1,
        dominance_delta=0.0,
        reason="positive_interaction"
    )
    
    # Get current state
    state = await emotion_service.get_state()
    print(state.to_description())  # "positive, energetic, confident"
"""

from ghost.emotion.emotion_service import EmotionService
from ghost.emotion.pad_model import PADModel
from ghost.emotion.circadian import CircadianRhythm

__all__ = [
    "EmotionService",
    "PADModel",
    "CircadianRhythm",
]


def create_emotion_service(persona_config, event_bus) -> EmotionService:
    """Factory function to create a configured emotion service.
    
    Args:
        persona_config: PersonaConfig with emotional defaults
        event_bus: EventBus for state change notifications
        
    Returns:
        Configured EmotionService
    """
    return EmotionService(persona_config, event_bus)
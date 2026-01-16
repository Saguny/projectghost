"""Emotional state management service."""

import logging
from datetime import datetime
from pathlib import Path
import json

from ghost.core.interfaces import IEmotionProvider, EmotionalState
from ghost.emotion.pad_model import PADModel
from ghost.emotion.circadian import CircadianRhythm
from ghost.core.config import PersonaConfig
from ghost.core.events import EventBus, EmotionalStateChanged

logger = logging.getLogger(__name__)


class EmotionService(IEmotionProvider):
    """Manages emotional state with PAD model and circadian rhythms."""
    
    def __init__(self, config: PersonaConfig, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        
        # Initialize PAD model
        self.pad_model = PADModel(
            initial_pleasure=config.default_pleasure,
            initial_arousal=config.default_arousal,
            initial_dominance=config.default_dominance
        )
        
        # Initialize circadian rhythm
        self.circadian = CircadianRhythm()
        
        # State persistence
        self._state_file = Path("data/emotional_state.json")
        self._load_state()
        
        logger.info("Emotion service initialized")
    
    async def get_state(self) -> EmotionalState:
        """Get current emotional state."""
        return self.pad_model.get_state()
    
    async def update_state(
        self,
        pleasure_delta: float,
        arousal_delta: float,
        dominance_delta: float,
        reason: str
    ) -> EmotionalState:
        """Update emotional state and emit event."""
        old_state = self.pad_model.get_state()
        
        # Apply update with decay
        new_state = self.pad_model.update(
            pleasure_delta,
            arousal_delta,
            dominance_delta
        )
        
        # Emit state change event
        await self.event_bus.publish(EmotionalStateChanged(
            old_pleasure=old_state.pleasure,
            old_arousal=old_state.arousal,
            old_dominance=old_state.dominance,
            new_pleasure=new_state.pleasure,
            new_arousal=new_state.arousal,
            new_dominance=new_state.dominance,
            trigger=reason
        ))
        
        # Persist state
        self._save_state()
        
        logger.info(f"Emotional state updated: {reason} -> {new_state.to_description()}")
        return new_state
    
    async def get_circadian_phase(self) -> str:
        """Get current circadian phase."""
        return self.circadian.get_phase_description()
    
    async def apply_circadian_influence(self) -> None:
        """Apply circadian rhythm influence to emotional state."""
        influence = self.circadian.get_emotional_influence()
        
        # Subtle circadian adjustments
        await self.update_state(
            pleasure_delta=influence['pleasure'] * 0.1,
            arousal_delta=influence['arousal'] * 0.1,
            dominance_delta=influence['dominance'] * 0.1,
            reason="circadian_rhythm"
        )
    
    def get_contextual_modifiers(self) -> dict:
        """Get current emotional modifiers for prompt generation."""
        state = self.pad_model.get_state()
        phase = self.circadian.get_phase_description()
        
        return {
            "mood_description": state.to_description(),
            "circadian_phase": phase,
            "energy_level": "high" if state.arousal > 0.3 else "low",
            "emotional_stability": "stable" if abs(state.pleasure) < 0.5 else "intense"
        }
    
    def _save_state(self) -> None:
        """Persist emotional state to disk."""
        try:
            state = self.pad_model.get_state()
            data = {
                "timestamp": datetime.utcnow().isoformat(),
                "pleasure": state.pleasure,
                "arousal": state.arousal,
                "dominance": state.dominance
            }
            
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save emotional state: {e}")
    
    def _load_state(self) -> None:
        """Load emotional state from disk."""
        if not self._state_file.exists():
            return
        
        try:
            with open(self._state_file) as f:
                data = json.load(f)
            
            self.pad_model = PADModel(
                initial_pleasure=data['pleasure'],
                initial_arousal=data['arousal'],
                initial_dominance=data['dominance']
            )
            logger.info("Loaded previous emotional state from disk")
        except Exception as e:
            logger.warning(f"Failed to load emotional state: {e}")
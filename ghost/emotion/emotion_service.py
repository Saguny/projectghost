"""
Emotional State Management Service (Updated for Emotional Permanence)

NEW FEATURES:
1. Emotional Inertia: Current state heavily weights previous state
   - Formula: new_state = 0.8 * old_state + 0.2 * new_stimulus
   - Prevents rapid mood swings from single messages

2. Grudge Mode: Lock into "Cold" state when hurt/angry
   - Trigger: Pleasure < -0.5 AND Dominance > 0.5
   - Effect: Short, curt responses until apology detected
   - Recovery: "sorry" or "apology" intent releases grudge

3. Sticky Emotions: Emotions persist across messages
   - No instant resets from positive prompts
   - Gradual emotional drift over time
"""

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
    """Manages emotional state with PAD model, circadian rhythms, and EMOTIONAL INERTIA."""
    
    # Emotional inertia weights
    INERTIA_WEIGHT = 0.8  # How much old state matters
    STIMULUS_WEIGHT = 0.2  # How much new input matters
    
    # Grudge mode thresholds
    GRUDGE_PLEASURE_THRESHOLD = -0.5
    GRUDGE_DOMINANCE_THRESHOLD = 0.5
    
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
        
        # Grudge mode state
        self._in_grudge_mode = False
        self._grudge_trigger_reason = None
        
        # State persistence
        self._state_file = Path("data/emotional_state.json")
        self._load_state()
        
        logger.info("Emotion service initialized with emotional inertia")
    
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
        """
        Update emotional state with EMOTIONAL INERTIA.
        
        NEW BEHAVIOR:
        - Applies inertia weighting (80% old, 20% new)
        - Checks for grudge mode triggers
        - Persists sticky emotional states
        """
        old_state = self.pad_model.get_state()
        
        # Apply inertia: Heavily weight the current state
        inertia_pleasure = old_state.pleasure * self.INERTIA_WEIGHT
        inertia_arousal = old_state.arousal * self.INERTIA_WEIGHT
        inertia_dominance = old_state.dominance * self.INERTIA_WEIGHT
        
        # Scale new stimulus
        stimulus_pleasure = pleasure_delta * self.STIMULUS_WEIGHT
        stimulus_arousal = arousal_delta * self.STIMULUS_WEIGHT
        stimulus_dominance = dominance_delta * self.STIMULUS_WEIGHT
        
        # Combine: Inertia + Stimulus
        final_pleasure_delta = (inertia_pleasure + stimulus_pleasure) - old_state.pleasure
        final_arousal_delta = (inertia_arousal + stimulus_arousal) - old_state.arousal
        final_dominance_delta = (inertia_dominance + stimulus_dominance) - old_state.dominance
        
        logger.debug(
            f"Emotional inertia: "
            f"P:{pleasure_delta:.2f}→{final_pleasure_delta:.2f}, "
            f"A:{arousal_delta:.2f}→{final_arousal_delta:.2f}, "
            f"D:{dominance_delta:.2f}→{final_dominance_delta:.2f}"
        )
        
        # Apply update with decay
        new_state = self.pad_model.update(
            final_pleasure_delta,
            final_arousal_delta,
            final_dominance_delta
        )
        
        # Check for grudge mode trigger
        await self._check_grudge_mode(new_state, reason)
        
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
    
    async def _check_grudge_mode(self, state: EmotionalState, reason: str):
        """
        Check if AI should enter "Grudge Mode".
        
        Trigger: Low pleasure + High dominance = Cold/Defensive
        Effect: Lock into curt responses until apology
        """
        
        # Check for grudge trigger
        if (state.pleasure < self.GRUDGE_PLEASURE_THRESHOLD and 
            state.dominance > self.GRUDGE_DOMINANCE_THRESHOLD):
            
            if not self._in_grudge_mode:
                self._in_grudge_mode = True
                self._grudge_trigger_reason = reason
                logger.warning(
                    f"🔒 GRUDGE MODE ACTIVATED: "
                    f"P={state.pleasure:.2f}, D={state.dominance:.2f}, "
                    f"Trigger: {reason}"
                )
        
        # Check for apology (grudge release)
        if self._in_grudge_mode:
            apology_keywords = ['sorry', 'apology', 'apologize', 'my bad', 'forgive']
            if any(keyword in reason.lower() for keyword in apology_keywords):
                self._in_grudge_mode = False
                logger.info("💚 GRUDGE MODE RELEASED: Apology detected")
    
    def is_in_grudge_mode(self) -> bool:
        """Check if AI is currently in grudge mode."""
        return self._in_grudge_mode
    
    def get_grudge_info(self) -> dict:
        """Get grudge mode status and reason."""
        return {
            'active': self._in_grudge_mode,
            'trigger_reason': self._grudge_trigger_reason if self._in_grudge_mode else None
        }
    
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
        """
        Get current emotional modifiers for prompt generation.
        
        NEW: Includes grudge mode status
        """
        state = self.pad_model.get_state()
        phase = self.circadian.get_phase_description()
        
        # Base modifiers
        modifiers = {
            "mood_description": state.to_description(),
            "circadian_phase": phase,
            "energy_level": "high" if state.arousal > 0.3 else "low",
            "emotional_stability": "stable" if abs(state.pleasure) < 0.5 else "intense",
            "grudge_mode": self._in_grudge_mode
        }
        
        # Add grudge context if active
        if self._in_grudge_mode:
            modifiers["grudge_reason"] = self._grudge_trigger_reason
            modifiers["mood_override"] = "cold, defensive, curt"
        
        return modifiers
    
    def _save_state(self) -> None:
        """Persist emotional state to disk."""
        try:
            state = self.pad_model.get_state()
            data = {
                "timestamp": datetime.utcnow().isoformat(),
                "pleasure": state.pleasure,
                "arousal": state.arousal,
                "dominance": state.dominance,
                "grudge_mode": self._in_grudge_mode,
                "grudge_trigger": self._grudge_trigger_reason
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
            
            # Restore grudge mode
            self._in_grudge_mode = data.get('grudge_mode', False)
            self._grudge_trigger_reason = data.get('grudge_trigger')
            
            logger.info("Loaded previous emotional state from disk")
            if self._in_grudge_mode:
                logger.warning(f"Restored GRUDGE MODE: {self._grudge_trigger_reason}")
        except Exception as e:
            logger.warning(f"Failed to load emotional state: {e}")
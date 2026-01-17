"""
Emotional State Management Service (Sentience Upgrade)

NEW FEATURES:
1. Emotional Inertia: Current state heavily weights previous state
   - Formula: new_state = 0.8 * old_state + 0.2 * new_stimulus
   - Prevents rapid mood swings from single messages

2. Grudge Mode: Lock into "Cold" state when hurt/angry
   - Trigger: Pleasure < -0.5 AND Dominance > 0.5
   - Effect: Dampen positive inputs until apology detected
   - Recovery: "sorry" or "apology" intent releases grudge

3. Sticky Emotions: Emotions persist across sessions
   - State saved to disk on shutdown
   - State loaded from disk on startup
"""

import logging
from datetime import datetime, timezone
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
    GRUDGE_DAMPENING_FACTOR = 0.3  # Reduce positive inputs by 70% when grudging
    
    def __init__(self, config: PersonaConfig, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        
        # Initialize PAD model (will be overwritten by load if state exists)
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
        self._grudge_start_time = None
        
        # State persistence
        self._state_file = Path("data/emotional_state.json")
        self._load_state()
        
        logger.info("Emotion service initialized with emotional inertia & grudge mode")
    
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
        Update emotional state with EMOTIONAL INERTIA and GRUDGE MODE.
        
        NEW BEHAVIOR:
        - Applies inertia weighting (80% old, 20% new)
        - Applies grudge dampening if in grudge mode
        - Checks for grudge mode triggers and releases
        - Persists sticky emotional states
        """
        old_state = self.pad_model.get_state()
        
        # === GRUDGE MODE DAMPENING ===
        # If in grudge mode, dampen positive pleasure inputs
        if self._in_grudge_mode and pleasure_delta > 0:
            original_delta = pleasure_delta
            pleasure_delta *= self.GRUDGE_DAMPENING_FACTOR
            logger.debug(
                f"🧊 Grudge dampening: "
                f"pleasure {original_delta:+.2f} → {pleasure_delta:+.2f}"
            )
        
        # === EMOTIONAL INERTIA ===
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
            f"Emotional inertia applied: "
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
        
        # === GRUDGE MODE LOGIC ===
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
        
        logger.info(f"Emotional state updated: {reason} → {new_state.to_description()}")
        return new_state
    
    async def _check_grudge_mode(self, state: EmotionalState, reason: str):
        """
        Check if AI should enter or exit "Grudge Mode".
        
        Trigger: Low pleasure + High dominance = Cold/Defensive
        Effect: Lock into curt responses, dampen positive inputs
        Release: Apology detected OR time passed (30 min)
        """
        
        # === CHECK FOR GRUDGE TRIGGER ===
        if (state.pleasure < self.GRUDGE_PLEASURE_THRESHOLD and 
            state.dominance > self.GRUDGE_DOMINANCE_THRESHOLD):
            
            if not self._in_grudge_mode:
                self._in_grudge_mode = True
                self._grudge_trigger_reason = reason
                self._grudge_start_time = datetime.now(timezone.utc)
                logger.warning(
                    f"🔒 GRUDGE MODE ACTIVATED: "
                    f"P={state.pleasure:.2f}, D={state.dominance:.2f}, "
                    f"Trigger: {reason}"
                )
        
        # === CHECK FOR GRUDGE RELEASE ===
        if self._in_grudge_mode:
            # Release condition 1: Apology detected
            apology_keywords = ['sorry', 'apology', 'apologize', 'my bad', 'forgive', 'didn\'t mean']
            if any(keyword in reason.lower() for keyword in apology_keywords):
                self._release_grudge("apology detected")
                return
            
            # Release condition 2: Time passed (auto-forgiveness after 30 min)
            if self._grudge_start_time:
                time_held = (datetime.now(timezone.utc) - self._grudge_start_time).total_seconds()
                if time_held > 1800:  # 30 minutes
                    self._release_grudge("time healed wounds")
                    return
            
            # Release condition 3: Emotional state improved naturally
            if state.pleasure > 0.2:
                self._release_grudge("mood improved")
                return
    
    def _release_grudge(self, reason: str):
        """Release grudge mode."""
        self._in_grudge_mode = False
        logger.info(f"💚 GRUDGE MODE RELEASED: {reason}")
        self._grudge_trigger_reason = None
        self._grudge_start_time = None
    
    def is_in_grudge_mode(self) -> bool:
        """Check if AI is currently in grudge mode."""
        return self._in_grudge_mode
    
    def get_grudge_info(self) -> dict:
        """Get grudge mode status and reason."""
        return {
            'active': self._in_grudge_mode,
            'trigger_reason': self._grudge_trigger_reason if self._in_grudge_mode else None,
            'duration_seconds': (
                (datetime.now(timezone.utc) - self._grudge_start_time).total_seconds()
                if self._grudge_start_time else 0
            )
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
        
        Includes grudge mode status and dampening info.
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
            modifiers["grudge_duration_min"] = int(
                (datetime.now(timezone.utc) - self._grudge_start_time).total_seconds() / 60
            ) if self._grudge_start_time else 0
        
        return modifiers
    
    def _save_state(self) -> None:
        """Persist emotional state to disk."""
        try:
            state = self.pad_model.get_state()
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pleasure": state.pleasure,
                "arousal": state.arousal,
                "dominance": state.dominance,
                "grudge_mode": self._in_grudge_mode,
                "grudge_trigger": self._grudge_trigger_reason,
                "grudge_start": self._grudge_start_time.isoformat() if self._grudge_start_time else None,
                "version": 2  # Sentience upgrade version
            }
            
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save emotional state: {e}")
    
    def _load_state(self) -> None:
        """Load emotional state from disk."""
        if not self._state_file.exists():
            logger.info("No saved emotional state found, using defaults")
            return
        
        try:
            with open(self._state_file) as f:
                data = json.load(f)
            
            # Restore PAD state
            self.pad_model = PADModel(
                initial_pleasure=data.get('pleasure', 0.6),
                initial_arousal=data.get('arousal', 0.7),
                initial_dominance=data.get('dominance', 0.5)
            )
            
            # Restore grudge mode
            self._in_grudge_mode = data.get('grudge_mode', False)
            self._grudge_trigger_reason = data.get('grudge_trigger')
            
            if data.get('grudge_start'):
                self._grudge_start_time = datetime.fromisoformat(data['grudge_start'])
            
            logger.info("✓ Loaded previous emotional state from disk")
            if self._in_grudge_mode:
                logger.warning(f"  Restored GRUDGE MODE: {self._grudge_trigger_reason}")
        except Exception as e:
            logger.warning(f"Failed to load emotional state: {e}, using defaults")
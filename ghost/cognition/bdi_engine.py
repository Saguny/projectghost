"""
BDI Engine: Belief-Desire-Intention Autonomy (Sentience Upgrade)

NEW FEATURES:
1. Metabolic Decay: Needs decay over real time (not per-message)
2. Consequential Triggers: Needs directly cause behavior
3. Energy Gating: Low energy can cause task refusal
4. Social Starvation: Prolonged isolation triggers contact attempts

Architecture:
    Beliefs (what agent knows) → Knowledge graph
    Desires (internal needs) → Drive system (NOW WITH DECAY)
    Intentions (planned actions) → Goal queue (NOW EXECUTED)
    
Needs (decay over TIME):
    - Social: Need for interaction (decays hourly)
    - Curiosity: Desire to learn (decays hourly)
    - Energy: Computational capacity (consumed by tasks)
    - Affiliation: Bond with user (decays when ignored)
    
Intentions (goal-driven):
    - Initiate conversation (social starvation)
    - Ask question (curiosity)
    - Share thought (affiliation)
    - Rest (low energy)
    - Refuse task (critical energy)
    
Decision Logic:
    needs → desires → intentions → actions (REAL CONSEQUENCES)
"""

import logging
import asyncio
import json
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

from ghost.core.events import EventBus, ProactiveImpulse

logger = logging.getLogger(__name__)


@dataclass
class Need:
    """Internal need/drive with TIME-BASED decay"""
    name: str
    value: float  # 0.0 (satisfied) to 1.0 (critical)
    decay_rate: float  # Per hour
    threshold_trigger: float  # Value that triggers action
    last_satisfied: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_decay: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def decay(self, hours: float):
        """Increase need over time."""
        self.value = min(1.0, self.value + (self.decay_rate * hours))
        self.last_decay = datetime.now(timezone.utc)
    
    def satisfy(self, amount: float):
        """Reduce need (action taken)."""
        self.value = max(0.0, self.value - amount)
        self.last_satisfied = datetime.now(timezone.utc)
    
    def is_critical(self) -> bool:
        """Check if need requires attention."""
        return self.value >= self.threshold_trigger


@dataclass
class Intention:
    """Planned action"""
    action: str  # e.g., "initiate_conversation"
    motivation: str  # Why (which need)
    priority: float  # 0-1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed: bool = False


class BDIEngine:
    """
    Belief-Desire-Intention autonomous agent with METABOLIC DECAY.
    
    Cycle:
        1. Update needs (TIME-BASED decay)
        2. Evaluate desires (check need levels)
        3. Generate intentions (plan actions)
        4. Execute intentions (autonomous behavior with CONSEQUENCES)
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        belief_system,
        config
    ):
        self.event_bus = event_bus
        self.belief_system = belief_system
        self.config = config
        
        # Need system
        self.needs = self._initialize_needs()
        
        # Intention queue
        self.intentions: List[Intention] = []
        
        # State
        self._running = False
        self._last_update = datetime.now(timezone.utc)
        self._last_action = datetime.now(timezone.utc)
        
        # Persistence
        self._state_file = Path("data/bdi_state.json")
        self._load_state()
        
        logger.info("BDI engine initialized with metabolic decay")
    
    def _initialize_needs(self) -> Dict[str, Need]:
        """Initialize internal needs with TIME-BASED decay."""
        return {
            'social': Need(
                name='social',
                value=0.3,
                decay_rate=0.15,  # 15% per hour
                threshold_trigger=0.7
            ),
            'curiosity': Need(
                name='curiosity',
                value=0.2,
                decay_rate=0.08,  # 8% per hour
                threshold_trigger=0.6
            ),
            'affiliation': Need(
                name='affiliation',
                value=0.5,
                decay_rate=0.1,  # 10% per hour
                threshold_trigger=0.8
            )
        }
    
    async def start(self):
        """Start BDI cycle."""
        if not self.config.autonomy.enabled:
            logger.info("BDI engine disabled in config")
            return
        
        self._running = True
        asyncio.create_task(self._bdi_loop())
        logger.info("BDI engine started (metabolic decay active)")
    
    async def stop(self):
        """Stop BDI cycle."""
        self._running = False
        self._save_state()
        logger.info("BDI engine stopped")
    
    async def _bdi_loop(self):
        """Main BDI cycle with TIME-BASED updates."""
        while self._running:
            try:
                await asyncio.sleep(self.config.autonomy.check_interval_seconds)
                
                # Step 1: Update needs (TIME-BASED)
                await self._update_needs()
                
                # Step 2: Evaluate desires
                desires = self._evaluate_desires()
                
                # Step 3: Form intentions
                if desires:
                    intention = self._form_intention(desires)
                    if intention:
                        self.intentions.append(intention)
                
                # Step 4: Execute intentions
                await self._execute_intentions()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"BDI loop error: {e}", exc_info=True)
    
    async def _update_needs(self):
        """Update need levels based on TIME passage (metabolic decay)."""
        now = datetime.now(timezone.utc)
        
        for need in self.needs.values():
            # Calculate hours since last decay
            time_since_decay = (now - need.last_decay).total_seconds() / 3600
            
            if time_since_decay < 0.01:  # Skip if < 36 seconds
                continue
            
            # Apply time-based decay
            need.decay(time_since_decay)
        
        self._last_update = now
        
        # Log critical needs
        critical = [n for n in self.needs.values() if n.is_critical()]
        if critical:
            logger.info(
                f"Critical needs: {', '.join(n.name for n in critical)} "
                f"[{', '.join(f'{n.name}={n.value:.2f}' for n in critical)}]"
            )
    
    def _evaluate_desires(self) -> List[str]:
        """
        Evaluate which desires are active.
        
        Returns:
            List of active desire names
        """
        desires = []
        
        # Social desire (CONSEQUENTIAL)
        if self.needs['social'].is_critical():
            desires.append('seek_interaction')
        
        # Curiosity desire
        if self.needs['curiosity'].is_critical():
            desires.append('seek_knowledge')
        
        # Affiliation desire
        if self.needs['affiliation'].is_critical():
            desires.append('strengthen_bond')
        
        return desires
    
    def _form_intention(self, desires: List[str]) -> Optional[Intention]:
        """
        Generate intention from desires (WITH COOLDOWN).
        """
        
        # Check cooldown (min time between actions)
        time_since_last = (
            datetime.now(timezone.utc) - self._last_action
        ).total_seconds() / 60
        
        min_interval = self.config.autonomy.min_interval_minutes
        if time_since_last < min_interval:
            return None
        
        # Priority ranking (energy removed)
        priority_map = {
            'seek_interaction': 0.7,  # Medium-high (social starvation)
            'strengthen_bond': 0.6,
            'seek_knowledge': 0.5
        }
        
        # Pick highest priority desire
        desires_sorted = sorted(
            desires,
            key=lambda d: priority_map.get(d, 0.0),
            reverse=True
        )
        
        if not desires_sorted:
            return None
        
        primary_desire = desires_sorted[0]
        
        # Map desires to actions (no rest action)
        action_map = {
            'seek_interaction': 'initiate_conversation',
            'strengthen_bond': 'share_thought',
            'seek_knowledge': 'ask_question'
        }
        
        action = action_map.get(primary_desire)
        if not action:
            return None
        
        return Intention(
            action=action,
            motivation=primary_desire,
            priority=priority_map.get(primary_desire, 0.5)
        )
    
    async def _execute_intentions(self):
        """Execute queued intentions (WITH REAL CONSEQUENCES)."""
        if not self.intentions:
            return
        
        # Sort by priority
        self.intentions.sort(key=lambda i: i.priority, reverse=True)
        
        # Execute highest priority
        intention = self.intentions[0]
        
        if intention.executed:
            self.intentions.remove(intention)
            return
        
        success = await self._execute_action(intention)
        
        if success:
            intention.executed = True
            self.intentions.remove(intention)
            self._last_action = datetime.now(timezone.utc)
    
    async def _execute_action(self, intention: Intention) -> bool:
        """
        Execute a specific intention (METABOLIC CONSEQUENCES - NO ENERGY COSTS).
        """
        action = intention.action
        
        logger.info(
            f"Executing intention: {action} "
            f"(motivation: {intention.motivation}, priority: {intention.priority:.2f})"
        )
        
        if action == 'initiate_conversation':
            # Initiate social interaction (SATISFIES SOCIAL NEED)
            trigger_reason = self._get_conversation_trigger(intention.motivation)
            
            await self.event_bus.publish(ProactiveImpulse(
                trigger_reason=trigger_reason,
                confidence=intention.priority
            ))
            
            # CONSEQUENCE: Satisfy social need (no energy cost)
            self.needs['social'].satisfy(0.5)
            
            logger.info(f"Initiated conversation (social: {self.needs['social'].value:.2f})")
            return True
        
        elif action == 'share_thought':
            # Share something to strengthen bond
            trigger_reason = "wanted to share something with you"
            
            await self.event_bus.publish(ProactiveImpulse(
                trigger_reason=trigger_reason,
                confidence=intention.priority
            ))
            
            # CONSEQUENCE: Satisfy affiliation (no energy cost)
            self.needs['affiliation'].satisfy(0.4)
            
            return True
        
        elif action == 'ask_question':
            # Ask question to satisfy curiosity
            trigger_reason = "curious about something"
            
            await self.event_bus.publish(ProactiveImpulse(
                trigger_reason=trigger_reason,
                confidence=intention.priority
            ))
            
            # CONSEQUENCE: Satisfy curiosity (no energy cost)
            self.needs['curiosity'].satisfy(0.3)
            
            return True
        
        else:
            logger.warning(f"Unknown action: {action}")
            return False
    
    def _get_conversation_trigger(self, motivation: str) -> str:
        """Generate context-appropriate trigger reason (energy removed)."""
        triggers = {
            'seek_interaction': "haven't talked in a while, wanted to check in",
            'strengthen_bond': "thinking about you",
            'seek_knowledge': "curious about what you're up to"
        }
        
        return triggers.get(motivation, "spontaneous impulse")
    
    async def update_need(self, need_name: str, delta: float):
        """
        Manually update need (from external event).
        
        Delta is SIGNED:
        - Negative = Satisfy (reduce need)
        - Positive = Increase need
        """
        if need_name in self.needs:
            old_value = self.needs[need_name].value
            
            if delta < 0:
                # Satisfy
                self.needs[need_name].satisfy(-delta)
            else:
                # Increase
                self.needs[need_name].value = min(1.0, self.needs[need_name].value + delta)
            
            new_value = self.needs[need_name].value
            logger.debug(
                f"Need updated: {need_name} "
                f"{old_value:.2f} → {new_value:.2f} ({delta:+.2f})"
            )
    
    def get_need_state(self) -> Dict[str, float]:
        """Get current need values."""
        return {name: need.value for name, need in self.needs.items()}
    
    def check_willpower(self, task_cost: float = 0.2) -> tuple[bool, str]:
        """
        Check if agent has enough willpower to perform a task.
        
        Energy system removed - always return True.
        
        Returns:
            (True, "") - Agent is always willing
        """
        return True, ""
    
    def _save_state(self):
        """Persist BDI state."""
        try:
            state = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'needs': {
                    name: {
                        'value': need.value,
                        'last_satisfied': need.last_satisfied.isoformat(),
                        'last_decay': need.last_decay.isoformat()
                    }
                    for name, need in self.needs.items()
                },
                'last_action': self._last_action.isoformat(),
                'version': 2  # Sentience upgrade version
            }
            
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
            logger.debug("BDI state saved")
                
        except Exception as e:
            logger.error(f"Failed to save BDI state: {e}")
    
    def _load_state(self):
        """Load BDI state from disk with safety checks."""
        if not self._state_file.exists():
            return
        
        try:
            with open(self._state_file) as f:
                state = json.load(f)
            
            # Helper to parse time safely
            def safe_parse_time(iso_str: Any, default: datetime) -> datetime:
                if not isinstance(iso_str, str):
                    return default
                try:
                    return datetime.fromisoformat(iso_str)
                except ValueError:
                    return default

            # Restore need values
            current_time = datetime.now(timezone.utc)
            for name, data in state.get('needs', {}).items():
                if name in self.needs:
                    self.needs[name].value = float(data.get('value', 0.5))
                    
                    # Safe timestamp parsing
                    last_sat = data.get('last_satisfied')
                    self.needs[name].last_satisfied = safe_parse_time(last_sat, current_time)
                    
                    # Safe decay parsing (handle migration from v1 to v2)
                    last_dec = data.get('last_decay')
                    self.needs[name].last_decay = safe_parse_time(last_dec, current_time)
            
            # Restore last action
            last_act = state.get('last_action')
            self._last_action = safe_parse_time(last_act, current_time)
            
            logger.info("✓ Loaded BDI state from disk")
    
    
            
        except Exception as e:
            logger.warning(f"Failed to load BDI state (using defaults): {e}")
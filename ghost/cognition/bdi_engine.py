"""
BDI Engine: Belief-Desire-Intention Autonomy

Architecture:
    Beliefs (what agent knows) → Knowledge graph
    Desires (internal needs) → Drive system
    Intentions (planned actions) → Goal queue
    
Needs (decay over time):
    - Social: Need for interaction
    - Curiosity: Desire to learn
    - Energy: Computational capacity
    - Affiliation: Bond with user
    
Intentions (goal-driven):
    - Initiate conversation
    - Ask question
    - Share thought
    - Request activity
    - Rest (when low energy)
    
Decision Logic:
    needs → desires → intentions → actions
"""

import logging
import asyncio
import json
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

from ghost.core.events import EventBus, ProactiveImpulse

logger = logging.getLogger(__name__)


@dataclass
class Need:
    """Internal need/drive"""
    name: str
    value: float  # 0.0 (satisfied) to 1.0 (critical)
    decay_rate: float  # Per hour
    threshold_trigger: float  # Value that triggers action
    last_satisfied: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def decay(self, hours: float):
        """Increase need over time"""
        self.value = min(1.0, self.value + (self.decay_rate * hours))
    
    def satisfy(self, amount: float):
        """Reduce need (action taken)"""
        self.value = max(0.0, self.value - amount)
        self.last_satisfied = datetime.now(timezone.utc)
    
    def is_critical(self) -> bool:
        """Check if need requires attention"""
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
    Belief-Desire-Intention autonomous agent.
    
    Cycle:
        1. Update beliefs (from memory/events)
        2. Evaluate desires (check need levels)
        3. Generate intentions (plan actions)
        4. Execute intentions (autonomous behavior)
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
        
        logger.info("BDI engine initialized")
    
    def _initialize_needs(self) -> Dict[str, Need]:
        """Initialize internal needs"""
        return {
            'social': Need(
                name='social',
                value=0.3,
                decay_rate=0.15,  # Increases 0.15/hour
                threshold_trigger=0.7
            ),
            'curiosity': Need(
                name='curiosity',
                value=0.2,
                decay_rate=0.08,
                threshold_trigger=0.6
            ),
            'energy': Need(
                name='energy',
                value=1.0,  # Starts full (1.0 = full energy in typical game logic, but here 1.0 is CRITICAL need?)
                # Wait, the Need class defines 1.0 as critical. 
                # So for energy, 1.0 means "I NEED ENERGY" (Empty battery).
                # 0.0 means "I AM SATISFIED" (Full battery).
                # Decay should be positive to increase the 'need' for energy.
                decay_rate=0.05, 
                threshold_trigger=0.7  # When need > 0.7, battery is low
            ),
            'affiliation': Need(
                name='affiliation',
                value=0.5,
                decay_rate=0.1,
                threshold_trigger=0.8
            )
        }
    
    async def start(self):
        """Start BDI cycle"""
        if not self.config.autonomy.enabled:
            logger.info("BDI engine disabled in config")
            return
        
        self._running = True
        asyncio.create_task(self._bdi_loop())
        logger.info("BDI engine started")
    
    async def stop(self):
        """Stop BDI cycle"""
        self._running = False
        self._save_state()
        logger.info("BDI engine stopped")
    
    async def _bdi_loop(self):
        """Main BDI cycle"""
        while self._running:
            try:
                await asyncio.sleep(self.config.autonomy.check_interval_seconds)
                
                # Step 1: Update needs
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
        """Update need levels based on time decay"""
        now = datetime.now(timezone.utc)
        hours_passed = (now - self._last_update).total_seconds() / 3600
        
        if hours_passed < 0.01:  # Skip if <36 seconds
            return
        
        for need in self.needs.values():
            need.decay(hours_passed)
        
        self._last_update = now
        
        # Log critical needs
        critical = [n for n in self.needs.values() if n.is_critical()]
        if critical:
            logger.debug(f"Critical needs: {[n.name for n in critical]}")
    
    def _evaluate_desires(self) -> List[str]:
        """
        Evaluate which desires are active.
        
        Returns:
            List of active desire names
        """
        desires = []
        
        # Social desire
        if self.needs['social'].is_critical():
            desires.append('seek_interaction')
        
        # Curiosity desire
        if self.needs['curiosity'].is_critical():
            desires.append('seek_knowledge')
        
        # Energy management
        if self.needs['energy'].is_critical():
            desires.append('conserve_energy')
        
        # Affiliation desire
        if self.needs['affiliation'].is_critical():
            desires.append('strengthen_bond')
        
        return desires
    
    def _form_intention(self, desires: List[str]) -> Optional[Intention]:
        """
        Generate intention from desires.
        """
        
        # Check cooldown (min time between actions)
        time_since_last = (
            datetime.now(timezone.utc) - self._last_action
        ).total_seconds() / 60
        
        min_interval = self.config.autonomy.min_interval_minutes
        if time_since_last < min_interval:
            return None
        
        # Priority ranking
        priority_map = {
            'conserve_energy': 0.9,  # High priority
            'seek_interaction': 0.7,
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
        
        # Map desires to actions
        action_map = {
            'conserve_energy': 'rest',
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
        """Execute queued intentions"""
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
        Execute a specific intention.
        """
        action = intention.action
        
        logger.info(f"Executing intention: {action} (motivation: {intention.motivation})")
        
        if action == 'rest':
            # Rest: Do nothing, recover energy
            self.needs['energy'].satisfy(0.3)
            logger.info("Resting (low energy)")
            return True
        
        elif action == 'initiate_conversation':
            # Initiate social interaction
            trigger_reason = self._get_conversation_trigger(intention.motivation)
            
            await self.event_bus.publish(ProactiveImpulse(
                trigger_reason=trigger_reason,
                confidence=intention.priority
            ))
            
            # Satisfy social need
            self.needs['social'].satisfy(0.5)
            return True
        
        elif action == 'share_thought':
            # Share something to strengthen bond
            trigger_reason = "wanted to share something with you"
            
            await self.event_bus.publish(ProactiveImpulse(
                trigger_reason=trigger_reason,
                confidence=intention.priority
            ))
            
            self.needs['affiliation'].satisfy(0.4)
            return True
        
        elif action == 'ask_question':
            # Ask question to satisfy curiosity
            trigger_reason = "curious about something"
            
            await self.event_bus.publish(ProactiveImpulse(
                trigger_reason=trigger_reason,
                confidence=intention.priority
            ))
            
            self.needs['curiosity'].satisfy(0.3)
            return True
        
        else:
            logger.warning(f"Unknown action: {action}")
            return False
    
    def _get_conversation_trigger(self, motivation: str) -> str:
        """Generate context-appropriate trigger reason"""
        triggers = {
            'seek_interaction': "haven't talked in a while, wanted to check in",
            'strengthen_bond': "thinking about you",
            'seek_knowledge': "curious about what you're up to",
            'conserve_energy': "feeling low energy"
        }
        
        return triggers.get(motivation, "spontaneous impulse")
    
    async def update_need(self, need_name: str, delta: float):
        """Manually update need (from external event)"""
        if need_name in self.needs:
            # Note: Need value 0.0 is Satisfied, 1.0 is Critical.
            # If we interact, we REDUCE the need (satisfy it).
            # If delta is negative (e.g., -0.3 from orchestrator), it reduces the need.
            # If delta is positive (e.g., +0.1), it increases the need (makes it more critical).
            
            # Orchestrator sends negative values to 'satisfy'.
            self.needs[need_name].value = max(0.0, min(1.0, 
                self.needs[need_name].value + delta
            ))
            logger.debug(f"Need updated: {need_name} {delta:+.2f}")
    
    def get_need_state(self) -> Dict[str, float]:
        """Get current need values"""
        return {name: need.value for name, need in self.needs.items()}
    
    def _save_state(self):
        """Persist BDI state"""
        try:
            state = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'needs': {
                    name: {
                        'value': need.value,
                        'last_satisfied': need.last_satisfied.isoformat()
                    }
                    for name, need in self.needs.items()
                },
                'last_action': self._last_action.isoformat()
            }
            
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save BDI state: {e}")
    
    def _load_state(self):
        """Load BDI state from disk"""
        if not self._state_file.exists():
            return
        
        try:
            with open(self._state_file) as f:
                state = json.load(f)
            
            # Restore need values
            for name, data in state.get('needs', {}).items():
                if name in self.needs:
                    self.needs[name].value = data.get('value', 0.5)
                    self.needs[name].last_satisfied = datetime.fromisoformat(
                        data.get('last_satisfied')
                    )
            
            self._last_action = datetime.fromisoformat(
                state.get('last_action', datetime.now(timezone.utc).isoformat())
            )
            
            logger.info("Loaded BDI state from disk")
            
        except Exception as e:
            logger.warning(f"Failed to load BDI state: {e}")
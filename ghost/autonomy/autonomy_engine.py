"""Autonomous decision-making engine for proactive conversation initiation."""

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

from ghost.core.events import EventBus, ProactiveImpulse, MessageReceived, UserActivityChanged
from ghost.core.config import AutonomyConfig
from ghost.emotion.emotion_service import EmotionService
from ghost.autonomy.triggers import TriggerEvaluator

logger = logging.getLogger(__name__)


class AutonomyEngine:
    """Manages autonomous behavior and proactive conversation initiation."""
    
    def __init__(
        self,
        config: AutonomyConfig,
        event_bus: EventBus,
        emotion_service: EmotionService
    ):
        self.config = config
        self.event_bus = event_bus
        self.emotion_service = emotion_service
        self.trigger_evaluator = TriggerEvaluator(
            silence_threshold_minutes=config.silence_threshold_minutes
        )
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._last_initiation_time: Optional[datetime] = None
        self._running = False
        
        # Activity tracking (to prevent spam)
        self._last_activity_reaction: Optional[datetime] = None
        self._activity_cooldown_minutes = 15  # Don't spam about the same activity
        
        # Subscribe to message events to track activity
        self.event_bus.subscribe(MessageReceived, self._on_message_received)
        
        # Subscribe to activity changes (NEW)
        self.event_bus.subscribe(UserActivityChanged, self._on_activity_changed)
        
        logger.info("Autonomy engine initialized with activity awareness")
    
    async def start(self):
        """Start autonomy monitoring."""
        if not self.config.enabled:
            logger.info("Autonomy disabled in config")
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._autonomy_loop())
        logger.info("Autonomy engine started")
    
    async def stop(self):
        """Stop autonomy monitoring."""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Autonomy engine stopped")
    
    async def _on_message_received(self, event: MessageReceived):
        """Update trigger state when messages are received."""
        self.trigger_evaluator.update_last_message_time()
        logger.debug("Updated last message time for autonomy triggers")
    
    async def _on_activity_changed(self, event: UserActivityChanged):
        """
        React to user activity changes (NEW FEATURE).
        
        Triggers:
        - User starts gaming → Comment on the game
        - User switches from gaming to coding → Tease about rage quitting
        - User goes idle after gaming → Ask how it went
        """
        logger.info(
            f"Activity change detected: {event.old_activity} → {event.new_activity} "
            f"({event.app_name or 'N/A'})"
        )
        
        # Check cooldown to prevent spam
        if self._last_activity_reaction:
            time_since_last = datetime.now(timezone.utc) - self._last_activity_reaction
            if time_since_last < timedelta(minutes=self._activity_cooldown_minutes):
                logger.debug(
                    f"Activity reaction cooldown active "
                    f"({time_since_last.total_seconds()/60:.1f}min)"
                )
                return
        
        # Determine if this is worth reacting to
        should_react, trigger_reason = self._evaluate_activity_change(event)
        
        if should_react:
            logger.info(f"🎯 Reacting to activity change: {trigger_reason}")
            
            # Fire proactive impulse
            await self.event_bus.publish(ProactiveImpulse(
                trigger_reason=trigger_reason,
                confidence=0.8
            ))
            
            self._last_activity_reaction = datetime.now(timezone.utc)
            self._last_initiation_time = datetime.now(timezone.utc)
    
    def _evaluate_activity_change(
        self,
        event: UserActivityChanged
    ) -> tuple[bool, str]:
        """
        Decide if activity change warrants a reaction.
        
        Returns:
            (should_react, trigger_reason)
        """
        old = event.old_activity.lower()
        new = event.new_activity.lower()
        app = event.app_name.lower() if event.app_name else ""
        
        # === GAMING TRIGGERS ===
        if new == "gaming":
            # User started gaming
            if "rocket" in app:
                return True, "noticed you launched rocket league (time to miss aerials?)"
            elif "league" in app:
                return True, "league of legends? rip your mental"
            else:
                return True, f"starting {app}? gl hf"
        
        # Gaming → Coding (rage quit?)
        if old == "gaming" and new == "coding":
            return True, "gave up on the game already? <SPLIT> back to copy pasting ai code?"
        
        # Gaming → Idle (how'd it go?)
        if old == "gaming" and new == "idle":
            return True, "done gaming? did you rank up or tilt queue?"
        
        # === CODING TRIGGERS ===
        if new == "coding" and old != "coding":
            return True, "time to write some code <SPLIT> or just add comments?"
        
        # === IDLE TRIGGERS ===
        if new == "idle" and old in ["gaming", "coding"]:
            return True, "taking a break? go touch grass"
        
        # Default: Not significant enough
        return False, ""
    
    async def _autonomy_loop(self):
        """Main autonomy monitoring loop."""
        while self._running:
            try:
                await asyncio.sleep(self.config.check_interval_seconds)
                
                if await self._should_initiate():
                    await self._initiate_conversation()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Autonomy loop error: {e}", exc_info=True)
    
    async def _should_initiate(self) -> bool:
        """Determine if AI should initiate conversation."""
        # Check minimum interval
        if self._last_initiation_time:
            time_since_last = datetime.now(timezone.utc) - self._last_initiation_time
            min_interval = timedelta(minutes=self.config.min_interval_minutes)
            
            if time_since_last < min_interval:
                return False
        
        # Get circadian modifier
        circadian = self.emotion_service.circadian
        circadian_modifier = circadian.get_proactivity_modifier()
        
        # Calculate probability
        base_probability = self.config.trigger_probability
        adjusted_probability = base_probability * circadian_modifier
        
        # Random roll
        if random.random() > adjusted_probability:
            return False
        
        # Evaluate triggers
        trigger_result = await self.trigger_evaluator.evaluate()
        
        if trigger_result:
            logger.info(f"Autonomy trigger fired: {trigger_result}")
            return True
        
        return False
    
    async def _initiate_conversation(self):
        """Initiate autonomous conversation."""
        trigger_reason = await self.trigger_evaluator.evaluate()
        
        if not trigger_reason:
            trigger_reason = "spontaneous check-in"
        
        # Emit impulse event (orchestrator will handle generation and Discord will send)
        await self.event_bus.publish(ProactiveImpulse(
            trigger_reason=trigger_reason,
            confidence=0.7
        ))
        
        self._last_initiation_time = datetime.now(timezone.utc)
        logger.info(f"Initiated autonomous conversation: {trigger_reason}")
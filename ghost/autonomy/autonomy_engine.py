"""Autonomous decision-making engine for proactive conversation initiation."""

import asyncio
import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

from ghost.core.events import EventBus, ProactiveImpulse, MessageReceived
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
        
        # Subscribe to message events to track activity
        self.event_bus.subscribe(MessageReceived, self._on_message_received)
        
        logger.info("Autonomy engine initialized")
    
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
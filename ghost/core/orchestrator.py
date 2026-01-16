"""Main orchestrator coordinating all system components."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from ghost.core.events import (
    EventBus, MessageReceived, ResponseGenerated,
    ProactiveImpulse, AutonomousMessageSent
)
from ghost.core.interfaces import (
    IMemoryProvider, IEmotionProvider, IInferenceEngine,
    ICryostasisController, ISensor, Message
)
from ghost.core.config import SystemConfig

logger = logging.getLogger(__name__)


class Orchestrator:
    """Central coordinator for Ghost system."""
    
    def __init__(
        self,
        config: SystemConfig,
        event_bus: EventBus,
        memory: IMemoryProvider,
        emotion: IEmotionProvider,
        inference: IInferenceEngine,
        cryostasis: ICryostasisController,
        sensors: List[ISensor]
    ):
        self.config = config
        self.event_bus = event_bus
        self.memory = memory
        self.emotion = emotion
        self.inference = inference
        self.cryostasis = cryostasis
        self.sensors = sensors
        
        # Subscribe to events
        self.event_bus.subscribe(MessageReceived, self.handle_message)
        self.event_bus.subscribe(ProactiveImpulse, self.handle_impulse)
        
        # Track last message time for autonomy
        self._last_message_time: Optional[datetime] = None
        
        logger.info("Orchestrator initialized")
    
    async def handle_message(self, event: MessageReceived) -> Optional[str]:
        """Handle incoming user message."""
        try:
            # Update last message time for autonomy triggers
            self._last_message_time = datetime.now(timezone.utc)
            
            # Check if hibernating
            if self.cryostasis.is_hibernating():
                logger.info("System hibernating, waking up for message")
                await self.cryostasis.wake()
            
            # Analyze sentiment and update emotional state
            pad_deltas = self.emotion.pad_model.analyze_sentiment(event.content)
            await self.emotion.update_state(
                pleasure_delta=pad_deltas[0],
                arousal_delta=pad_deltas[1],
                dominance_delta=pad_deltas[2],
                reason=f"user_message:{event.user_name}"
            )
            
            # Store user message
            user_message = Message(
                role="user",
                content=f"{event.user_name}: {event.content}",
                metadata={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_id": event.user_id,
                    "user_name": event.user_name
                }
            )
            await self.memory.add_message(user_message)
            
            # Get context from hierarchical memory
            context = await self.memory.get_context(event.content)
            
            # Get emotional context
            emotional_context = self.emotion.get_contextual_modifiers()
            
            # Get sensory context
            sensory_context = await self._gather_sensory_context()
            
            # Build conversation context
            from ghost.inference.inference_service import InferenceService
            if isinstance(self.inference, InferenceService):
                context_messages = self.inference.build_conversation_context(
                    working_memory=context.get('working', []),
                    episodic_memory=context.get('episodic', []),
                    semantic_memory=context.get('semantic', []),
                    emotional_context=emotional_context,
                    sensory_context=sensory_context
                )
            else:
                # Fallback for mock/test services
                context_messages = context.get('episodic', [])
            
            # Generate response with error handling
            start_time = datetime.now(timezone.utc)
            try:
                response = await self.inference.generate(context_messages)
            except Exception as e:
                logger.error(f"Inference failed: {e}", exc_info=True)
                response = "sorry, i'm having trouble thinking right now... maybe ollama isn't running?"
            
            generation_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Store assistant response
            assistant_message = Message(
                role="assistant",
                content=response,
                metadata={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "generation_time_ms": generation_time
                }
            )
            await self.memory.add_message(assistant_message)
            
            # Emit response event
            await self.event_bus.publish(ResponseGenerated(
                content=response,
                context_used=[msg.content for msg in context.get('semantic', [])],
                generation_time_ms=generation_time
            ))
            
            logger.info(f"Generated response in {generation_time:.0f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return "sorry, i'm having trouble thinking right now..."
    
    async def handle_impulse(self, event: ProactiveImpulse) -> Optional[str]:
        """Handle autonomous initiation impulse."""
        try:
            if self.cryostasis.is_hibernating():
                logger.debug("Skipping impulse - system hibernating")
                return None
            
            # Get emotional context
            emotional_context = self.emotion.get_contextual_modifiers()
            
            # Build impulse prompt
            from ghost.inference.prompt_builder import PromptBuilder
            builder = PromptBuilder(self.config.persona)
            impulse_content = builder.build_impulse_prompt(
                trigger_reason=event.trigger_reason,
                emotional_context=emotional_context
            )
            
            # Generate response
            impulse_message = Message(
                role="system",
                content=impulse_content,
                metadata={}
            )
            
            try:
                response = await self.inference.generate([impulse_message])
            except Exception as e:
                logger.error(f"Autonomous generation failed: {e}", exc_info=True)
                return None
            
            # Store as assistant message
            assistant_message = Message(
                role="assistant",
                content=response,
                metadata={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "autonomous": True,
                    "trigger": event.trigger_reason
                }
            )
            await self.memory.add_message(assistant_message)
            
            # Emit autonomous message event for Discord to send
            await self.event_bus.publish(AutonomousMessageSent(
                content=response,
                channel_id=self.config.discord.primary_channel_id
            ))
            
            logger.info(f"Autonomous initiation: {event.trigger_reason}")
            return response
            
        except Exception as e:
            logger.error(f"Error handling impulse: {e}", exc_info=True)
            return None
    
    async def _gather_sensory_context(self) -> str:
        """Gather context from all sensors (async-safe)."""
        context_parts = []
        for sensor in self.sensors:
            try:
                # Sensors are synchronous, but we could run them in executor if needed
                context = sensor.get_context()
                if context:
                    context_parts.append(context)
            except Exception as e:
                logger.error(f"Sensor {sensor.get_name()} failed: {e}")
        
        return "\n".join(context_parts)
    
    def get_last_message_time(self) -> Optional[datetime]:
        """Get timestamp of last message (for autonomy triggers)."""
        return self._last_message_time
    
    async def health_check(self) -> dict:
        """Perform comprehensive system health check."""
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inference_available": False,
            "hibernating": False,
            "memory_stats": {},
            "emotional_state": "",
            "sensors_active": 0,
            "event_bus_running": False,
        }
        
        try:
            # Check inference
            health["inference_available"] = await self.inference.is_available()
            
            # Check cryostasis
            health["hibernating"] = self.cryostasis.is_hibernating()
            
            # Check memory
            if hasattr(self.memory, 'vector_store'):
                health["memory_stats"] = await self.memory.vector_store.get_stats()
            
            # Check emotion
            emotional_state = await self.emotion.get_state()
            health["emotional_state"] = emotional_state.to_description()
            
            # Check sensors
            health["sensors_active"] = len([s for s in self.sensors if s.get_context()])
            
            # Check event bus
            health["event_bus_running"] = self.event_bus._running
            
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            health["error"] = str(e)
        
        return health
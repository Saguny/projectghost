"""Main orchestrator coordinating all system components."""

import logging
from datetime import datetime
from typing import List, Optional

from ghost.core.events import (
    EventBus, MessageReceived, ResponseGenerated,
    ProactiveImpulse
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
        
        logger.info("Orchestrator initialized")
    
    async def handle_message(self, event: MessageReceived) -> Optional[str]:
        """Handle incoming user message."""
        try:
            # Check if hibernating
            if self.cryostasis.is_hibernating():
                logger.info("System hibernating, ignoring message")
                return None
            
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
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_id": event.user_id,
                    "user_name": event.user_name
                }
            )
            await self.memory.add_message(user_message)
            
            # Get context
            recent_messages = await self.memory.get_recent(limit=10)
            relevant_memories = await self.memory.search_semantic(
                event.content,
                limit=self.config.memory.semantic_search_limit
            )
            
            # Get emotional context
            emotional_context = self.emotion.get_contextual_modifiers()
            
            # Get sensory context
            sensory_context = self._gather_sensory_context()
            
            # Build conversation context
            from ghost.inference.inference_service import InferenceService
            if isinstance(self.inference, InferenceService):
                context_messages = self.inference.build_conversation_context(
                    recent_messages=recent_messages,
                    relevant_memories=relevant_memories,
                    emotional_context=emotional_context,
                    sensory_context=sensory_context
                )
            else:
                context_messages = recent_messages
            
            # Generate response
            start_time = datetime.now()
            response = await self.inference.generate(context_messages)
            generation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Store assistant response
            assistant_message = Message(
                role="assistant",
                content=response,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            await self.memory.add_message(assistant_message)
            
            # Emit response event
            await self.event_bus.publish(ResponseGenerated(
                content=response,
                context_used=[msg.content for msg in relevant_memories],
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
            
            response = await self.inference.generate([impulse_message])
            
            # Store as assistant message
            assistant_message = Message(
                role="assistant",
                content=response,
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "autonomous": True,
                    "trigger": event.trigger_reason
                }
            )
            await self.memory.add_message(assistant_message)
            
            logger.info(f"Autonomous initiation: {event.trigger_reason}")
            return response
            
        except Exception as e:
            logger.error(f"Error handling impulse: {e}", exc_info=True)
            return None
    
    def _gather_sensory_context(self) -> str:
        """Gather context from all sensors."""
        context_parts = []
        for sensor in self.sensors:
            try:
                context = sensor.get_context()
                if context:
                    context_parts.append(context)
            except Exception as e:
                logger.error(f"Sensor {sensor.get_name()} failed: {e}")
        
        return "\n".join(context_parts)
    
    async def health_check(self) -> dict:
        """Perform system health check."""
        return {
            "inference_available": await self.inference.is_available(),
            "hibernating": self.cryostasis.is_hibernating(),
            "memory_stats": await self.memory.vector_store.get_stats(),
            "emotional_state": (await self.emotion.get_state()).to_description(),
            "sensors_active": len(self.sensors)
        }
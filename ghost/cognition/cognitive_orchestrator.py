"""
Cognitive Orchestrator: Unified Agent Control (Updated for Personality Evolution)

NEW FEATURE: "Ego Injection"
- Fetches BOTH user beliefs AND agent beliefs
- Passes agent's self-knowledge into CognitiveCore
- Enables opinion formation and personality continuity

Architecture:
    User Input →
        1. Gather context (memory + sensors + BELIEFS)
        2. Cognitive Core (Think → Validate → Speak)
        3. Belief System (Store user facts + AGENT OPINIONS)
        4. Validator (Reality check)
        5. BDI Engine (Autonomy)
    → Output
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ghost.core.events import (
    EventBus, MessageReceived, ResponseGenerated,
    ProactiveImpulse, AutonomousMessageSent
)
from ghost.core.interfaces import Message
from ghost.core.config import SystemConfig

from ghost.cognition.cognitive_core import CognitiveCore, ThinkOutput
from ghost.cognition.validator import RealityValidator, ValidationResult
from ghost.cognition.belief_system import BeliefSystem
from ghost.cognition.bdi_engine import BDIEngine

# Original services (still used)
from ghost.memory.memory_service import MemoryService
from ghost.emotion.emotion_service import EmotionService
from ghost.inference.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class CognitiveOrchestrator:
    """
    Cognitive agent orchestrator.
    
    Pipeline:
        Input → Think → Validate → Speak → Memory → Output
        
    Autonomy:
        BDI → Desires → Intentions → Actions → Events
    """
    
    def __init__(
        self,
        config: SystemConfig,
        event_bus: EventBus,
        memory: MemoryService,
        emotion: EmotionService,
        ollama_client: OllamaClient,
        cryostasis,
        sensors
    ):
        self.config = config
        self.event_bus = event_bus
        self.memory = memory
        self.emotion = emotion
        self.cryostasis = cryostasis
        self.sensors = sensors
        
        # Initialize cognitive components
        # FIX: Correct assignment operator
        self.belief_system = BeliefSystem()
        
        self.cognitive_core = CognitiveCore(
            ollama_client=ollama_client,
            persona_config=config.persona
        )
        
        self.validator = RealityValidator(
            belief_system=self.belief_system
        )
        
        self.bdi_engine = BDIEngine(
            event_bus=event_bus,
            belief_system=self.belief_system,
            config=config
        )
        
        # Subscribe to events
        self.event_bus.subscribe(MessageReceived, self.handle_message)
        self.event_bus.subscribe(ProactiveImpulse, self.handle_impulse)
        
        # Track last message
        self._last_message_time: Optional[datetime] = None
        
        logger.info("Cognitive orchestrator initialized")

    async def start(self):
        """Start all background cognitive processes."""
        # FIX: Hydrate the Belief System (Fixes 0 Identity bug)
        await self.belief_system.initialize()
        
        # Start the Metabolic Loop (Needs/Drives)
        await self.bdi_engine.start()
        
        logger.info("Cognitive Orchestrator started")

    async def stop(self):
        """Stop all background cognitive processes."""
        await self.bdi_engine.stop()
    
    async def handle_message(self, event: MessageReceived) -> Optional[str]:
        """
        Handle user message with full cognitive pipeline.
        
        Pipeline:
            1. Context gathering (memory + sensors + BELIEFS)
            2. Think stage (internal reasoning with EGO AWARENESS)
            3. Validation (reality check)
            4. Speak stage (character dialogue)
            5. Belief updates (USER + AGENT)
            6. Memory storage
            7. Need satisfaction
        """
        try:
            self._last_message_time = datetime.now(timezone.utc)
            
            # Wake from cryostasis if needed
            if self.cryostasis.is_hibernating():
                logger.info("Waking from cryostasis for message")
                await self.cryostasis.wake()
            
            # Pause monitoring during inference
            await self.cryostasis.stop_monitoring()
            
            # Step 1: Gather context (INCLUDING BELIEFS)
            context = await self._gather_context(event.content)
            
            # NEW: Fetch BOTH user beliefs AND agent beliefs
            user_beliefs = await self.belief_system.get_all('user')
            agent_profile = await self.belief_system.get_agent_profile()
            
            # Combine into unified belief structure
            beliefs = {
                'user': user_beliefs,
                'agent': agent_profile
            }
            
            needs = self.bdi_engine.get_need_state()
            
            # Step 2: Cognitive processing (Think → Validate → Speak)
            think_output, speech = await self._cognitive_process(
                user_input=event.content,
                context=context,
                beliefs=beliefs,  # NOW INCLUDES AGENT'S SELF-KNOWLEDGE
                needs=needs
            )
            
            # Step 3: Update emotional state (from think output)
            await self._update_emotion(think_output)
            
            # Step 4: Store beliefs (USER + AGENT)
            await self._store_beliefs(think_output, event.user_name)
            
            # Step 5: Store memory
            await self._store_interaction(event, speech)
            
            # Step 6: Satisfy needs
            await self._satisfy_needs(think_output)
            
            # Resume monitoring
            await self.cryostasis.start_monitoring()
            
            # Emit response event
            await self.event_bus.publish(ResponseGenerated(
                content=speech,
                context_used=[],
                generation_time_ms=0.0
            ))
            
            logger.info(f"Response generated (intent: {think_output.intent})")
            return speech
            
        except Exception as e:
            await self.cryostasis.start_monitoring()
            logger.error(f"Message handling failed: {e}", exc_info=True)
            return "sorry, i'm having trouble thinking right now..."
    
    async def _cognitive_process(
        self,
        user_input: str,
        context: Dict[str, Any],
        beliefs: Dict[str, Any],
        needs: Dict[str, float]
    ) -> tuple[ThinkOutput, str]:
        """
        Run full cognitive pipeline.
        
        Returns:
            (think_output, final_speech)
        """
        
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # THINK (NOW WITH AGENT SELF-KNOWLEDGE)
            think_output, speech = await self.cognitive_core.process(
                user_input=user_input,
                context=context,
                beliefs=beliefs,  # Contains user + agent
                needs=needs
            )
            
            # VALIDATE
            validation = await self.validator.validate(
                think_output=think_output,
                speech=speech
            )
            
            if validation.approved:
                logger.debug(f"Validation passed (attempt {attempt})")
                return think_output, speech
            
            # REJECTION HANDLING
            logger.warning(f"Validation failed (attempt {attempt}): {validation}")
            
            # Try auto-correction
            corrected = await self.validator.auto_correct(
                violations=validation.violations,
                think_output=think_output,
                speech=speech
            )
            
            if corrected:
                logger.info("Auto-corrected speech")
                return think_output, corrected
            
            # Critical violations cannot be auto-corrected
            if validation.severity == "critical":
                logger.error(
                    f"Critical validation failure: {validation.violations}"
                )
                # Force safe response
                safe_speech = "sorry, i had a confusing thought there"
                return think_output, safe_speech
        
        # Max attempts reached
        logger.error("Cognitive process failed after max attempts")
        fallback_speech = "i'm having trouble organizing my thoughts"
        return think_output, fallback_speech
    
    async def _gather_context(
        self,
        query: str
    ) -> Dict[str, Any]:
        """Gather full context (memory + sensors)"""
        
        # Memory context
        memory_context = await self.memory.get_context(query)
        
        # Emotional context
        emotional_context = self.emotion.get_contextual_modifiers()
        
        # Sensory context
        sensory_parts = []
        for sensor in self.sensors:
            try:
                ctx = sensor.get_context()
                if ctx:
                    sensory_parts.append(ctx)
            except Exception as e:
                logger.error(f"Sensor {sensor.get_name()} failed: {e}")
        
        sensory_context = "\n".join(sensory_parts)
        
        return {
            **memory_context,
            'emotional': emotional_context,
            'sensory': sensory_context
        }
    
    async def _update_emotion(self, think_output: ThinkOutput):
        """Update emotional state from think output"""
        
        # Map emotion string to PAD deltas
        emotion_map = {
            'happy': (0.3, 0.2, 0.1),
            'sad': (-0.3, -0.1, -0.1),
            'excited': (0.2, 0.4, 0.2),
            'calm': (0.1, -0.2, 0.0),
            'anxious': (-0.2, 0.3, -0.2),
            'confused': (-0.1, 0.0, -0.3),
            'neutral': (0.0, 0.0, 0.0)
        }
        
        emotion = think_output.emotion.lower()
        deltas = emotion_map.get(emotion, (0.0, 0.0, 0.0))
        
        await self.emotion.update_state(
            pleasure_delta=deltas[0],
            arousal_delta=deltas[1],
            dominance_delta=deltas[2],
            reason=f"think_stage:{think_output.intent}"
        )
    
    async def _store_beliefs(
        self,
        think_output: ThinkOutput,
        user_name: str
    ):
        """
        Store beliefs from think output.
        
        NOW SUPPORTS: Storing agent beliefs (entity='agent')
        This is how the AI remembers its own opinions!
        """
        
        for belief_update in think_output.belief_updates:
            entity = belief_update.get('entity', 'user')
            relation = belief_update.get('relation')
            value = belief_update.get('value')
            
            if not all([relation, value]):
                continue
            
            # Special handling for user identity
            if entity == 'user' and relation == 'name' and not value:
                value = user_name
            
            # NEW: Log when agent updates its own beliefs
            if entity == 'agent':
                logger.info(
                    f" PERSONALITY UPDATE: Agent believes "
                    f"({relation}, {value})"
                )
            
            await self.belief_system.store(
                entity=entity,
                relation=relation,
                value=value,
                confidence=think_output.confidence,
                source='inference'
            )
            
            logger.debug(f"Stored belief: ({entity}, {relation}, {value})")
    
    async def _store_interaction(
        self,
        event: MessageReceived,
        speech: str
    ):
        """Store conversation in memory"""
        
        # User message
        user_msg = Message(
            role="user",
            content=f"{event.user_name}: {event.content}",
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": event.user_id,
                "user_name": event.user_name
            }
        )
        await self.memory.add_message(user_msg)
        
        # Agent response
        agent_msg = Message(
            role="assistant",
            content=speech,
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        await self.memory.add_message(agent_msg)
    
    async def _satisfy_needs(self, think_output: ThinkOutput):
        """Update BDI needs from interaction"""
        
        # Social interaction satisfies social need
        await self.bdi_engine.update_need('social', -0.3)
        
        # Curiosity increases if asking questions
        if '?' in think_output.speech_plan:
            await self.bdi_engine.update_need('curiosity', 0.1)
        
        # Energy cost of thinking
        await self.bdi_engine.update_need('energy', -0.05)
        
        # Process need updates from think output
        for need_name, delta in think_output.needs_update.items():
            await self.bdi_engine.update_need(need_name, delta)
    
    async def handle_impulse(self, event: ProactiveImpulse) -> Optional[str]:
        """Handle autonomous impulse (from BDI engine)"""
        
        try:
            if self.cryostasis.is_hibernating():
                logger.debug("Skipping impulse (hibernating)")
                return None
            
            # Gather context (including beliefs)
            context = await self._gather_context(event.trigger_reason)
            user_beliefs = await self.belief_system.get_all('user')
            agent_profile = await self.belief_system.get_agent_profile()
            beliefs = {'user': user_beliefs, 'agent': agent_profile}
            needs = self.bdi_engine.get_need_state()
            
            # Pause monitoring
            await self.cryostasis.stop_monitoring()
            
            # Build impulse input
            impulse_input = f"[AUTONOMOUS] Trigger: {event.trigger_reason}"
            
            # Think → Validate → Speak
            think_output, speech = await self._cognitive_process(
                user_input=impulse_input,
                context=context,
                beliefs=beliefs,
                needs=needs
            )
            
            # Resume monitoring
            await self.cryostasis.start_monitoring()
            
            # Store autonomous message
            agent_msg = Message(
                role="assistant",
                content=speech,
                metadata={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "autonomous": True,
                    "trigger": event.trigger_reason
                }
            )
            await self.memory.add_message(agent_msg)
            
            # Emit event for Discord
            await self.event_bus.publish(AutonomousMessageSent(
                content=speech,
                channel_id=self.config.discord.primary_channel_id
            ))
            
            logger.info(f"Autonomous message: {event.trigger_reason}")
            return speech
            
        except Exception as e:
            await self.cryostasis.start_monitoring()
            logger.error(f"Impulse handling failed: {e}", exc_info=True)
            return None
    
    async def health_check(self) -> dict:
        """System health check"""
        
        belief_count = len(await self.belief_system.search(limit=1000))
        agent_profile = await self.belief_system.get_agent_profile()
        needs = self.bdi_engine.get_need_state()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cognitive_core": "active",
            "validator": "active",
            "belief_system": f"{belief_count} beliefs",
            "agent_opinions": len(agent_profile['opinions']),
            "agent_traits": len(agent_profile['traits']),
            "bdi_engine": "active",
            "needs": needs,
            "hibernating": self.cryostasis.is_hibernating(),
            "emotional_state": (await self.emotion.get_state()).to_description()
        }
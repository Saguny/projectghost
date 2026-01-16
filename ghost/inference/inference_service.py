"""Inference service coordinating LLM generation."""

from typing import List, Optional
import logging

from ghost.core.interfaces import IInferenceEngine, Message
from ghost.inference.ollama_client import OllamaClient
from ghost.inference.prompt_builder import PromptBuilder
from ghost.core.config import OllamaConfig, PersonaConfig

logger = logging.getLogger(__name__)


class InferenceService(IInferenceEngine):
    """Coordinates LLM inference with prompt building and generation."""
    
    def __init__(
        self,
        ollama_config: OllamaConfig,
        persona_config: PersonaConfig
    ):
        self.ollama_client = OllamaClient(ollama_config)
        self.prompt_builder = PromptBuilder(persona_config)
        self.persona_config = persona_config
        
        # Loop detection
        self._last_response = ""
        self._loop_count = 0
        
        logger.info("Inference service initialized")
    
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: int = 500
    ) -> str:
        """Generate a response using the LLM."""
        if temperature is None:
            temperature = self.persona_config.temperature
        
        try:
            # Generate response
            response = await self.ollama_client.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Loop detection
            if response.strip().lower() == self._last_response.strip().lower():
                self._loop_count += 1
                logger.warning(f"Loop detected (count: {self._loop_count})")
                
                if self._loop_count >= 2:
                    # Break loop with higher temperature
                    logger.info("Breaking loop with temperature increase")
                    response = await self.ollama_client.generate(
                        messages=messages,
                        temperature=min(temperature + 0.3, 1.5),
                        max_tokens=max_tokens
                    )
                    self._loop_count = 0
            else:
                self._loop_count = 0
            
            self._last_response = response
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise
    
    async def is_available(self) -> bool:
        """Check if inference engine is available."""
        return await self.ollama_client.health_check()
    
    def build_conversation_context(
        self,
        working_memory: List[Message],
        episodic_memory: List[Message],
        semantic_memory: List[Message],
        emotional_context: dict,
        sensory_context: str
    ) -> List[Message]:
        """Build complete conversation context for generation."""
        return self.prompt_builder.build_conversation_context(
            working_memory=working_memory,
            episodic_memory=episodic_memory,
            semantic_memory=semantic_memory,
            emotional_context=emotional_context,
            sensory_context=sensory_context
        )
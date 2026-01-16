"""LLM inference and prompt building.

This module handles all LLM-related operations:
- Connection to Ollama API
- Dynamic prompt construction
- Context window management
- Response generation
- Loop detection

Key Features:
- Retry logic with exponential backoff
- Temperature-based loop breaking
- Token budget management
- Memory deduplication in prompts
- Emotional context integration

Usage:
    from ghost.inference import InferenceService, OllamaClient
    from ghost.core.config import OllamaConfig, PersonaConfig
    
    ollama_config = OllamaConfig()
    persona_config = PersonaConfig()
    
    service = InferenceService(ollama_config, persona_config)
    
    # Generate response
    response = await service.generate(messages, temperature=0.8)
"""

from ghost.inference.inference_service import InferenceService
from ghost.inference.ollama_client import OllamaClient, OllamaConnectionError
from ghost.inference.prompt_builder import PromptBuilder

__all__ = [
    "InferenceService",
    "OllamaClient",
    "OllamaConnectionError",
    "PromptBuilder",
]


def create_inference_service(
    ollama_config,
    persona_config
) -> InferenceService:
    """Factory function to create a configured inference service.
    
    Args:
        ollama_config: OllamaConfig with API settings
        persona_config: PersonaConfig with model parameters
        
    Returns:
        Configured InferenceService
    """
    return InferenceService(ollama_config, persona_config)


async def check_ollama_availability(url: str = "http://localhost:11434") -> bool:
    """Quick check if Ollama is running.
    
    Args:
        url: Ollama API URL
        
    Returns:
        True if Ollama is available, False otherwise
    """
    from ghost.core.config import OllamaConfig
    
    config = OllamaConfig(url=url)
    client = OllamaClient(config)
    
    return await client.health_check()
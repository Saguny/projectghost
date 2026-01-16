"""Ollama API client with retry logic."""

from typing import List, Dict, Any
import logging
import aiohttp
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ghost.core.interfaces import Message
from ghost.core.config import OllamaConfig

logger = logging.getLogger(__name__)


class OllamaConnectionError(Exception):
    """Ollama connection error."""
    pass


class OllamaClient:
    """Client for Ollama LLM API with robust error handling."""
    
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.base_url = config.url
        self.model = config.model
        self.timeout = aiohttp.ClientTimeout(total=config.timeout_seconds)
    
    @retry(
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.8,
        max_tokens: int = 500
    ) -> str:
        """Generate completion from Ollama."""
        url = f"{self.base_url}/api/chat"
        
        # Convert to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_k": 50,
                "repeat_penalty": 1.2,
                "stop": ["### Instruction:", "### Response:", "User:", "Sagun:"]
            }
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise OllamaConnectionError(
                            f"Ollama returned {resp.status}: {error_text}"
                        )
                    
                    data = await resp.json()
                    content = data.get('message', {}).get('content', '')
                    
                    if not content:
                        raise OllamaConnectionError("Empty response from Ollama")
                    
                    return content.strip()
        
        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            raise OllamaConnectionError(f"Failed to connect to Ollama: {e}")
        except asyncio.TimeoutError:
            logger.error("Ollama request timed out")
            raise OllamaConnectionError("Ollama request timed out")
    
    async def health_check(self) -> bool:
        """Check if Ollama is available."""
        url = f"{self.base_url}/api/tags"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False
    
    async def unload_model(self) -> bool:
        """Unload model from VRAM."""
        url = f"{self.base_url}/api/generate"
        payload = {"model": self.model, "keep_alive": 0}
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(url, json=payload) as resp:
                    success = resp.status == 200
                    if success:
                        logger.info(f"Unloaded model: {self.model}")
                    return success
        except Exception as e:
            logger.error(f"Failed to unload model: {e}")
            return False
"""Interface definitions for all major components."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class Message:
    """Standard message format."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Dict[str, Any]


@dataclass
class EmotionalState:
    """PAD emotional state representation."""
    pleasure: float  # -1 to 1
    arousal: float   # -1 to 1
    dominance: float  # -1 to 1
    
    def to_description(self) -> str:
        """Convert to natural language."""
        mood = "positive" if self.pleasure > 0 else "somber"
        energy = "energetic" if self.arousal > 0 else "calm"
        confidence = "confident" if self.dominance > 0 else "uncertain"
        return f"{mood}, {energy}, {confidence}"


class IMemoryProvider(ABC):
    """Memory storage and retrieval interface."""
    
    @abstractmethod
    async def add_message(self, message: Message) -> None:
        """Store a message."""
        pass
    
    @abstractmethod
    async def search_semantic(self, query: str, limit: int = 5) -> List[Message]:
        """Search for semantically similar messages."""
        pass
    
    @abstractmethod
    async def get_recent(self, limit: int = 10) -> List[Message]:
        """Get recent messages."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory."""
        pass


class IEmotionProvider(ABC):
    """Emotional state management interface."""
    
    @abstractmethod
    async def get_state(self) -> EmotionalState:
        """Get current emotional state."""
        pass
    
    @abstractmethod
    async def update_state(self, pleasure_delta: float, arousal_delta: float, 
                          dominance_delta: float, reason: str) -> EmotionalState:
        """Update emotional state."""
        pass
    
    @abstractmethod
    async def get_circadian_phase(self) -> str:
        """Get current circadian phase description."""
        pass


class IInferenceEngine(ABC):
    """LLM inference interface."""
    
    @abstractmethod
    async def generate(self, messages: List[Message], 
                      temperature: float = 0.8,
                      max_tokens: int = 500) -> str:
        """Generate a response."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if inference engine is available."""
        pass


class ISensor(ABC):
    """Sensor interface for environmental awareness."""
    
    @abstractmethod
    def get_context(self) -> str:
        """Get current context as text."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get sensor name."""
        pass


class ICryostasisController(ABC):
    """Resource management interface."""
    
    @abstractmethod
    async def check_should_hibernate(self) -> tuple[bool, str]:
        """Check if system should enter hibernation."""
        pass
    
    @abstractmethod
    async def hibernate(self) -> bool:
        """Unload model from memory."""
        pass
    
    @abstractmethod
    async def wake(self) -> bool:
        """Load model into memory."""
        pass
    
    @abstractmethod
    def is_hibernating(self) -> bool:
        """Check hibernation status."""
        pass


class IHealthCheck(ABC):
    """Health monitoring interface."""
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Run health checks."""
        pass
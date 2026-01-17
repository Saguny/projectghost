"""Mock services for testing."""

from typing import List, Dict, Any
from ghost.core.interfaces import (
    IMemoryProvider,
    IEmotionProvider,
    IInferenceEngine,
    ICryostasisController,
    Message,
    EmotionalState
)


class MockMemoryProvider(IMemoryProvider):
    """Mock memory provider for testing."""
    
    def __init__(self):
        self.messages: List[Message] = []
    
    async def add_message(self, message: Message) -> None:
        self.messages.append(message)
    
    async def search_semantic(self, query: str, limit: int = 5) -> List[Message]:
        return self.messages[:limit]
    
    async def get_recent(self, limit: int = 10) -> List[Message]:
        return self.messages[-limit:]
    
    async def clear(self) -> None:
        self.messages.clear()


class MockEmotionProvider(IEmotionProvider):
    """Mock emotion provider for testing."""
    
    def __init__(self):
        self.state = EmotionalState(pleasure=0.5, arousal=0.5, dominance=0.5)
        # Fix 1: Orchestrator expects pad_model.analyze_sentiment
        self.pad_model = self.MockPADModel()

    class MockPADModel:
        def analyze_sentiment(self, text):
            return (0.1, 0.1, 0.1)
    
    async def get_state(self) -> EmotionalState:
        return self.state
    
    async def update_state(
        self,
        pleasure_delta: float,
        arousal_delta: float,
        dominance_delta: float,
        reason: str
    ) -> EmotionalState:
        self.state.pleasure += pleasure_delta
        self.state.arousal += arousal_delta
        self.state.dominance += dominance_delta
        return self.state
    
    async def get_circadian_phase(self) -> str:
        return "Test Phase"

    # Fix 2: Orchestrator expects this method
    def get_contextual_modifiers(self) -> Dict[str, Any]:
        return {
            "mood_description": "neutral",
            "circadian_phase": "daytime",
            "pleasure": 0.5,
            "arousal": 0.5
        }


class MockInferenceEngine(IInferenceEngine):
    """Mock inference engine for testing."""
    
    def __init__(self, response: str = "Test response"):
        self.response = response
        self.call_count = 0
    
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.8,
        max_tokens: int = 500
    ) -> str:
        self.call_count += 1
        return self.response
    
    async def is_available(self) -> bool:
        return True


class MockCryostasisController(ICryostasisController):
    """Mock cryostasis controller for testing."""
    
    def __init__(self):
        self._hibernating = False
    
    async def check_should_hibernate(self) -> tuple[bool, str]:
        return False, ""
    
    async def hibernate(self) -> bool:
        self._hibernating = True
        return True
    
    async def wake(self) -> bool:
        self._hibernating = False
        return True
    
    def is_hibernating(self) -> bool:
        return self._hibernating

    # Fix 3: Add missing monitoring methods to prevent AttributeError
    async def stop_monitoring(self):
        pass

    async def start_monitoring(self):
        pass
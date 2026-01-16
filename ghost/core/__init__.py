"""Core system components."""

from ghost.core.config import (
    SystemConfig,
    OllamaConfig,
    PersonaConfig,
    CryostasisConfig,
    MemoryConfig,
    AutonomyConfig,
    DiscordConfig,
    load_config,
    validate_config,
)
from ghost.core.events import (
    EventBus,
    Event,
    MessageReceived,
    ResponseGenerated,
    EmotionalStateChanged,
    ProactiveImpulse,
)
from ghost.core.interfaces import (
    Message,
    EmotionalState,
    IMemoryProvider,
    IEmotionProvider,
    IInferenceEngine,
    ISensor,
    ICryostasisController,
)
from ghost.core.orchestrator import Orchestrator

__all__ = [
    # Config
    "SystemConfig",
    "OllamaConfig",
    "PersonaConfig",
    "CryostasisConfig",
    "MemoryConfig",
    "AutonomyConfig",
    "DiscordConfig",
    "load_config",
    "validate_config",
    # Events
    "EventBus",
    "Event",
    "MessageReceived",
    "ResponseGenerated",
    "EmotionalStateChanged",
    "ProactiveImpulse",
    # Interfaces
    "Message",
    "EmotionalState",
    "IMemoryProvider",
    "IEmotionProvider",
    "IInferenceEngine",
    "ISensor",
    "ICryostasisController",
    # Orchestrator
    "Orchestrator",
]
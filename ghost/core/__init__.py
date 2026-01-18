"""Core system components - Central orchestration layer.

This module contains the foundational components that tie the entire system together:
- Configuration loading and validation
- Event bus for inter-service communication
- Core interfaces and data models
- Speech pacing and segmentation
- Event logging and monitoring system

Usage:
    from ghost.core import SystemConfig, EventBus, SpeechGovernor
    from ghost.cognition import CognitiveOrchestrator
"""

from ghost.core.config import (
    SystemConfig,
    OllamaConfig,
    PersonaConfig,
    CryostasisConfig,
    MemoryConfig,
    AutonomyConfig,
    DiscordConfig,
    EmotionConfig,
    load_config,
    validate_config,
)
from ghost.core.events import (
    EventBus,
    Event,
    EventPriority,
    MessageReceived,
    ResponseGenerated,
    EmotionalStateChanged,
    ProactiveImpulse,
    AutonomousMessageSent,
    UserActivityChanged,
    SystemResourceAlert,
    CryostasisActivated,
    CryostasisDeactivated,
)
from ghost.core.interfaces import (
    Message,
    EmotionalState,
    IMemoryProvider,
    IEmotionProvider,
    IInferenceEngine,
    ISensor,
    ICryostasisController,
    IHealthCheck,
)
from ghost.core.speech_governor import SpeechGovernor
from ghost.core.events_listener import (
    SystemEventLogger,
    register_event_listeners
)

__version__ = "1.0.0"

__all__ = [
    # Version
    "__version__",
    
    # Configuration
    "SystemConfig",
    "OllamaConfig",
    "PersonaConfig",
    "CryostasisConfig",
    "MemoryConfig",
    "AutonomyConfig",
    "DiscordConfig",
    "EmotionConfig",
    "load_config",
    "validate_config",
    
    # Event System
    "EventBus",
    "Event",
    "EventPriority",
    "MessageReceived",
    "ResponseGenerated",
    "EmotionalStateChanged",
    "ProactiveImpulse",
    "AutonomousMessageSent",
    "UserActivityChanged",
    "SystemResourceAlert",
    "CryostasisActivated",
    "CryostasisDeactivated",
    
    # Interfaces & Models
    "Message",
    "EmotionalState",
    "IMemoryProvider",
    "IEmotionProvider",
    "IInferenceEngine",
    "ISensor",
    "ICryostasisController",
    "IHealthCheck",

    # Speech
    "SpeechGovernor",

    # Logging & Listeners
    "SystemEventLogger",
    "register_event_listeners",
]


def get_version() -> str:
    """Get the current version of Project Ghost core."""
    return __version__


def create_default_config() -> SystemConfig:
    """Create a default system configuration."""
    return SystemConfig()
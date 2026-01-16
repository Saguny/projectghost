"""Core system components - Central orchestration layer.

This module contains the foundational components that tie the entire system together:
- Configuration loading and validation
- Event bus for inter-service communication
- Core interfaces and data models
- Main orchestrator that coordinates all services

Usage:
    from ghost.core import SystemConfig, EventBus, Orchestrator
    
    config = load_config()
    event_bus = EventBus()
    orchestrator = Orchestrator(config, event_bus, ...)
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
from ghost.core.orchestrator import Orchestrator

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
    
    # Main Orchestrator
    "Orchestrator",
]


def get_version() -> str:
    """Get the current version of Project Ghost core."""
    return __version__


def create_default_config() -> SystemConfig:
    """Create a default system configuration.
    
    Returns:
        SystemConfig with default values
    """
    return SystemConfig()
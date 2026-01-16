"""
Project Ghost - Production-grade autonomous AI companion.

A Discord bot with semantic memory, emotional modeling, resource management,
and autonomous behavior that creates a persistent digital companion.

Vision:
    The end goal is to create a persistent, autonomous digital organism that
    lives on your PC. It is not a tool you use; it is a companion that co-exists
    with you.

Key Features:
    - Agency: Decides when to speak based on mood, boredom, or loneliness
    - Continuity: Persistent memory spanning days and weeks
    - Instinct: Knows when to step back (games) and step in (idle/lonely)

Usage:
    from ghost import SystemConfig, load_config
    
    config = load_config()
    # See main.py for full initialization
"""

__version__ = "1.0.0"
__author__ = "Project Ghost Team"
__license__ = "MIT"

# Core exports
from ghost.core import (
    SystemConfig,
    load_config,
    validate_config,
    EventBus,
    Orchestrator,
)

# Service exports
from ghost.memory import MemoryService
from ghost.emotion import EmotionService
from ghost.inference import InferenceService
from ghost.cryostasis import CryostasisController
from ghost.autonomy import AutonomyEngine
from ghost.integrations import DiscordAdapter

# Utility exports
from ghost.utils import setup_logging

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    
    # Core
    "SystemConfig",
    "load_config",
    "validate_config",
    "EventBus",
    "Orchestrator",
    
    # Services
    "MemoryService",
    "EmotionService",
    "InferenceService",
    "CryostasisController",
    "AutonomyEngine",
    "DiscordAdapter",
    
    # Utilities
    "setup_logging",
]


def get_version() -> str:
    """Get the current version of Project Ghost."""
    return __version__


def get_system_info() -> dict:
    """Get information about the Ghost system.
    
    Returns:
        Dictionary with system information
    """
    return {
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "features": [
            "Semantic Memory",
            "Emotional Modeling (PAD)",
            "Autonomous Initiation",
            "Resource Management (Cryostasis)",
            "Discord Integration",
        ],
        "architecture": "Event-Driven Microservices",
    }


# ASCII art banner for terminal
BANNER = r"""
╔═══════════════════════════════════════════════════════════╗
║                    PROJECT GHOST                          ║
║                                                           ║
║  "A persistent, autonomous digital companion             ║
║   that co-exists with you"                               ║
║                                                           ║
║  Version: 1.0.0                                           ║
╚═══════════════════════════════════════════════════════════╝
"""


def print_banner():
    """Print the Project Ghost banner."""
    print(BANNER)
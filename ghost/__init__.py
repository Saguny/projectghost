"""
Project Ghost - Production-grade autonomous AI companion with cognitive architecture.

A Discord bot with semantic memory, emotional modeling, resource management,
and goal-driven autonomous behavior powered by a bicameral cognitive architecture.

Vision:
    The end goal is to create a persistent, autonomous digital organism that
    lives on your PC. It is not a tool you use; it is a companion that co-exists
    with you. It thinks before it speaks, verifies facts against reality, and
    pursues internal goals through belief-desire-intention autonomy.

Key Features:
    - Bicameral Mind: Separates internal reasoning (think) from external speech
    - Reality Validation: Prevents hallucinations and impossible claims
    - Knowledge Graph: Stores and verifies facts about the world
    - BDI Autonomy: Goal-driven behavior based on internal needs
    - Agency: Decides when to speak based on mood, boredom, or loneliness
    - Continuity: Persistent memory spanning days and weeks
    - Instinct: Knows when to step back (games) and step in (idle/lonely)

Architecture:
    User Input → Cognitive Core (Think → Validate → Speak) → Output
    Background → BDI Engine → Desires → Intentions → Actions → Events

Usage:
    from ghost import SystemConfig, load_config
    from ghost.cognition import CognitiveOrchestrator
    
    config = load_config()
    # See main.py for full initialization
"""

__version__ = "2.0.0"  # Cognitive architecture version
__author__ = "Project Ghost Team"
__license__ = "MIT"

# Core exports
from ghost.core import (
    SystemConfig,
    load_config,
    validate_config,
    EventBus,
)

# Service exports
from ghost.memory import MemoryService
from ghost.emotion import EmotionService
from ghost.inference import InferenceService
from ghost.cryostasis import CryostasisController
from ghost.autonomy import AutonomyEngine
from ghost.integrations import DiscordAdapter

# Cognitive exports (NEW)
from ghost.cognition import CognitiveOrchestrator

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
    
    # Services
    "MemoryService",
    "EmotionService",
    "InferenceService",
    "CryostasisController",
    "AutonomyEngine",
    "DiscordAdapter",
    
    # Cognitive Architecture
    "CognitiveOrchestrator",
    
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
        "architecture": "Cognitive Agent (Bicameral Mind)",
        "features": [
            "Bicameral Cognition (Think/Speak)",
            "Reality Validation",
            "Knowledge Graph",
            "BDI Autonomy",
            "Semantic Memory",
            "Emotional Modeling (PAD)",
            "Resource Management (Cryostasis)",
            "Discord Integration",
        ],
    }


# ASCII art banner for terminal
BANNER = r"""
╔═══════════════════════════════════════════════════════════╗
║                    PROJECT GHOST v2.0                     ║
║                                                           ║
║  "A synthetic mind that thinks before it speaks"         ║
║                                                           ║
║  Architecture: Cognitive Agent                           ║
║  Features: Think/Speak • Validation • Knowledge Graph   ║
╚═══════════════════════════════════════════════════════════╝
"""


def print_banner():
    """Print the Project Ghost banner."""
    print(BANNER)
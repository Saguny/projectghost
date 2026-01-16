"""
Project Ghost - Production-grade autonomous AI companion.

A Discord bot with semantic memory, emotional modeling, and resource management.
"""

__version__ = "1.0.0"
__author__ = "Project Ghost Team"

from ghost.core.config import SystemConfig, load_config
from ghost.core.events import EventBus

__all__ = [
    "SystemConfig",
    "load_config",
    "EventBus",
]
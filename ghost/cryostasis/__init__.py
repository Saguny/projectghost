"""Dynamic resource management (Cryostasis system).

This module implements intelligent resource management that automatically
hibernates the AI when system resources are needed (e.g., when playing games)
and wakes it back up when resources are available.

Key Features:
- GPU/CPU/VRAM monitoring
- Process blacklist detection
- Automatic model unloading
- Configurable thresholds
- Wake cooldown to prevent thrashing

Concept:
The AI instinctively "knows" when to step back (like when you launch a game)
and when to step in (when resources are free), without micromanagement.

Usage:
    from ghost.cryostasis import CryostasisController, ResourceMonitor
    from ghost.core.config import CryostasisConfig
    
    config = CryostasisConfig()
    controller = CryostasisController(config, ollama_client, event_bus)
    
    # Start monitoring
    await controller.start_monitoring()
    
    # Controller will automatically hibernate/wake as needed
"""

from ghost.cryostasis.controller import CryostasisController
from ghost.cryostasis.monitor import ResourceMonitor

__all__ = [
    "CryostasisController",
    "ResourceMonitor",
]


def create_cryostasis_controller(
    config,
    ollama_client,
    event_bus
) -> CryostasisController:
    """Factory function to create a configured cryostasis controller.
    
    Args:
        config: CryostasisConfig with threshold settings
        ollama_client: OllamaClient for model unloading
        event_bus: EventBus for state change notifications
        
    Returns:
        Configured CryostasisController (not started)
    """
    return CryostasisController(config, ollama_client, event_bus)
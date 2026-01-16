"""External service integrations.

This module handles integration with external platforms:
- Discord (primary interface)
- Future: Slack, Telegram, Web API

Key Features:
- Event-driven message handling
- Autonomous message routing
- Channel filtering
- Typing indicators
- Error recovery

Usage:
    from ghost.integrations import DiscordAdapter
    from ghost.core.config import DiscordConfig
    
    config = DiscordConfig()
    adapter = DiscordAdapter(config, event_bus, orchestrator)
    
    # Start bot (blocking)
    await adapter.start(config.token)
"""

from ghost.integrations.discord_adapter import DiscordAdapter

__all__ = [
    "DiscordAdapter",
]


def create_discord_adapter(
    config,
    event_bus,
    orchestrator
) -> DiscordAdapter:
    """Factory function to create a configured Discord adapter.
    
    Args:
        config: DiscordConfig with bot token and settings
        event_bus: EventBus for message events
        orchestrator: Orchestrator for handling messages
        
    Returns:
        Configured DiscordAdapter (not started)
    """
    return DiscordAdapter(config, event_bus, orchestrator)
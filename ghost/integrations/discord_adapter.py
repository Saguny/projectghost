"""Discord integration adapter."""

import discord
import logging
from typing import Optional

from ghost.core.events import EventBus, MessageReceived, ResponseGenerated
from ghost.core.config import DiscordConfig
from ghost.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class DiscordAdapter(discord.Client):
    """Discord bot integration."""
    
    def __init__(
        self,
        config: DiscordConfig,
        event_bus: EventBus,
        orchestrator: Orchestrator
    ):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        self.config = config
        self.event_bus = event_bus
        self.orchestrator = orchestrator
        
        # Subscribe to response events
        self.event_bus.subscribe(ResponseGenerated, self._handle_response_event)
        
        self._pending_channel: Optional[discord.TextChannel] = None
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Discord bot connected as {self.user}")
    
    async def on_message(self, message: discord.Message):
        """Handle incoming Discord message."""
        # Ignore self
        if message.author == self.user:
            return
        
        # Channel filter
        if self.config.allowed_channels:
            if str(message.channel.id) not in self.config.allowed_channels:
                return
        
        # Determine user label
        user_label = message.author.display_name
        if str(message.author.id) == self.config.owner_id:
            user_label += " (Owner)"
        
        logger.info(f"Message from {user_label}: {message.content}")
        
        # Show typing indicator
        async with message.channel.typing():
            # Emit event
            event = MessageReceived(
                user_id=str(message.author.id),
                user_name=user_label,
                content=message.content,
                channel_id=str(message.channel.id)
            )
            
            # Store channel for response
            self._pending_channel = message.channel
            
            # Handle via orchestrator
            response = await self.orchestrator.handle_message(event)
            
            # Send response
            if response:
                await message.channel.send(response)
    
    async def _handle_response_event(self, event: ResponseGenerated):
        """Handle response generated event (for autonomous messages)."""
        # This is called for autonomous initiations
        if not self._pending_channel and self.config.primary_channel_id:
            channel = self.get_channel(int(self.config.primary_channel_id))
            if channel and isinstance(channel, discord.TextChannel):
                await channel.send(event.content)
    
    async def send_to_primary(self, content: str):
        """Send message to primary channel."""
        if self.config.primary_channel_id:
            channel = self.get_channel(int(self.config.primary_channel_id))
            if channel and isinstance(channel, discord.TextChannel):
                await channel.send(content)
                logger.info("Sent autonomous message to primary channel")
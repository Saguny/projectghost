"""Discord integration adapter."""

import discord
import logging
from typing import Optional

from ghost.core.events import (
    EventBus, MessageReceived, ResponseGenerated, AutonomousMessageSent
)
from ghost.core.config import DiscordConfig
from ghost.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class DiscordAdapter(discord.Client):
    """Discord bot integration with autonomous message support."""
    
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
        
        # Subscribe to autonomous message events
        self.event_bus.subscribe(AutonomousMessageSent, self._handle_autonomous_message)
        
        logger.info("Discord adapter initialized")
    
    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"Discord bot connected as {self.user}")
        logger.info(f"Primary channel: {self.config.primary_channel_id}")
    
    async def on_message(self, message: discord.Message):
        """Handle incoming Discord message."""
        # Ignore self
        if message.author == self.user:
            return
        
        # Channel filter
        if self.config.allowed_channels:
            if str(message.channel.id) not in self.config.allowed_channels:
                logger.debug(f"Ignoring message from non-allowed channel: {message.channel.id}")
                return
        
        # Determine user label
        user_label = message.author.display_name
        if str(message.author.id) == self.config.owner_id:
            user_label = message.author.display_name  # Don't add "(Owner)" to content
        
        logger.info(f"Message from {user_label} (ID: {message.author.id}): {message.content}")
        
        # Show typing indicator
        async with message.channel.typing():
            # Emit event
            event = MessageReceived(
                user_id=str(message.author.id),
                user_name=user_label,
                content=message.content,
                channel_id=str(message.channel.id)
            )
            
            # Handle via orchestrator (which will emit ResponseGenerated)
            response = await self.orchestrator.handle_message(event)
            
            # Send response
            if response:
                try:
                    await message.channel.send(response)
                    logger.info(f"Sent response to {user_label}")
                except discord.errors.HTTPException as e:
                    logger.error(f"Failed to send message: {e}")
    
    async def _handle_autonomous_message(self, event: AutonomousMessageSent):
        """Handle autonomous message event - send to primary channel."""
        try:
            # Use specified channel or fall back to primary
            channel_id = event.channel_id or self.config.primary_channel_id
            
            if not channel_id:
                logger.error("No channel specified for autonomous message")
                return
            
            channel = self.get_channel(int(channel_id))
            
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return
            
            if not isinstance(channel, discord.TextChannel):
                logger.error(f"Channel {channel_id} is not a text channel")
                return
            
            # Send autonomous message
            await channel.send(event.content)
            logger.info(f"Sent autonomous message to channel {channel_id}")
            
        except ValueError:
            logger.error(f"Invalid channel ID: {channel_id}")
        except discord.errors.HTTPException as e:
            logger.error(f"Failed to send autonomous message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending autonomous message: {e}", exc_info=True)
    
    async def send_to_primary(self, content: str):
        """Send message to primary channel (legacy support)."""
        if self.config.primary_channel_id:
            try:
                channel = self.get_channel(int(self.config.primary_channel_id))
                if channel and isinstance(channel, discord.TextChannel):
                    await channel.send(content)
                    logger.info("Sent message to primary channel")
            except Exception as e:
                logger.error(f"Failed to send to primary channel: {e}")
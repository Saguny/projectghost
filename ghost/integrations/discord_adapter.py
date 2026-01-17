"""Discord integration adapter."""

import random
import discord
import logging
import asyncio
from typing import Optional

from ghost.core.events import (
    EventBus, MessageReceived, ResponseGenerated, AutonomousMessageSent
)
from ghost.core.config import DiscordConfig
from ghost.core.orchestrator import Orchestrator
from ghost.core.speech_governor import SpeechGovernor

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
        
        # Initialize the Speech Governor (The "Mouth")
        # wpm=280: Fast gamer typing speed
        # min_delay=0.8: Minimum reaction time
        self.governor = SpeechGovernor(wpm=280, min_delay=0.8)
        
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
            user_label = message.author.display_name
        
        logger.info(f"Message from {user_label} (ID: {message.author.id}): {message.content}")
        
        # Emit event
        event = MessageReceived(
            user_id=str(message.author.id),
            user_name=user_label,
            content=message.content,
            channel_id=str(message.channel.id)
        )
        
        # Initial typing indicator for the "Thinking" phase (Inference)
        async with message.channel.typing():
            # Handle via orchestrator
            response = await self.orchestrator.handle_message(event)
            
            # Send response using the Governor
            if response:
                await self._send_natural_message(message.channel, response, user_label)

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
            
            # Send autonomous message naturally
            logger.info(f"Initiating autonomous conversation in {channel_id}")
            await self._send_natural_message(channel, event.content, "Autonomous")
            
        except ValueError:
            logger.error(f"Invalid channel ID: {channel_id}")
        except discord.errors.HTTPException as e:
            logger.error(f"Failed to send autonomous message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending autonomous message: {e}", exc_info=True)

    async def _send_natural_message(self, channel, content: str, log_label: str):
        """
        Uses the Speech Governor to segment and pace the message naturally.
        Handles the specific typing delays and bursting logic.
        """
        try:
            # 1. Segment the thought into natural chat bubbles
            chunks = self.governor.segment_message(content)
            
            # 2. Speak them naturally
            # We use the typing context again to ensure it stays active during the sleeps
            async with channel.typing():
                for i, chunk in enumerate(chunks):
                    # Calculate how long it takes to 'type' this chunk
                    delay = self.governor.calculate_delay(chunk)
                    
                    # Logic: 
                    # If it's the first message, we already waited during inference, 
                    # so we just do a quick "reaction" delay (30% of calc time).
                    # If it's a follow-up message (chunk 2+), we wait the full typing time.
                    if i > 0:
                        await asyncio.sleep(delay)
                    else:
                        await asyncio.sleep(delay * 0.3)
                    
                    await channel.send(chunk)
                    logger.info(f"Sent chunk {i+1}/{len(chunks)} to {log_label}")
                    
                    # Tiny micro-pause between hitting enter and typing next line
                    # This prevents the bot from spamming 3 messages in 100ms
                    if i < len(chunks) - 1:
                        await asyncio.sleep(random.uniform(0.3, 0.6))
                        
        except discord.errors.HTTPException as e:
            logger.error(f"Failed to send message: {e}")

    async def send_to_primary(self, content: str):
        """Send message to primary channel (legacy support)."""
        if self.config.primary_channel_id:
            try:
                channel = self.get_channel(int(self.config.primary_channel_id))
                if channel and isinstance(channel, discord.TextChannel):
                    await self._send_natural_message(channel, content, "Primary(Legacy)")
            except Exception as e:
                logger.error(f"Failed to send to primary channel: {e}")
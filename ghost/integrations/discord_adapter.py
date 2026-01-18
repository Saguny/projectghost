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
from ghost.cognition import CognitiveOrchestrator as Orchestrator
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
        
        # Initialize the Speech Governor
        # wpm=280: Schnelles Tippen (Gamer Speed)
        self.governor = SpeechGovernor(wpm=280, min_delay=0.6)
        
        self.event_bus.subscribe(AutonomousMessageSent, self._handle_autonomous_message)
        
        logger.info("Discord adapter initialized")
    
    async def on_ready(self):
        logger.info(f"Discord bot connected as {self.user}")
        if self.config.primary_channel_id:
            logger.info(f"Primary channel: {self.config.primary_channel_id}")
    
    async def on_message(self, message: discord.Message):
        # Ignore self
        if message.author == self.user:
            return
        
        # Channel Filter
        if self.config.allowed_channels:
            if str(message.channel.id) not in self.config.allowed_channels:
                return
        
        # User Identification
        user_label = message.author.display_name
        if str(message.author.id) == self.config.owner_id:
            user_label = "Sagun" # Force name for Owner if desired
        
        logger.info(f"Message from {user_label}: {message.content}")
        
        event = MessageReceived(
            user_id=str(message.author.id),
            user_name=user_label,
            content=message.content,
            channel_id=str(message.channel.id)
        )
        
        # TYPING INDICATOR (Thinking Phase)
        async with message.channel.typing():
            response = await self.orchestrator.handle_message(event)
            
            if response:
                await self._send_natural_message(message.channel, response, user_label)

    async def _handle_autonomous_message(self, event: AutonomousMessageSent):
        """Handle autonomous messages (triggered by boredom/events)."""
        try:
            channel_id = event.channel_id or self.config.primary_channel_id
            if not channel_id:
                return
            
            channel = self.get_channel(int(channel_id))
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return
            
            logger.info(f"Initiating autonomous conversation in {channel_id}")
            # Auch bei autonomen Nachrichten nutzen wir den Governor für natürliches Tippen
            await self._send_natural_message(channel, event.content, "Autonomous")
            
        except Exception as e:
            logger.error(f"Error sending autonomous message: {e}")

    async def _send_natural_message(self, channel, content: str, log_label: str):
        """
        Splits message using Governor (handling <SPLIT>) and simulates typing.
        """
        try:
            # 1. Split Logic (Hier wird der <SPLIT> Token verarbeitet!)
            chunks = self.governor.segment_message(content)
            
            # 2. Send Loop
            async with channel.typing():
                for i, chunk in enumerate(chunks):
                    # Berechne wie lange das Tippen dieses Teils dauert
                    delay = self.governor.calculate_delay(chunk)
                    
                    # LOGIK:
                    # Chunk 0 (Erste Nachricht): Wir haben schon während der Berechnung gewartet.
                    # Daher nur kurzer "Reaction Delay" (30%).
                    # Chunk 1+ (Follow-up): Wir müssen die volle Zeit warten, als würden wir tippen.
                    wait_time = delay if i > 0 else (delay * 0.3)
                    
                    if i > 0:
                        logger.info(f"Typing follow-up... ({wait_time:.2f}s)")
                        
                    await asyncio.sleep(wait_time)
                    await channel.send(chunk)
                    logger.info(f"Sent chunk {i+1}/{len(chunks)} to {log_label}")
                    
                    # Mini-Pause zwischen "Enter drücken" und "Nächsten Satz tippen"
                    if i < len(chunks) - 1:
                        await asyncio.sleep(random.uniform(0.2, 0.5))
                        
        except Exception as e:
            logger.error(f"Failed to send natural message: {e}")
"""Main entry point for Project Ghost."""

import asyncio
import logging
from logging import config
import sys
from pathlib import Path

from networkx import config

from ghost import emotion

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ghost.core.config import load_config, validate_config
from ghost.core.events import EventBus
from ghost.core.orchestrator import Orchestrator
from ghost.memory.memory_service import MemoryService
from ghost.emotion.emotion_service import EmotionService
from ghost.inference.inference_service import InferenceService
from ghost.inference.ollama_client import OllamaClient
from ghost.cryostasis.controller import CryostasisController
from ghost.integrations.discord_adapter import DiscordAdapter
from ghost.sensors.hardware_sensor import HardwareSensor
from ghost.sensors.time_sensor import TimeSensor
from ghost.utils.logging_config import setup_logging
from ghost.autonomy.autonomy_engine import AutonomyEngine

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config.debug_mode, config.log_level)
    
    # Validate configuration
    errors = validate_config(config)
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Project Ghost Initializing")
    logger.info("=" * 60)
    
    try:
        # Initialize event bus
        event_bus = EventBus()
        await event_bus.start()
        
        # Initialize core services
        memory = MemoryService(config.memory)
        emotion = EmotionService(config.persona, event_bus)
        
        ollama_client = OllamaClient(config.ollama)
        inference = InferenceService(config.ollama, config.persona)
        autonomy_engine = AutonomyEngine(config.autonomy, event_bus, emotion)
        await autonomy_engine.start()

        cryostasis = CryostasisController(
            config.cryostasis,
            ollama_client,
            event_bus
        )
        
        # Initialize sensors
        sensors = [
            HardwareSensor(config.cryostasis),
            TimeSensor()
        ]
        
        # Initialize orchestrator
        orchestrator = Orchestrator(
            config=config,
            event_bus=event_bus,
            memory=memory,
            emotion=emotion,
            inference=inference,
            cryostasis=cryostasis,
            sensors=sensors
        )
        
        # Initialize Discord
        discord_adapter = DiscordAdapter(
            config.discord,
            event_bus,
            orchestrator
        )
        
        # Health check
        logger.info("Performing health check...")
        health = await orchestrator.health_check()
        logger.info(f"Health check: {health}")
        
        if not health['inference_available']:
            logger.warning("Ollama not available! Bot will have limited functionality.")
        
        # Start cryostasis monitoring
        await cryostasis.start_monitoring()
        
        # Start Discord bot
        logger.info("=" * 60)
        logger.info("System Ready - Starting Discord Bot")
        logger.info("=" * 60)
        
        await discord_adapter.start(config.discord.token)
        
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Shutting down...")
        await event_bus.stop()
        await autonomy_engine.stop()
        if cryostasis:
            await cryostasis.stop_monitoring()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
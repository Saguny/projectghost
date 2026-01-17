import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ghost.core.config import load_config, validate_config
from ghost.core.events import EventBus
from ghost.memory.memory_service import MemoryService
from ghost.emotion.emotion_service import EmotionService
from ghost.inference.ollama_client import OllamaClient
from ghost.cryostasis.controller import CryostasisController
from ghost.integrations.discord_adapter import DiscordAdapter
from ghost.sensors.hardware_sensor import HardwareSensor
from ghost.sensors.time_sensor import TimeSensor
from ghost.utils.logging_config import setup_logging
from ghost.utils.validation import validate_discord_token, ValidationError
from ghost.core.events_listener import register_event_listeners

from ghost.cognition.cognitive_orchestrator import CognitiveOrchestrator

logger = logging.getLogger(__name__)


def print_cognitive_banner():
    banner = """
╔═══════════════════════════════════════════════════════════╗
║              PROJECT GHOST: COGNITIVE AGENT               ║
║                                                           ║
║  Architecture:                                            ║
║    • Bicameral Mind (Think/Speak)                        ║
║    • Reality Validator (Hallucination prevention)        ║
║    • Knowledge Graph (Fact verification)                 ║
║    • BDI Autonomy (Goal-driven behavior)                 ║
║                                                           ║
║  "A synthetic mind that thinks before it speaks"         ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


async def main():
    print_cognitive_banner()
    
    config = load_config()
    setup_logging(config.debug_mode, config.log_level)
    
    errors = validate_config(config)
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    try:
        if not validate_discord_token(config.discord.token):
            logger.error("Invalid Discord token format")
            sys.exit(1)
    except ValidationError as e:
        logger.error(f"Token validation failed: {e}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Cognitive Architecture Initialization")
    logger.info("=" * 60)
    
    event_bus = None
    cryostasis = None
    discord_adapter = None
    cognitive_orchestrator = None
    
    try:
        event_bus = EventBus(max_queue_size=1000)
        await event_bus.start()
        logger.info("✓ Event bus started")
        
        register_event_listeners(event_bus)
        logger.info("✓ Event handlers registered")
        
        memory = MemoryService(config.memory)
        logger.info("✓ Memory service initialized")
        
        emotion = EmotionService(config.persona, event_bus)
        logger.info("✓ Emotion service initialized")
        
        ollama_client = OllamaClient(config.ollama)
        logger.info("✓ Ollama client initialized")
        
        cryostasis = CryostasisController(
            config.cryostasis,
            ollama_client,
            event_bus
        )
        logger.info("✓ Cryostasis controller initialized")
        
        sensors = [
            HardwareSensor(config.cryostasis),
            TimeSensor()
        ]
        logger.info("✓ Sensors initialized")
        
        cognitive_orchestrator = CognitiveOrchestrator(
            config=config,
            event_bus=event_bus,
            memory=memory,
            emotion=emotion,
            ollama_client=ollama_client,
            cryostasis=cryostasis,
            sensors=sensors
        )
        logger.info("✓ Cognitive orchestrator initialized")
        
        await cognitive_orchestrator.bdi_engine.start()
        logger.info("✓ BDI engine started")
        
        discord_adapter = DiscordAdapter(
            config.discord,
            event_bus,
            cognitive_orchestrator
        )
        logger.info("✓ Discord adapter initialized")
        
        logger.info("=" * 60)
        logger.info("Performing health check...")
        health = await cognitive_orchestrator.health_check()
        logger.info(f"Health: {health}")
        
        ollama_available = await ollama_client.health_check()
        if not ollama_available:
            logger.warning("⚠ Ollama not available - limited functionality")
            logger.warning("  Start Ollama: ollama serve")
        else:
            logger.info("✓ Ollama available")
        
        belief_summary = await cognitive_orchestrator.belief_system.get_summary()
        logger.info(f"\n{belief_summary}")
        
        await cryostasis.start_monitoring()
        logger.info("✓ Cryostasis monitoring started")
        
        logger.info("=" * 60)
        logger.info("COGNITIVE AGENT READY")
        logger.info("=" * 60)
        logger.info("Starting Discord bot...")
        
        await discord_adapter.start(config.discord.token)
        
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Shutting down cognitive agent...")
        
        if cognitive_orchestrator and hasattr(cognitive_orchestrator, 'bdi_engine'):
            await cognitive_orchestrator.bdi_engine.stop()
        
        if discord_adapter and discord_adapter.is_ready():
            await discord_adapter.close()
        
        if cryostasis:
            await cryostasis.stop_monitoring()
        
        if event_bus:
            await event_bus.stop()
        
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCognitive agent terminated.")
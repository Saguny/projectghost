"""
Main entry point: Cognitive Agent Architecture

Replaces: main.py (chatbot bootstrap)

Architecture:
    - Cognitive Core (Think/Speak)
    - Validator (Reality firewall)
    - Belief System (Knowledge graph)
    - BDI Engine (Autonomy)
    - Cognitive Orchestrator (Integration)
    
Bootstrap Order:
    1. Config & Logging
    2. Event Bus
    3. Memory & Emotion (existing)
    4. Ollama Client
    5. Belief System (NEW)
    6. Cognitive Core (NEW)
    7. Validator (NEW)
    8. BDI Engine (NEW)
    9. Cognitive Orchestrator (NEW)
    10. Discord Adapter
"""

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

# NEW: Cognitive components
from ghost.cognition.cognitive_orchestrator import CognitiveOrchestrator

logger = logging.getLogger(__name__)


def print_cognitive_banner():
    """Print startup banner"""
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
    """Main entry point: Cognitive agent bootstrap"""
    
    print_cognitive_banner()
    
    # Load configuration
    config = load_config()
    setup_logging(config.debug_mode, config.log_level)
    
    # Validate configuration
    errors = validate_config(config)
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    # Validate Discord token
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
    bdi_engine = None
    cryostasis = None
    discord_adapter = None
    
    try:
        # Initialize event bus
        event_bus = EventBus(max_queue_size=1000)
        await event_bus.start()
        logger.info("✓ Event bus started")
        
        # Initialize memory
        memory = MemoryService(config.memory)
        logger.info("✓ Memory service initialized")
        
        # Initialize emotion
        emotion = EmotionService(config.persona, event_bus)
        logger.info("✓ Emotion service initialized")
        
        # Initialize Ollama client
        ollama_client = OllamaClient(config.ollama)
        logger.info("✓ Ollama client initialized")
        
        # Initialize cryostasis
        cryostasis = CryostasisController(
            config.cryostasis,
            ollama_client,
            event_bus
        )
        logger.info("✓ Cryostasis controller initialized")
        
        # Initialize sensors
        sensors = [
            HardwareSensor(config.cryostasis),
            TimeSensor()
        ]
        logger.info("✓ Sensors initialized")
        
        # === COGNITIVE ARCHITECTURE ===
        
        # Initialize cognitive orchestrator (includes all cognitive components)
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
        
        # Start BDI engine
        await cognitive_orchestrator.bdi_engine.start()
        logger.info("✓ BDI engine started")
        
        # Initialize Discord adapter
        discord_adapter = DiscordAdapter(
            config.discord,
            event_bus,
            cognitive_orchestrator  # Uses new orchestrator
        )
        logger.info("✓ Discord adapter initialized")
        
        # Health check
        logger.info("=" * 60)
        logger.info("Performing health check...")
        health = await cognitive_orchestrator.health_check()
        logger.info(f"Health: {health}")
        
        # Check Ollama availability
        ollama_available = await ollama_client.health_check()
        if not ollama_available:
            logger.warning("⚠ Ollama not available - limited functionality")
            logger.warning("  Start Ollama: ollama serve")
        else:
            logger.info("✓ Ollama available")
        
        # Display belief system summary
        belief_summary = await cognitive_orchestrator.belief_system.get_summary()
        logger.info(f"\n{belief_summary}")
        
        # Start cryostasis monitoring
        await cryostasis.start_monitoring()
        logger.info("✓ Cryostasis monitoring started")
        
        # Start Discord bot
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
        
        # Graceful shutdown
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
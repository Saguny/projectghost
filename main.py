"""
Main entry point: Cognitive Agent Architecture

Architecture:
    - Cognitive Core (Think/Speak)
    - Validator (Reality firewall)
    - Belief System (Knowledge graph)
    - BDI Engine (Autonomy)
    - Cognitive Orchestrator (Integration)
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ghost.core.config import load_config, validate_config
from ghost.core.events import EventBus
from ghost.core.events_listener import register_event_listeners

from ghost.memory.memory_service import MemoryService
from ghost.emotion.emotion_service import EmotionService
from ghost.inference.ollama_client import OllamaClient
from ghost.cryostasis.controller import CryostasisController
from ghost.integrations.discord_adapter import DiscordAdapter
from ghost.sensors.hardware_sensor import HardwareSensor
from ghost.sensors.time_sensor import TimeSensor
from ghost.utils.logging_config import setup_logging
from ghost.utils.validation import validate_discord_token, ValidationError

# Cognitive components
from ghost.cognition.cognitive_orchestrator import CognitiveOrchestrator

logger = logging.getLogger(__name__)


def print_cognitive_banner():
    """Print startup banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║              PROJECT GHOST: COGNITIVE AGENT               ║
║                                                           ║
║  Architecture:                                            ║
║    • Bicameral Mind (Think/Speak)                         ║
║    • Reality Validator (Hallucination prevention)         ║
║    • Knowledge Graph (Fact verification)                  ║
║    • BDI Autonomy (Goal-driven behavior)                  ║
║                                                           ║
║  "A synthetic mind that thinks before it speaks"          ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


async def main():
    """Main entry point: Cognitive agent bootstrap"""
    
    print_cognitive_banner()
    
    # 1. Load configuration
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
    
    # Context managers for graceful shutdown
    event_bus = None
    cryostasis = None
    discord_adapter = None
    cognitive_orchestrator = None
    
    try:
        # 2. Initialize Event Bus & Listeners
        event_bus = EventBus(max_queue_size=1000)
        
        # Register listeners BEFORE starting components
        register_event_listeners(event_bus)
        logger.info("✓ Event listeners registered")
        
        await event_bus.start()
        logger.info("✓ Event bus started")
        
        # 3. Initialize Services
        memory = MemoryService(config.memory)
        logger.info("✓ Memory service initialized")
        
        emotion = EmotionService(config.persona, event_bus)
        logger.info("✓ Emotion service initialized")
        
        # Initialize Ollama client (using config object)
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
        
        # 4. Initialize Cognitive Architecture
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
        
        # Hydrate Beliefs + BDI
        await cognitive_orchestrator.start()
        logger.info("✓ Cognitive Engine started (Beliefs Hydrated + BDI Active)")
        
        # 5. Initialize Discord Adapter
        discord_adapter = DiscordAdapter(
            config=config.discord,
            event_bus=event_bus,
            orchestrator=cognitive_orchestrator
        )
        logger.info("✓ Discord adapter initialized")
        
        # 6. Post-Startup Checks
        logger.info("=" * 60)
        logger.info("Performing health check...")
        health = await cognitive_orchestrator.health_check()
        logger.info(f"Health: {health}")
        
        # Check Ollama availability
        if not await ollama_client.health_check():
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
        
        # 7. Start Discord Bot (Blocking Call)
        logger.info("=" * 60)
        logger.info("COGNITIVE AGENT READY")
        logger.info("=" * 60)
        logger.info("Starting Discord bot...")
        
        # Setup graceful shutdown logic
        async def shutdown(sig=None):
            if sig:
                logger.info(f"Received signal {sig.name}")
            else:
                logger.info("Received shutdown signal")
                
            logger.info("Shutting down cognitive agent...")
            
            if cognitive_orchestrator:
                await cognitive_orchestrator.stop()
            
            if discord_adapter and discord_adapter.is_ready():
                await discord_adapter.close()
            
            if cryostasis:
                await cryostasis.stop_monitoring()
            
            if event_bus:
                await event_bus.stop()
                
            logger.info("Shutdown complete")
            sys.exit(0)
            
        # FIX: Only add signal handlers on Unix-like systems
        if sys.platform != 'win32':
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

        await discord_adapter.start(config.discord.token)
        
    except KeyboardInterrupt:
        # FIX: Explicit shutdown call for Windows Ctrl+C
        logger.info("Shutdown signal received (KeyboardInterrupt)")
        # We need to run shutdown, but we can't await inside this except block easily 
        # if the loop is closing. However, discord_adapter.start() is awaited, 
        # so when it raises KeyboardInterrupt, we are still inside main().
        # We will let the finally block handle cleanup or call shutdown here.
        # Calling shutdown() directly which invokes sys.exit(0) is cleanest.
        # But since shutdown is async, we create a task if loop is running.
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                await shutdown()
        except RuntimeError:
            pass # Loop already closed
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
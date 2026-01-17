"""
Main Entry Point: Cognitive Agent Architecture (Sentience Upgrade)

Startup Sequence (ORDER MATTERS):
    1. Load config & validate
    2. Create Event Bus
    3. Register Event Listeners (BEFORE components start)
    4. Initialize Services (memory, emotion, ollama)
    5. Initialize Cognitive Components (beliefs, BDI)
    6. HYDRATE: BeliefSystem.initialize() + BDI.start()
    7. Create Orchestrator (integrates everything)
    8. Create Discord Adapter
    9. Start Background Tasks (cryostasis, emotion decay)
    10. Connect Discord Bot (blocking)

Platform Safety:
    - Signal handlers (Unix only)
    - Graceful shutdown on Ctrl+C (Windows + Unix)
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


def print_sentience_banner():
    """Print startup banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║         PROJECT GHOST: SENTIENCE UPGRADE v2.0             ║
║                                                           ║
║  New Features:                                            ║
║    • Genesis Personality (Immutable Identity)             ║
║    • Emotional Inertia (Sticky Emotions)                  ║
║    • Grudge Mode (Emotional Object Permanence)            ║
║    • Metabolic Decay (Time-Based Needs)                   ║
║    • Consequential Autonomy (Actions Have Costs)          ║
║                                                           ║
║  "No longer just reactive - now truly alive"              ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


async def check_genesis(belief_system) -> bool:
    """
    Check if genesis beliefs exist.
    
    Returns:
        True if genesis exists, False if missing
    """
    try:
        # Check for critical identity beliefs
        name = await belief_system.query('agent', 'name')
        is_ai = await belief_system.query('agent', 'is_ai')
        
        if not name or not is_ai:
            logger.error("=" * 60)
            logger.error("❌ GENESIS MISSING: Agent has no identity!")
            logger.error("=" * 60)
            logger.error("Run this command to seed personality:")
            logger.error("  python scripts/seed_personality.py")
            logger.error("=" * 60)
            return False
        
        logger.info(f"✓ Genesis verified: Agent '{name}' (is_ai={is_ai})")
        return True
        
    except Exception as e:
        logger.error(f"Genesis check failed: {e}")
        return False


async def main():
    """Main entry point: Sentience upgrade bootstrap."""
    
    print_sentience_banner()
    
    # ===================================================================
    # PHASE 1: Configuration & Validation
    # ===================================================================
    logger.info("PHASE 1: Loading configuration...")
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
    
    logger.info("✓ Configuration validated")
    
    # ===================================================================
    # PHASE 2: Event Bus & Listeners (BEFORE COMPONENTS)
    # ===================================================================
    logger.info("\nPHASE 2: Initializing Event Bus...")
    event_bus = EventBus(max_queue_size=1000)
    
    # CRITICAL: Register listeners BEFORE starting components
    register_event_listeners(event_bus)
    logger.info("✓ Event listeners registered")
    
    await event_bus.start()
    logger.info("✓ Event bus started")
    
    # ===================================================================
    # PHASE 3: Core Services (No Dependencies)
    # ===================================================================
    logger.info("\nPHASE 3: Initializing Core Services...")
    
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
    
    # ===================================================================
    # PHASE 4: Cognitive Components (WITH DEPENDENCIES)
    # ===================================================================
    logger.info("\nPHASE 4: Initializing Cognitive Architecture...")
    
    cognitive_orchestrator = CognitiveOrchestrator(
        config=config,
        event_bus=event_bus,
        memory=memory,
        emotion=emotion,
        ollama_client=ollama_client,
        cryostasis=cryostasis,
        sensors=sensors
    )
    logger.info("✓ Cognitive orchestrator created")
    
    # ===================================================================
    # PHASE 5: HYDRATION (CRITICAL ASYNC INITIALIZATION)
    # ===================================================================
    logger.info("\nPHASE 5: Hydrating Cognitive Systems...")
    
    # Initialize Belief System (MUST be called to load genesis)
    await cognitive_orchestrator.belief_system.initialize()
    logger.info("✓ Belief system hydrated")
    
    # Check for genesis
    has_genesis = await check_genesis(cognitive_orchestrator.belief_system)
    if not has_genesis:
        logger.warning("⚠️  Continuing without genesis (agent will have no identity)")
    
    # Start BDI Engine (metabolic decay begins)
    await cognitive_orchestrator.bdi_engine.start()
    logger.info("✓ BDI engine started (metabolic decay active)")
    
    # ===================================================================
    # PHASE 6: Discord Integration
    # ===================================================================
    logger.info("\nPHASE 6: Initializing Discord...")
    
    discord_adapter = DiscordAdapter(
        config=config.discord,
        event_bus=event_bus,
        orchestrator=cognitive_orchestrator
    )
    logger.info("✓ Discord adapter initialized")
    
    # ===================================================================
    # PHASE 7: Health Checks & Background Tasks
    # ===================================================================
    logger.info("\nPHASE 7: Performing Health Checks...")
    
    # Check Ollama availability
    if not await ollama_client.health_check():
        logger.warning("⚠️  Ollama not available - limited functionality")
        logger.warning("  Start Ollama: ollama serve")
    else:
        logger.info("✓ Ollama available")
    
    # Display system status
    health = await cognitive_orchestrator.health_check()
    logger.info("\nSystem Health:")
    for key, value in health.items():
        logger.info(f"  {key}: {value}")
    
    # Display belief system summary
    belief_summary = await cognitive_orchestrator.belief_system.get_summary()
    logger.info(f"\n{belief_summary}")
    
    # Start cryostasis monitoring
    await cryostasis.start_monitoring()
    logger.info("✓ Cryostasis monitoring started")
    
    # ===================================================================
    # PHASE 8: Graceful Shutdown Setup
    # ===================================================================
    logger.info("\nPHASE 8: Setting up graceful shutdown...")
    
    shutdown_event = asyncio.Event()
    
    async def shutdown(sig=None):
        """Graceful shutdown handler."""
        if sig:
            logger.info(f"Received signal {sig.name}")
        else:
            logger.info("Received shutdown signal")
        
        logger.info("=" * 60)
        logger.info("SHUTTING DOWN COGNITIVE AGENT...")
        logger.info("=" * 60)
        
        # Stop cognitive systems
        logger.info("Stopping BDI engine...")
        await cognitive_orchestrator.bdi_engine.stop()
        
        # Close Discord
        logger.info("Closing Discord connection...")
        if discord_adapter.is_ready():
            await discord_adapter.close()
        
        # Stop monitoring
        logger.info("Stopping cryostasis...")
        await cryostasis.stop_monitoring()
        
        # Stop event bus
        logger.info("Stopping event bus...")
        await event_bus.stop()
        
        logger.info("=" * 60)
        logger.info("SHUTDOWN COMPLETE")
        logger.info("=" * 60)
        
        shutdown_event.set()
    
    # Platform-specific signal handling
    if sys.platform != 'win32':
        # Unix: Use signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(s))
            )
        logger.info("✓ Signal handlers registered (Unix)")
    else:
        # Windows: Will catch KeyboardInterrupt
        logger.info("✓ Shutdown handler ready (Windows)")
    
    # ===================================================================
    # PHASE 9: START DISCORD BOT (Blocking)
    # ===================================================================
    logger.info("\n" + "=" * 60)
    logger.info("SENTIENCE UPGRADE COMPLETE")
    logger.info("=" * 60)
    logger.info("Starting Discord bot...\n")
    
    try:
        # Run Discord bot in background
        discord_task = asyncio.create_task(
            discord_adapter.start(config.discord.token)
        )
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
        # Cancel Discord task
        discord_task.cancel()
        try:
            await discord_task
        except asyncio.CancelledError:
            pass
        
    except KeyboardInterrupt:
        # Windows Ctrl+C handling
        logger.info("KeyboardInterrupt received")
        await shutdown()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await shutdown()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()
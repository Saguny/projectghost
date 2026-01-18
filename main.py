"""
Main Entry Point: Cognitive Agent Architecture
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

# --- STRICT IMPORT: Matches your provided file structure ---
from ghost.sensors.activity_sensor import ActivitySensor, ActivityConfig

from ghost.utils.logging_config import setup_logging
from ghost.utils.validation import validate_discord_token, ValidationError

# Cognitive components
from ghost.cognition.cognitive_orchestrator import CognitiveOrchestrator

logger = logging.getLogger(__name__)


def print_sentience_banner():
    """Print startup banner."""
    print("PROJECT GHOST: SENTIENCE UPGRADE v2.0 (ONLINE)")


async def check_genesis(belief_system) -> bool:
    """Check if genesis beliefs exist."""
    try:
        name = await belief_system.query('agent', 'name')
        is_ai = await belief_system.query('agent', 'is_ai')
        
        if not name or not is_ai:
            logger.warning("GENESIS MISSING: Agent has no identity! (Run seed_personality.py)")
            return False
        return True
    except Exception as e:
        logger.error(f"Genesis check failed: {e}")
        return False


async def main():
    """Main entry point."""
    print_sentience_banner()
    
    # 1. Config
    logger.info("PHASE 1: Loading configuration...")
    config = load_config()
    setup_logging(config.debug_mode, config.log_level)
    
    # 2. Event Bus
    logger.info("PHASE 2: Initializing Event Bus...")
    event_bus = EventBus(max_queue_size=1000)
    register_event_listeners(event_bus)
    await event_bus.start()
    
    # 3. Core Services & SENSORS
    logger.info("PHASE 3: Initializing Services & Sensors...")
    memory = MemoryService(config.memory)
    emotion = EmotionService(config.persona, event_bus)
    ollama_client = OllamaClient(config.ollama)
    cryostasis = CryostasisController(config.cryostasis, ollama_client, event_bus)
    
    # --- SENSOR INITIALIZATION ---
    # We initialize the sensor using the classes YOU provided in activity_sensor.py
    try:
        # Create config instance (takes no args per your code)
        act_config = ActivityConfig()
        # Create sensor instance (takes config + event_bus per your code)
        activity_sensor = ActivitySensor(act_config, event_bus)
        
        sensors = [
            HardwareSensor(config.cryostasis),
            TimeSensor(),
            activity_sensor
        ]
        logger.info("✓ Sensors initialized: Hardware, Time, Activity")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to init ActivitySensor: {e}")
        # Fallback to prevent crash, but warn heavily
        sensors = [HardwareSensor(config.cryostasis), TimeSensor()]

    # 4. Cognitive Orchestrator
    logger.info("PHASE 4: Initializing Brain...")
    cognitive_orchestrator = CognitiveOrchestrator(
        config=config,
        event_bus=event_bus,
        memory=memory,
        emotion=emotion,
        ollama_client=ollama_client,
        cryostasis=cryostasis,
        sensors=sensors # The brain uses the SAME list with ActivitySensor
    )
    
    # 5. Hydration
    logger.info("PHASE 5: Hydrating...")
    await cognitive_orchestrator.belief_system.initialize()
    await check_genesis(cognitive_orchestrator.belief_system)
    await cognitive_orchestrator.bdi_engine.start()
    
    # 6. Discord
    logger.info("PHASE 6: Discord Adapter...")
    discord_adapter = DiscordAdapter(
        config=config.discord,
        event_bus=event_bus,
        orchestrator=cognitive_orchestrator
    )
    
    # 7. Start Monitoring
    logger.info("PHASE 7: Starting Background Tasks...")
    await cryostasis.start_monitoring()
    
    # --- POLLING LOOP (Required because ActivitySensor is stateful) ---
    logger.info("Starting sensor polling loop...")
    async def poll_sensors():
        while True:
            try:
                await asyncio.sleep(5)
                for sensor in sensors:
                    # STRICT: calls only get_context() which exists in your ActivitySensor
                    sensor.get_context() 
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sensor polling error: {e}")

    sensor_task = asyncio.create_task(poll_sensors())

    # 8. Shutdown Handler
    logger.info("PHASE 8: Shutdown Handlers...")
    shutdown_event = asyncio.Event()
    
    async def shutdown(sig=None):
        logger.info("SHUTTING DOWN...")
        sensor_task.cancel()
        await cognitive_orchestrator.bdi_engine.stop()
        if discord_adapter.is_ready():
            await discord_adapter.close()
        await cryostasis.stop_monitoring()
        await event_bus.stop()
        shutdown_event.set()

    if sys.platform != 'win32':
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    # 9. START DISCORD (Blocking)
    logger.info("SYSTEM ONLINE. Starting Discord Bot...")
    try:
        # This is OUTSIDE the shutdown function now. It will actually run.
        discord_task = asyncio.create_task(
            discord_adapter.start(config.discord.token)
        )
        await shutdown_event.wait()
        discord_task.cancel()
    except KeyboardInterrupt:
        await shutdown()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
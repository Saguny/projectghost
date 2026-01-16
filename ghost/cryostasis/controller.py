"""Cryostasis controller for dynamic resource management."""

import logging
import asyncio
from datetime import datetime, timedelta

from ghost.core.interfaces import ICryostasisController
from ghost.cryostasis.monitor import ResourceMonitor
from ghost.inference.ollama_client import OllamaClient
from ghost.core.config import CryostasisConfig
from ghost.core.events import EventBus, CryostasisActivated, CryostasisDeactivated

logger = logging.getLogger(__name__)


class CryostasisController(ICryostasisController):
    """Manages model loading/unloading based on system resources."""
    
    def __init__(
        self,
        config: CryostasisConfig,
        ollama_client: OllamaClient,
        event_bus: EventBus
    ):
        self.config = config
        self.ollama_client = ollama_client
        self.event_bus = event_bus
        self.monitor = ResourceMonitor(config)
        
        self._hibernating = False
        self._last_wake_time = None
        self._monitoring_task = None
        
        logger.info("Cryostasis controller initialized")
    
    async def start_monitoring(self):
        """Start resource monitoring loop."""
        if not self.config.enabled:
            logger.info("Cryostasis disabled in config")
            return
        
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Cryostasis monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Continuous monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.config.poll_interval_seconds)
                
                should_hibernate, reason = await self.check_should_hibernate()
                
                if should_hibernate and not self._hibernating:
                    await self.hibernate()
                elif not should_hibernate and self._hibernating:
                    await self.wake()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}", exc_info=True)
    
    async def check_should_hibernate(self) -> tuple[bool, str]:
        """Determine if system should enter hibernation."""
        if not self.config.enabled:
            return False, ""
        
        # Check blacklisted processes
        blacklist_running = self.monitor.check_blacklist()
        if blacklist_running:
            return True, f"Blacklisted process: {blacklist_running}"
        
        # Check GPU utilization
        gpu_util, vram_used = self.monitor.get_gpu_stats()
        if gpu_util > self.config.gpu_threshold_percent:
            return True, f"High GPU utilization: {gpu_util}%"
        
        if vram_used > self.config.vram_threshold_mb:
            return True, f"High VRAM usage: {vram_used}MB"
        
        # Check CPU utilization
        cpu_util = self.monitor.get_cpu_stats()
        if cpu_util > self.config.cpu_threshold_percent:
            return True, f"High CPU utilization: {cpu_util}%"
        
        return False, ""
    
    async def hibernate(self) -> bool:
        """Enter hibernation (unload model)."""
        if self._hibernating:
            return True
        
        logger.warning("Entering cryostasis (hibernation)")
        
        start_time = datetime.now()
        success = await self.ollama_client.unload_model()
        
        if success:
            self._hibernating = True
            
            # Emit event
            await self.event_bus.publish(CryostasisActivated(
                reason="Resource threshold exceeded",
                memory_freed_mb=0.0  # Could calculate actual freed memory
            ))
            
            logger.info("Cryostasis activated")
            return True
        else:
            logger.error("Failed to enter hibernation")
            return False
    
    async def wake(self) -> bool:
        """Exit hibernation (model will load on next inference)."""
        if not self._hibernating:
            return True
        
        # Cooldown to prevent rapid wake/sleep cycles
        if self._last_wake_time:
            time_since_wake = datetime.now() - self._last_wake_time
            if time_since_wake < timedelta(seconds=30):
                logger.debug("Wake cooldown active")
                return False
        
        logger.info("Exiting cryostasis (waking up)")
        
        start_time = datetime.now()
        self._hibernating = False
        self._last_wake_time = datetime.now()
        
        # Emit event
        load_time = (datetime.now() - start_time).total_seconds() * 1000
        await self.event_bus.publish(CryostasisDeactivated(
            load_time_ms=load_time
        ))
        
        logger.info("Cryostasis deactivated")
        return True
    
    def is_hibernating(self) -> bool:
        """Check if currently in hibernation."""
        return self._hibernating
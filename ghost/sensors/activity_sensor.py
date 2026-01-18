"""
Activity Sensor: Monitors running processes and detects activity changes.

Features:
- Tracks current user activity (Idle, Gaming, Coding, etc.)
- Detects state changes and fires events
- Windows-safe (case-insensitive matching)
- Configurable app categories
"""

import logging
import psutil
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from ghost.core.interfaces import ISensor
from ghost.core.events import EventBus

logger = logging.getLogger(__name__)


class UserActivityEvent:
    """Event fired when user activity changes."""
    def __init__(
        self,
        old_activity: str,
        new_activity: str,
        app_name: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.old_activity = old_activity
        self.new_activity = new_activity
        self.app_name = app_name
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    def is_significant(self) -> bool:
        """Check if this is a significant activity change worth reacting to."""
        # Starting a game or major app is significant
        if self.old_activity == "Idle" and self.new_activity in ["Gaming", "Streaming"]:
            return True
        # Switching from gaming to coding is significant
        if self.old_activity == "Gaming" and self.new_activity == "Coding":
            return True
        return False


class ActivityConfig:
    """Configuration for activity detection."""
    def __init__(self):
        # Gaming apps (case-insensitive)
        self.gaming_apps = [
            "rocketleague.exe",
            "steam.exe",
            "epicgameslauncher.exe",
            "league of legends.exe",
            "valorant.exe",
            "cs2.exe",
            "minecraft.exe"
        ]
        
        # Coding apps
        self.coding_apps = [
            "code.exe",  # VS Code
            "pycharm64.exe",
            "devenv.exe",  # Visual Studio
            "sublime_text.exe",
            "notepad++.exe"
        ]
        
        # Streaming/Media apps
        self.streaming_apps = [
            "obs64.exe",
            "streamlabs obs.exe",
            "discord.exe",
            "spotify.exe",
            "chrome.exe",
            "firefox.exe"
        ]
        
        # Browsers (for web browsing detection)
        self.browsers = [
            "chrome.exe",
            "firefox.exe",
            "msedge.exe",
            "brave.exe"
        ]


class ActivitySensor(ISensor):
    """
    Monitors user activity by scanning running processes.
    
    Detects:
    - Idle (no significant apps)
    - Gaming (game detected)
    - Coding (IDE detected)
    - Browsing (browser active)
    - Streaming (OBS/Discord detected)
    
    Fires UserActivityEvent when activity changes.
    """
    
    def __init__(self, config: ActivityConfig, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        
        # State tracking
        self._last_activity: str = "Unknown"
        self._last_app_name: Optional[str] = None
        self._last_check_time: Optional[datetime] = None
        
        # Cooldown to prevent spam (30 seconds between events)
        self._cooldown_seconds = 30
        self._last_event_time: Optional[datetime] = None
        
        logger.info("Activity sensor initialized")
    
    def get_context(self) -> str:
        """Get current activity context and detect changes."""
        current_activity, current_app = self._detect_activity()
        
        # Check if activity changed
        if current_activity != self._last_activity:
            # Check cooldown
            now = datetime.now(timezone.utc)
            can_emit = True
            
            if self._last_event_time:
                time_since_last = (now - self._last_event_time).total_seconds()
                if time_since_last < self._cooldown_seconds:
                    can_emit = False
                    logger.debug(f"Activity change cooldown active ({time_since_last:.0f}s)")
            
            if can_emit:
                # Fire event
                event = UserActivityEvent(
                    old_activity=self._last_activity,
                    new_activity=current_activity,
                    app_name=current_app
                )
                
                # Publish asynchronously (non-blocking)
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.event_bus.publish(event))
                    logger.info(
                        f"🎯 Activity changed: {self._last_activity} → {current_activity} "
                        f"({current_app or 'N/A'})"
                    )
                    self._last_event_time = now
                except RuntimeError:
                    # No event loop running, skip event
                    logger.debug("No event loop, skipping activity event")
            
            # Update state
            self._last_activity = current_activity
            self._last_app_name = current_app
        
        self._last_check_time = datetime.now(timezone.utc)
        
        # Return context string for prompt
        context_parts = [
            f"User Activity: {current_activity}"
        ]
        
        if current_app:
            context_parts.append(f"Active App: {current_app}")
        
        return "\n".join(context_parts)
    
    def _detect_activity(self) -> tuple[str, Optional[str]]:
        """
        Detect current user activity based on running processes.
        
        Returns:
            (activity_name, app_name)
        """
        try:
            running_processes = self._get_running_processes()
            
            # Check gaming apps first (highest priority)
            for game in self.config.gaming_apps:
                if self._is_process_running(game, running_processes):
                    return "Gaming", game
            
            # Check coding apps
            for ide in self.config.coding_apps:
                if self._is_process_running(ide, running_processes):
                    return "Coding", ide
            
            # Check streaming apps
            for stream in self.config.streaming_apps:
                if self._is_process_running(stream, running_processes):
                    # Special case: Discord alone is not "streaming"
                    if stream.lower() == "discord.exe":
                        continue
                    return "Streaming", stream
            
            # Check browsers (fallback)
            for browser in self.config.browsers:
                if self._is_process_running(browser, running_processes):
                    return "Browsing", browser
            
            # Default: Idle
            return "Idle", None
            
        except Exception as e:
            logger.error(f"Activity detection failed: {e}")
            return "Unknown", None
    
    def _get_running_processes(self) -> set[str]:
        """Get set of running process names (lowercase for comparison)."""
        processes = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name:
                    processes.add(name.lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    def _is_process_running(self, process_name: str, running_processes: set[str]) -> bool:
        """Check if process is running (case-insensitive)."""
        return process_name.lower() in running_processes
    
    def get_name(self) -> str:
        """Get sensor name."""
        return "ActivitySensor"
    
    def get_last_activity(self) -> str:
        """Get last detected activity (for debugging)."""
        return self._last_activity
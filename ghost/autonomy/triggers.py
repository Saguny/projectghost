"""Trigger evaluation for autonomous behavior."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class TriggerEvaluator:
    """Evaluates various triggers for autonomous initiation."""
    
    def __init__(self, silence_threshold_minutes: int = 180):
        self._last_message_time: Optional[datetime] = None
        self._silence_threshold_minutes = silence_threshold_minutes
        logger.info(f"Trigger evaluator initialized (silence_threshold={silence_threshold_minutes}min)")
    
    async def evaluate(self) -> Optional[str]:
        """
        Evaluate all triggers and return reason if one fires.
        
        Returns:
            Trigger reason string if triggered, None otherwise
        """
        # Check for prolonged silence
        silence_trigger = self._check_silence()
        if silence_trigger:
            return silence_trigger
        
        # Check for specific times of day
        time_trigger = self._check_time_of_day()
        if time_trigger:
            return time_trigger
        
        return None
    
    def update_last_message_time(self):
        """Update the last message timestamp (called by AutonomyEngine)."""
        self._last_message_time = datetime.now(timezone.utc)
        logger.debug(f"Updated last message time: {self._last_message_time.isoformat()}")
    
    def _check_silence(self) -> Optional[str]:
        """Check if there's been prolonged silence."""
        if not self._last_message_time:
            logger.debug("No message history yet, skipping silence check")
            return None
        
        silence_duration = datetime.now(timezone.utc) - self._last_message_time
        threshold = timedelta(minutes=self._silence_threshold_minutes)
        
        if silence_duration > threshold:
            hours = int(silence_duration.total_seconds() / 3600)
            logger.info(f"Silence detected: {hours}h since last message")
            return f"prolonged silence ({hours}h since last message)"
        
        return None
    
    def _check_time_of_day(self) -> Optional[str]:
        """Check for specific trigger times."""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        
        # Only trigger once per hour (check if we're in the first 5 minutes)
        if minute > 5:
            return None
        
        # Morning check-in (9 AM)
        if hour == 9:
            return "morning check-in time"
        
        # Evening check-in (8 PM)
        if hour == 20:
            return "evening check-in time"
        
        return None
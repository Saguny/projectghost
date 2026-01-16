"""Trigger evaluation for autonomous behavior."""

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class TriggerEvaluator:
    """Evaluates various triggers for autonomous initiation."""
    
    def __init__(self):
        self._last_message_time: Optional[datetime] = None
        self._silence_threshold_minutes = 180  # 3 hours
    
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
        """Update the last message timestamp."""
        self._last_message_time = datetime.now()
    
    def _check_silence(self) -> Optional[str]:
        """Check if there's been prolonged silence."""
        if not self._last_message_time:
            return None
        
        silence_duration = datetime.now() - self._last_message_time
        threshold = timedelta(minutes=self._silence_threshold_minutes)
        
        if silence_duration > threshold:
            hours = int(silence_duration.total_seconds() / 3600)
            return f"prolonged silence ({hours}h since last message)"
        
        return None
    
    def _check_time_of_day(self) -> Optional[str]:
        """Check for specific trigger times."""
        hour = datetime.now().hour
        
        # Morning check-in (9 AM)
        if hour == 9:
            return "morning check-in time"
        
        # Evening check-in (8 PM)
        if hour == 20:
            return "evening check-in time"
        
        return None
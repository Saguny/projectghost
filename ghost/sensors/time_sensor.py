"""Time and circadian awareness sensor."""

from datetime import datetime
from ghost.core.interfaces import ISensor
from ghost.emotion.circadian import CircadianRhythm


class TimeSensor(ISensor):
    """Provides time context."""
    
    def __init__(self):
        self.circadian = CircadianRhythm()
    
    def get_context(self) -> str:
        """Get time context."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        phase = self.circadian.get_phase_description()
        
        return f"""
Time Context:
- Current Time: {time_str}
- Circadian Phase: {phase}
"""
    
    def get_name(self) -> str:
        """Get sensor name."""
        return "TimeSensor"
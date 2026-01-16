"""Hardware monitoring sensor."""

from ghost.core.interfaces import ISensor
from ghost.cryostasis.monitor import ResourceMonitor
from ghost.core.config import CryostasisConfig


class HardwareSensor(ISensor):
    """Provides hardware status context."""
    
    def __init__(self, config: CryostasisConfig):
        self.monitor = ResourceMonitor(config)
    
    def get_context(self) -> str:
        """Get hardware context."""
        return self.monitor.get_system_summary()
    
    def get_name(self) -> str:
        """Get sensor name."""
        return "HardwareSensor"
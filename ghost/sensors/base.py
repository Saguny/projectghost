"""Base sensor implementation."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseSensor(ABC):
    """Base class for all sensors."""
    
    def __init__(self):
        self._enabled = True
    
    @abstractmethod
    def get_context(self) -> str:
        """Get sensor context as string."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get sensor name."""
        pass
    
    def enable(self):
        """Enable sensor."""
        self._enabled = True
    
    def disable(self):
        """Disable sensor."""
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if sensor is enabled."""
        return self._enabled
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get sensor metadata."""
        return {
            "name": self.get_name(),
            "enabled": self._enabled
        }
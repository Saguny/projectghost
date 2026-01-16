"""Environmental awareness sensors.

This module provides context about the system environment:
- Hardware status (CPU, GPU, RAM)
- Time and circadian phase
- File system activity
- Future: Weather, calendar, etc.

Key Features:
- Pluggable sensor architecture
- Graceful failure handling
- Async-safe operation
- Context string generation

Usage:
    from ghost.sensors import HardwareSensor, TimeSensor
    from ghost.core.config import CryostasisConfig
    
    # Create sensors
    sensors = [
        HardwareSensor(cryostasis_config),
        TimeSensor()
    ]
    
    # Gather context
    context = "\n".join(sensor.get_context() for sensor in sensors)
"""

from ghost.sensors.base import BaseSensor
from ghost.sensors.hardware_sensor import HardwareSensor
from ghost.sensors.time_sensor import TimeSensor
from ghost.sensors.file_sensor import FileSensor

__all__ = [
    "BaseSensor",
    "HardwareSensor",
    "TimeSensor",
    "FileSensor",
]


def create_default_sensors(cryostasis_config=None, workspace_root=None):
    """Factory function to create default sensor set.
    
    Args:
        cryostasis_config: Optional CryostasisConfig for hardware monitoring
        workspace_root: Optional workspace path for file monitoring
        
    Returns:
        List of configured sensors
    """
    sensors = [TimeSensor()]
    
    if cryostasis_config:
        sensors.append(HardwareSensor(cryostasis_config))
    
    if workspace_root:
        sensors.append(FileSensor(workspace_root))
    
    return sensors
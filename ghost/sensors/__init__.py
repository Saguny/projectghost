"""Environmental awareness sensors.

This module provides context about the system environment:
- Hardware status (CPU, GPU, RAM)
- Time and circadian phase
- File system activity
- User activity monitoring
- Future: Weather, calendar, etc.

Key Features:
- Pluggable sensor architecture
- Graceful failure handling
- Async-safe operation
- Context string generation

Usage:
    from ghost.sensors import HardwareSensor, TimeSensor, ActivitySensor
    from ghost.core.config import CryostasisConfig, ActivityConfig
    
    # Create sensors
    sensors = [
        HardwareSensor(cryostasis_config),
        TimeSensor(),
        ActivitySensor(activity_config)
    ]
    
    # Gather context
    context = "\n".join(sensor.get_context() for sensor in sensors)
"""

from ghost.sensors.base import BaseSensor
from ghost.sensors.hardware_sensor import HardwareSensor
from ghost.sensors.time_sensor import TimeSensor
from ghost.sensors.file_sensor import FileSensor
from ghost.sensors.activity_sensor import ActivitySensor, ActivityConfig, UserActivityEvent

__all__ = [
    "BaseSensor",
    "HardwareSensor",
    "TimeSensor",
    "FileSensor",
    "ActivitySensor",
    "ActivityConfig",
    "UserActivityEvent",
]


def create_default_sensors(
    cryostasis_config=None,
    workspace_root=None,
    activity_config=None
):
    """Factory function to create default sensor set.
    
    Args:
        cryostasis_config: Optional CryostasisConfig for hardware monitoring
        workspace_root: Optional workspace path for file monitoring
        activity_config: Optional ActivityConfig for process monitoring
        
    Returns:
        List of configured sensors
    """
    sensors = [TimeSensor()]
    
    if cryostasis_config:
        sensors.append(HardwareSensor(cryostasis_config))
    
    if workspace_root:
        sensors.append(FileSensor(workspace_root))
    
    if activity_config and activity_config.enabled:
        sensors.append(ActivitySensor(activity_config))
    
    return sensors
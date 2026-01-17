import logging
from datetime import datetime, timezone
from pathlib import Path
import json

from ghost.core.events import (
    EventBus,
    EmotionalStateChanged,
    ResponseGenerated,
    CryostasisActivated,
    CryostasisDeactivated,
    SystemResourceAlert
)

logger = logging.getLogger(__name__)


class SystemEventLogger:
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.log_dir / "metrics.jsonl"
        
    async def on_emotional_state_changed(self, event: EmotionalStateChanged):
        logger.info(
            f"Emotional transition: "
            f"P:{event.old_pleasure:.2f}->{event.new_pleasure:.2f}, "
            f"A:{event.old_arousal:.2f}->{event.new_arousal:.2f}, "
            f"D:{event.old_dominance:.2f}->{event.new_dominance:.2f} "
            f"({event.trigger})"
        )
        
        await self._write_metric({
            "event": "emotional_state_changed",
            "timestamp": event.timestamp.isoformat(),
            "old_state": {
                "pleasure": event.old_pleasure,
                "arousal": event.old_arousal,
                "dominance": event.old_dominance
            },
            "new_state": {
                "pleasure": event.new_pleasure,
                "arousal": event.new_arousal,
                "dominance": event.new_dominance
            },
            "trigger": event.trigger
        })
    
    async def on_response_generated(self, event: ResponseGenerated):
        logger.info(
            f"Response generated: {len(event.content)} chars, "
            f"{event.generation_time_ms:.0f}ms, "
            f"{len(event.context_used)} context items"
        )
        
        await self._write_metric({
            "event": "response_generated",
            "timestamp": event.timestamp.isoformat(),
            "generation_time_ms": event.generation_time_ms,
            "content_length": len(event.content),
            "context_items": len(event.context_used)
        })
    
    async def on_cryostasis_activated(self, event: CryostasisActivated):
        logger.warning(
            f"Cryostasis activated: {event.reason} "
            f"(freed {event.memory_freed_mb:.1f}MB)"
        )
    
    async def on_cryostasis_deactivated(self, event: CryostasisDeactivated):
        logger.info(
            f"Cryostasis deactivated "
            f"(load time: {event.load_time_ms:.0f}ms)"
        )
    
    async def on_resource_alert(self, event: SystemResourceAlert):
        logger.warning(
            f"Resource alert: {event.resource_type} "
            f"at {event.current_value:.1f}% "
            f"(threshold: {event.threshold:.1f}%) - "
            f"{event.action_taken}"
        )
    
    async def _write_metric(self, data: dict):
        try:
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write metric: {e}")


def register_event_listeners(event_bus: EventBus, log_dir: str = "data/logs"):
    event_logger = SystemEventLogger(log_dir)
    
    event_bus.subscribe(EmotionalStateChanged, event_logger.on_emotional_state_changed)
    event_bus.subscribe(ResponseGenerated, event_logger.on_response_generated)
    event_bus.subscribe(CryostasisActivated, event_logger.on_cryostasis_activated)
    event_bus.subscribe(CryostasisDeactivated, event_logger.on_cryostasis_deactivated)
    event_bus.subscribe(SystemResourceAlert, event_logger.on_resource_alert)
    
    logger.info("Event listeners registered")
    return event_logger
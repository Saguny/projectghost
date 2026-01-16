"""Event system for decoupled communication between components."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Type
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """Base event class.
    
    Note: All fields have defaults to allow subclasses to add required fields.
    """
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageReceived(Event):
    """User message received."""
    user_id: str = ""
    user_name: str = ""
    content: str = ""
    channel_id: str = ""


@dataclass
class ResponseGenerated(Event):
    """AI response generated."""
    content: str = ""
    context_used: List[str] = field(default_factory=list)
    generation_time_ms: float = 0.0


@dataclass
class EmotionalStateChanged(Event):
    """Emotional state transition."""
    old_pleasure: float = 0.0
    old_arousal: float = 0.0
    old_dominance: float = 0.0
    new_pleasure: float = 0.0
    new_arousal: float = 0.0
    new_dominance: float = 0.0
    trigger: str = ""


@dataclass
class SystemResourceAlert(Event):
    """System resource threshold exceeded."""
    resource_type: str = ""  # 'gpu', 'cpu', 'memory'
    current_value: float = 0.0
    threshold: float = 0.0
    action_taken: str = ""


@dataclass
class CryostasisActivated(Event):
    """Model unloaded from memory."""
    reason: str = ""
    memory_freed_mb: float = 0.0


@dataclass
class CryostasisDeactivated(Event):
    """Model loaded back into memory."""
    load_time_ms: float = 0.0


@dataclass
class ProactiveImpulse(Event):
    """AI decided to initiate conversation."""
    trigger_reason: str = ""
    confidence: float = 0.0


@dataclass
class AutonomousMessageSent(Event):
    """Autonomous message was sent to Discord."""
    content: str = ""
    channel_id: str = ""


class EventBus:
    """Central event bus for system-wide communication with backpressure."""
    
    def __init__(self, max_queue_size: int = 1000):
        self._handlers: Dict[Type[Event], List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._task = None
        logger.info(f"Event bus initialized (max_queue_size={max_queue_size})")
    
    def subscribe(self, event_type: Type[Event], handler: Callable):
        """Register an event handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")
    
    def unsubscribe(self, event_type: Type[Event], handler: Callable):
        """Remove an event handler."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers."""
        try:
            await asyncio.wait_for(self._queue.put(event), timeout=1.0)
        except asyncio.TimeoutError:
            logger.error(f"Event queue full, dropping {type(event).__name__}")
    
    async def start(self):
        """Start processing events."""
        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
    
    async def stop(self):
        """Stop processing events."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Event bus stopped")
    
    async def _process_events(self):
        """Process events from queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                await self._dispatch(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
    
    async def _dispatch(self, event: Event):
        """Dispatch event to handlers with error isolation."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for {event_type.__name__}")
            return
        
        logger.debug(f"Dispatching {event_type.__name__} to {len(handlers)} handlers")
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    f"Handler {handler.__name__} failed for {event_type.__name__}: {e}",
                    exc_info=True
                )
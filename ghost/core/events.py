"""Event system for decoupled communication between components."""

from dataclasses import dataclass, field
from datetime import datetime
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


# --- FIX APPLIED HERE: kw_only=True ---
@dataclass(kw_only=True)
class Event:
    """Base event class.
    
    kw_only=True is required here because subclasses have fields without defaults.
    This moves timestamp, priority, and metadata to the end of the __init__ arguments.
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageReceived(Event):
    """User message received."""
    user_id: str
    user_name: str
    content: str
    channel_id: str


@dataclass
class ResponseGenerated(Event):
    """AI response generated."""
    content: str
    context_used: List[str]
    generation_time_ms: float


@dataclass
class EmotionalStateChanged(Event):
    """Emotional state transition."""
    old_pleasure: float
    old_arousal: float
    old_dominance: float
    new_pleasure: float
    new_arousal: float
    new_dominance: float
    trigger: str


@dataclass
class SystemResourceAlert(Event):
    """System resource threshold exceeded."""
    resource_type: str  # 'gpu', 'cpu', 'memory'
    current_value: float
    threshold: float
    action_taken: str


@dataclass
class CryostasisActivated(Event):
    """Model unloaded from memory."""
    reason: str
    memory_freed_mb: float


@dataclass
class CryostasisDeactivated(Event):
    """Model loaded back into memory."""
    load_time_ms: float


@dataclass
class ProactiveImpulse(Event):
    """AI decided to initiate conversation."""
    trigger_reason: str
    confidence: float


class EventBus:
    """Central event bus for system-wide communication."""
    
    def __init__(self):
        self._handlers: Dict[Type[Event], List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task = None
    
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
        await self._queue.put(event)
    
    async def start(self):
        """Start processing events."""
        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
    
    async def stop(self):
        """Stop processing events."""
        self._running = False
        if self._task:
            await self._task
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
        """Dispatch event to handlers."""
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
"""Episodic buffer for short-term conversation context."""

from collections import deque
from typing import List
import logging

from ghost.core.interfaces import Message

logger = logging.getLogger(__name__)


class EpisodicBuffer:
    """Manages recent conversation context with a sliding window."""
    
    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self.messages: deque[Message] = deque(maxlen=max_size)
        logger.info(f"Episodic buffer initialized (max_size={max_size})")
    
    def add(self, message: Message) -> None:
        """Add a message to the buffer."""
        self.messages.append(message)
        logger.debug(f"Added to episodic buffer (total: {len(self.messages)})")
    
    def get_recent(self, limit: int = 10) -> List[Message]:
        """Get the most recent N messages."""
        return list(self.messages)[-limit:]
    
    def get_all(self) -> List[Message]:
        """Get all messages in buffer."""
        return list(self.messages)
    
    def clear(self) -> None:
        """Clear the buffer."""
        self.messages.clear()
        logger.info("Episodic buffer cleared")
    
    def size(self) -> int:
        """Get current buffer size."""
        return len(self.messages)
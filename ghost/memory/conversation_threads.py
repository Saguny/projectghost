"""Track conversation threads and topics."""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from ghost.core.interfaces import Message

logger = logging.getLogger(__name__)


class ConversationThread:
    """Represents a single conversation thread/topic."""
    
    def __init__(self, thread_id: str, topic: str):
        self.thread_id = thread_id
        self.topic = topic
        self.messages: List[Message] = []
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.message_count = 0
    
    def add_message(self, message: Message):
        """Add message to thread."""
        self.messages.append(message)
        self.last_updated = datetime.utcnow()
        self.message_count += 1
    
    def get_summary(self) -> str:
        """Get thread summary."""
        return f"Thread about '{self.topic}' with {self.message_count} messages"


class ConversationThreadManager:
    """Manages conversation threads for better context tracking."""
    
    def __init__(self, session_timeout_minutes: int = 30):
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.threads: Dict[str, ConversationThread] = {}
        self.current_thread_id: Optional[str] = None
    
    def start_new_thread(self, topic: str = "general") -> str:
        """Start a new conversation thread."""
        thread_id = f"thread_{datetime.utcnow().timestamp()}"
        self.threads[thread_id] = ConversationThread(thread_id, topic)
        self.current_thread_id = thread_id
        logger.info(f"Started new thread: {thread_id} ({topic})")
        return thread_id
    
    def add_to_current_thread(self, message: Message):
        """Add message to current thread or start new one."""
        # Check if we need a new thread (timeout)
        if self.current_thread_id:
            current = self.threads[self.current_thread_id]
            if datetime.utcnow() - current.last_updated > self.session_timeout:
                logger.info("Session timeout, starting new thread")
                self.start_new_thread()
        else:
            self.start_new_thread()
        
        # Add to current thread
        self.threads[self.current_thread_id].add_message(message)
    
    def get_thread_context(self, thread_id: str) -> List[Message]:
        """Get all messages in a thread."""
        if thread_id in self.threads:
            return self.threads[thread_id].messages
        return []
    
    def get_recent_threads(self, limit: int = 5) -> List[ConversationThread]:
        """Get recent conversation threads."""
        sorted_threads = sorted(
            self.threads.values(),
            key=lambda t: t.last_updated,
            reverse=True
        )
        return sorted_threads[:limit]
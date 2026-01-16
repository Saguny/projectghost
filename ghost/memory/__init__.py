"""Memory system with hierarchical storage and semantic search.

This module implements a three-tier memory architecture:
1. Working Memory - Last 10 messages (immediate context)
2. Episodic Memory - Recent session (up to 50 messages)
3. Semantic Memory - Long-term facts stored in vector database

Key Features:
- Automatic memory consolidation
- Importance-based filtering
- Semantic similarity search
- Optional summarization
- Auto-snapshots

Usage:
    from ghost.memory import MemoryService
    from ghost.core.config import MemoryConfig
    
    config = MemoryConfig()
    memory = MemoryService(config)
    await memory.add_message(message)
    context = await memory.get_context(query)
"""

from ghost.memory.memory_service import MemoryService
from ghost.memory.vector_store import VectorStore
from ghost.memory.episodic_buffer import EpisodicBuffer
from ghost.memory.hierarchical_memory import HierarchicalMemory
from ghost.memory.importance_scorer import ImportanceScorer
from ghost.memory.conversation_threads import (
    ConversationThread,
    ConversationThreadManager
)

# Optional components
try:
    from ghost.memory.redis_cache import RedisMemoryCache
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    RedisMemoryCache = None

try:
    from ghost.memory.sumamrizer import ConversationSummarizer
    SUMMARIZER_AVAILABLE = True
except ImportError:
    SUMMARIZER_AVAILABLE = False
    ConversationSummarizer = None


__all__ = [
    # Main Service
    "MemoryService",
    
    # Core Components
    "VectorStore",
    "EpisodicBuffer",
    "HierarchicalMemory",
    
    # Utilities
    "ImportanceScorer",
    "ConversationThread",
    "ConversationThreadManager",
    
    # Optional (may be None if deps missing)
    "RedisMemoryCache",
    "ConversationSummarizer",
    
    # Feature Flags
    "REDIS_AVAILABLE",
    "SUMMARIZER_AVAILABLE",
]


def create_memory_service(config) -> MemoryService:
    """Factory function to create a fully configured memory service.
    
    Args:
        config: MemoryConfig instance
        
    Returns:
        Configured MemoryService
    """
    return MemoryService(config)
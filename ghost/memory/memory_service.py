"""Unified memory service combining vector store and episodic buffer."""

from typing import List, Dict, Any
import logging
from datetime import datetime
import json
from pathlib import Path

from ghost.core.interfaces import IMemoryProvider, Message
from ghost.memory.vector_store import VectorStore
from ghost.memory.episodic_buffer import EpisodicBuffer
from ghost.core.config import MemoryConfig

logger = logging.getLogger(__name__)


class MemoryService(IMemoryProvider):
    """Manages both long-term semantic and short-term episodic memory."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.vector_store = VectorStore(
            persist_directory=config.vector_db_path,
            embedding_model=config.embedding_model
        )
        self.episodic_buffer = EpisodicBuffer(max_size=config.episodic_buffer_size)
        from ghost.memory.hierarchical_memory import HierarchicalMemory
        self.hierarchical = HierarchicalMemory(
            self.episodic_buffer,
            self.vector_store,
            consolidation_threshold=50
        )
        
        self._snapshot_path = Path("data/memory_snapshots")
        self._snapshot_path.mkdir(parents=True, exist_ok=True)
        logger.info("Memory service initialized with hierarchical memory")


    async def add_message(self, message: Message) -> None:
        """Store message in hierarchical memory system."""
        await self.hierarchical.add_message(message)
    
    async def search_semantic(self, query: str, limit: int = 5) -> List[Message]:
        """Search for semantically similar messages."""
        try:
            return await self.vector_store.search(query, limit)
        except Exception as e:
            logger.error(f"Semantic search failed: {e}", exc_info=True)
            return []
    
    async def get_recent(self, limit: int = 10) -> List[Message]:
        """Get recent messages from working + episodic memory."""
        context = await self.hierarchical.get_context("", include_working=True)
        working = context['working']
        episodic = context['episodic']
        
        # Combine and deduplicate
        all_messages = working + episodic
        seen = set()
        unique = []
        for msg in reversed(all_messages):
            key = (msg.role, msg.content)
            if key not in seen:
                seen.add(key)
                unique.insert(0, msg)
        
        return unique[-limit:]
    
    async def clear(self) -> None:
        """Clear all memory (use with caution)."""
        logger.warning("Clearing all memory")
        self.episodic_buffer.clear()
        await self.vector_store.clear()
    
    async def create_snapshot(self) -> str:
        """Create a backup snapshot of current memory state."""
        timestamp = datetime.utcnow().isoformat()
        snapshot_file = self._snapshot_path / f"snapshot_{timestamp}.json"
        
        snapshot_data = {
            "timestamp": timestamp,
            "episodic_buffer": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": msg.metadata
                }
                for msg in self.episodic_buffer.messages
            ],
            "vector_store_stats": await self.vector_store.get_stats()
        }
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        logger.info(f"Created memory snapshot: {snapshot_file}")
        return str(snapshot_file)
    
    async def get_context_summary(self) -> str:
        """Get a summary of current memory state."""
        recent = await self.get_recent(5)
        stats = await self.vector_store.get_stats()
        
        return f"""
Memory State:
- Recent messages in buffer: {len(recent)}
- Total semantic memories: {stats.get('total_memories', 0)}
- Last interaction: {recent[-1].metadata.get('timestamp', 'unknown') if recent else 'none'}
"""
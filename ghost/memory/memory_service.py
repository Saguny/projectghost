"""Unified memory service combining vector store and episodic buffer."""

from typing import List, Dict, Any
import logging
from datetime import datetime, timezone
import json
from pathlib import Path

from discord import Optional

from ghost.core.interfaces import IMemoryProvider, Message
from ghost.memory.vector_store import VectorStore
from ghost.memory.episodic_buffer import EpisodicBuffer
from ghost.memory.hierarchical_memory import HierarchicalMemory
from ghost.core.config import MemoryConfig

logger = logging.getLogger(__name__)


class MemoryService(IMemoryProvider):
    """Manages both long-term semantic and short-term episodic memory."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        
        # Initialize vector store
        self.vector_store = VectorStore(
            persist_directory=config.vector_db_path,
            embedding_model=config.embedding_model,
            importance_threshold=config.importance_threshold
        )
        
        # Initialize episodic buffer
        self.episodic_buffer = EpisodicBuffer(max_size=config.episodic_buffer_size)
        
        # Initialize hierarchical memory
        self.hierarchical = HierarchicalMemory(
            episodic_buffer=self.episodic_buffer,
            vector_store=self.vector_store,
            consolidation_threshold=config.consolidation_threshold,
            enable_summarization=config.enable_summarization
        )
        
        # Snapshot management
        self._snapshot_path = Path("data/memory_snapshots")
        self._snapshot_path.mkdir(parents=True, exist_ok=True)
        
        # Auto-snapshot tracking
        self._last_snapshot_time: Optional[datetime] = None
        self._auto_snapshot_enabled = config.auto_snapshot_enabled
        self._auto_snapshot_interval_hours = config.auto_snapshot_interval_hours
        
        logger.info("Memory service initialized with hierarchical memory")
    
    async def add_message(self, message: Message) -> None:
        """Store message in hierarchical memory system."""
        await self.hierarchical.add_message(message)
        
        # Check if auto-snapshot needed
        if self._auto_snapshot_enabled:
            await self._check_auto_snapshot()
    
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
        working = context.get('working', [])
        episodic = context.get('episodic', [])
        
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
    
    async def get_context(self, query: str, include_working: bool = True) -> Dict[str, List[Message]]:
        """Get context from all memory tiers (for orchestrator)."""
        return await self.hierarchical.get_context(query, include_working)
    
    async def clear(self) -> None:
        """Clear all memory (use with caution)."""
        logger.warning("Clearing all memory")
        self.episodic_buffer.clear()
        await self.vector_store.clear()
        self.hierarchical.working_memory.clear()
    
    async def create_snapshot(self) -> str:
        """Create a backup snapshot of current memory state."""
        timestamp = datetime.now(timezone.utc).isoformat().replace(':', '-')
        snapshot_file = self._snapshot_path / f"snapshot_{timestamp}.json"
        
        snapshot_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "episodic_buffer": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": msg.metadata
                }
                for msg in self.episodic_buffer.messages
            ],
            "working_memory": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": msg.metadata
                }
                for msg in self.hierarchical.working_memory
            ],
            "vector_store_stats": await self.vector_store.get_stats()
        }
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        self._last_snapshot_time = datetime.now(timezone.utc)
        logger.info(f"Created memory snapshot: {snapshot_file}")
        return str(snapshot_file)
    
    async def _check_auto_snapshot(self) -> None:
        """Check if auto-snapshot is needed."""
        if not self._last_snapshot_time:
            # Create initial snapshot
            await self.create_snapshot()
            return
        
        time_since_snapshot = datetime.now(timezone.utc) - self._last_snapshot_time
        hours_since_snapshot = time_since_snapshot.total_seconds() / 3600
        
        if hours_since_snapshot >= self._auto_snapshot_interval_hours:
            logger.info(f"Auto-snapshot triggered ({hours_since_snapshot:.1f} hours since last)")
            await self.create_snapshot()
    
    async def get_context_summary(self) -> str:
        """Get a summary of current memory state."""
        recent = await self.get_recent(5)
        stats = await self.vector_store.get_stats()
        
        return f"""
Memory State:
- Recent messages in buffer: {len(recent)}
- Total semantic memories: {stats.get('total_memories', 0)}
- Last interaction: {recent[-1].metadata.get('timestamp', 'unknown') if recent else 'none'}
- Working memory: {len(self.hierarchical.working_memory)} messages
- Episodic buffer: {self.episodic_buffer.size()} messages
"""
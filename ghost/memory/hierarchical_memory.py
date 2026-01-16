"""Hierarchical memory system: Working → Episodic → Semantic."""

import logging
from typing import List, Dict
from datetime import datetime
from ghost.core.interfaces import Message

logger = logging.getLogger(__name__)


class HierarchicalMemory:
    """
    Three-tier memory system:
    1. Working Memory: Last 10 messages (immediate context)
    2. Episodic Memory: Last session (20-50 messages)
    3. Semantic Memory: Important facts, summarized long-term
    """

    def __init__(
        self,
        episodic_buffer,
        vector_store,
        consolidation_threshold: int = 50
    ):
        self.episodic_buffer = episodic_buffer
        self.vector_store = vector_store
        self.consolidation_threshold = consolidation_threshold

        # Working memory (most recent)
        self.working_memory: List[Message] = []

        # Session tracking
        self.current_session_id = None
        self.last_interaction = None

        logger.info("Hierarchical memory initialized")

    async def add_message(self, message: Message) -> None:
        """Add message to appropriate memory tier."""
        # Add to working memory
        self.working_memory.append(message)
        if len(self.working_memory) > 10:
            self.working_memory.pop(0)

        # Add to episodic buffer
        self.episodic_buffer.add(message)

        # Check if we need consolidation
        if self.episodic_buffer.size() >= self.consolidation_threshold:
            await self._consolidate_to_semantic()

        # Add to vector store
        await self.vector_store.add_message(message)

        self.last_interaction = datetime.utcnow()

    async def get_context(
        self,
        query: str,
        include_working: bool = True
    ) -> Dict[str, List[Message]]:
        """Get context from all memory tiers."""
        context = {
            "working": [],
            "episodic": [],
            "semantic": []
        }

        # Working memory (always relevant)
        if include_working:
            context["working"] = self.working_memory.copy()

        # Episodic memory (recent conversation)
        context["episodic"] = self.episodic_buffer.get_recent(limit=15)

        # Semantic memory (relevant past info)
        context["semantic"] = await self.vector_store.search(
            query,
            limit=5,
            rerank=True
        )

        return context

    async def _consolidate_to_semantic(self) -> None:
        """Consolidate with LLM-generated summaries."""
        logger.info("Consolidating episodic memory with intelligent summarization...")

        episodes = self.episodic_buffer.get_all()

        # Use LLM summarizer if available
        if hasattr(self, "summarizer") and self.summarizer:
            summary = await self.summarizer.summarize_conversation(episodes)
        else:
            summary = self._create_summary(episodes)

        # Store enriched summary
        summary_msg = Message(
            role="system",
            content=f"[MEMORY SUMMARY]\n{summary}",
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "type": "summary",
                "message_count": len(episodes),
                "importance": "high"
            }
        )

        await self.vector_store.add_message(summary_msg)

        # Preserve recent context
        recent = self.episodic_buffer.get_recent(10)
        self.episodic_buffer.clear()
        for msg in recent:
            self.episodic_buffer.add(msg)

    def _create_summary(self, messages: List[Message]) -> str:
        """Create a simple summary of conversation."""
        # Extract key topics (simple keyword extraction)
        user_messages = [m.content for m in messages if m.role == "user"]

        if not user_messages:
            return "Conversation about general topics"

        # Simple summary (in production, use LLM to generate this)
        summary_parts = []

        # Count message types
        user_count = sum(1 for m in messages if m.role == "user")
        summary_parts.append(f"Conversation with {user_count} user messages")

        # Extract potential topics (words that appear multiple times)
        all_text = " ".join(user_messages).lower()
        words = all_text.split()

        word_freq = {}
        for word in words:
            if len(word) > 4:  # Only meaningful words
                word_freq[word] = word_freq.get(word, 0) + 1

        # Top topics
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_words:
            topics = ", ".join(w[0] for w in top_words)
            summary_parts.append(f"discussing: {topics}")

        return ". ".join(summary_parts)

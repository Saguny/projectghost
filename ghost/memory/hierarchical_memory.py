"""Hierarchical memory system: Working → Episodic → Semantic."""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
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
        consolidation_threshold: int = 40,
        enable_summarization: bool = True,
        summarizer = None  # Optional ConversationSummarizer
    ):
        self.episodic_buffer = episodic_buffer
        self.vector_store = vector_store
        self.consolidation_threshold = consolidation_threshold
        self.enable_summarization = enable_summarization
        self.summarizer = summarizer

        # Working memory (most recent)
        self.working_memory: List[Message] = []

        # Session tracking
        self.current_session_id = None
        self.last_interaction = None

        logger.info(
            f"Hierarchical memory initialized "
            f"(consolidation_threshold={consolidation_threshold}, "
            f"summarization={'enabled' if enable_summarization else 'disabled'})"
        )

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

        # Add to vector store (with importance filtering)
        await self.vector_store.add_message(message)

        self.last_interaction = datetime.now(timezone.utc)

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
        if query:
            context["semantic"] = await self.vector_store.search(
                query,
                limit=5,
                rerank=True
            )

        return context

    async def _consolidate_to_semantic(self) -> None:
        """Consolidate episodic memory to semantic with optional summarization."""
        logger.info(
            f"Consolidating episodic memory "
            f"(buffer size: {self.episodic_buffer.size()})"
        )

        episodes = self.episodic_buffer.get_all()

        # Use summarizer if available and enabled
        if self.enable_summarization and self.summarizer:
            try:
                summary = await self.summarizer.summarize_conversation(episodes)
                logger.info("Generated intelligent summary for consolidation")
            except Exception as e:
                logger.error(f"Summarization failed, using fallback: {e}")
                summary = self._create_simple_summary(episodes)
        else:
            summary = self._create_simple_summary(episodes)

        # Store enriched summary in semantic memory
        summary_msg = Message(
            role="system",
            content=f"[MEMORY SUMMARY]\n{summary}",
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "summary",
                "message_count": len(episodes),
                "importance": 0.9  # Summaries are high importance
            }
        )

        await self.vector_store.add_message(summary_msg)
        logger.info(f"Stored consolidation summary ({len(episodes)} messages)")

        # Preserve recent context in buffer
        recent = self.episodic_buffer.get_recent(10)
        self.episodic_buffer.clear()
        for msg in recent:
            self.episodic_buffer.add(msg)
        
        logger.info(f"Preserved {len(recent)} recent messages in episodic buffer")

    def _create_simple_summary(self, messages: List[Message]) -> str:
        """Create a simple summary of conversation (fallback)."""
        if not messages:
            return "No messages to summarize"

        # Extract user messages
        user_messages = [m.content for m in messages if m.role == "user"]

        if not user_messages:
            return "Conversation with no user messages"

        # Count message types
        user_count = sum(1 for m in messages if m.role == "user")
        assistant_count = sum(1 for m in messages if m.role == "assistant")

        summary_parts = [
            f"Conversation with {user_count} user messages and {assistant_count} responses"
        ]

        # Extract potential topics (simple keyword frequency)
        all_text = " ".join(user_messages).lower()
        words = all_text.split()

        # Count meaningful words (>4 chars, not common words)
        common_words = {'this', 'that', 'with', 'have', 'from', 'they', 'what', 'when', 'there'}
        word_freq = {}
        for word in words:
            if len(word) > 4 and word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Top topics
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_words:
            topics = ", ".join(w[0] for w in top_words if w[1] > 1)
            if topics:
                summary_parts.append(f"Key topics: {topics}")

        return ". ".join(summary_parts)
    
    def set_summarizer(self, summarizer):
        """Set the conversation summarizer (for late injection)."""
        self.summarizer = summarizer
        logger.info("Conversation summarizer attached to hierarchical memory")
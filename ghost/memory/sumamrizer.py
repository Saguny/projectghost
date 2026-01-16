"""Intelligent conversation summarization for long-term memory."""

import logging
from typing import List
from ghost.core.interfaces import Message
from ghost.inference.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class ConversationSummarizer:
    """Generates intelligent summaries of conversations for long-term storage."""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client
    
    async def summarize_conversation(
        self, 
        messages: List[Message],
        focus_on_facts: bool = True
    ) -> str:
        """
        Generate a concise summary of conversation focusing on key facts.
        
        Args:
            messages: List of messages to summarize
            focus_on_facts: If True, emphasize factual information over chitchat
        
        Returns:
            Concise summary string
        """
        if not messages:
            return ""
        
        # Build conversation text
        conversation = []
        for msg in messages:
            if msg.role in ['user', 'assistant']:
                # Clean up format
                content = msg.content
                if ": " in content and msg.role == 'user':
                    # Remove "UserName: " prefix
                    content = content.split(": ", 1)[1]
                
                speaker = "User" if msg.role == 'user' else "Assistant"
                conversation.append(f"{speaker}: {content}")
        
        conversation_text = "\n".join(conversation)
        
        # Create summarization prompt
        summary_prompt = f"""You are a memory consolidation system. Your job is to create a concise summary of the following conversation that preserves the most important information.

Focus on:
- Key facts mentioned by the user (preferences, personal info, past events)
- Important topics discussed
- Decisions made or plans mentioned
- Recurring themes

Conversation:
{conversation_text}

Create a bullet-point summary (max 5 points) of the most important information to remember:"""
        
        # Generate summary
        try:
            summary_messages = [
                Message(
                    role="user",
                    content=summary_prompt,
                    metadata={}
                )
            ]
            
            summary = await self.ollama_client.generate(
                messages=summary_messages,
                temperature=0.3,  # Low temperature for consistent summaries
                max_tokens=300
            )
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            # Fallback to simple summary
            return f"Conversation covering {len(messages)} messages about various topics"
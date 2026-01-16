"""Dynamic prompt builder with context assembly."""

from typing import List, Dict, Any
import logging
from pathlib import Path
import yaml

from ghost.core.interfaces import Message
from ghost.core.config import PersonaConfig

logger = logging.getLogger(__name__)

# Cache templates at module level
_TEMPLATES_CACHE = None


def _load_templates() -> dict:
    """Load prompt templates from YAML (cached)."""
    global _TEMPLATES_CACHE
    if _TEMPLATES_CACHE is not None:
        return _TEMPLATES_CACHE
    
    template_path = Path("config/prompts.yaml")
    if template_path.exists():
        with open(template_path) as f:
            _TEMPLATES_CACHE = yaml.safe_load(f)
            return _TEMPLATES_CACHE
    return {}


class PromptBuilder:
    """Builds dynamic prompts with emotional and contextual awareness."""
    
    def __init__(self, persona_config: PersonaConfig):
        self.persona_config = persona_config
        self.templates = _load_templates()
    
    def build_conversation_context(
        self,
        working_memory: List[Message],
        episodic_memory: List[Message],
        semantic_memory: List[Message],
        emotional_context: dict,
        sensory_context: str,
        max_tokens: int = 3000
    ) -> List[Message]:
        """Build complete conversation context with proper deduplication."""
        
        messages = []
        
        # Build system prompt
        system_content = self._build_system_prompt(
            emotional_context,
            sensory_context,
            semantic_memory
        )
        
        messages.append(Message(
            role="system",
            content=system_content,
            metadata={}
        ))
        
        token_count = self._estimate_tokens(system_content)
        
        # Deduplicate memories against ALL conversation history
        all_conversation = working_memory + episodic_memory
        conversation_content = {
            self._normalize_content(msg.content) for msg in all_conversation
        }
        
        # Only include unique semantic memories
        unique_semantic = []
        for mem in semantic_memory:
            normalized = self._normalize_content(mem.content)
            if normalized not in conversation_content:
                unique_semantic.append(mem)
        
        if len(semantic_memory) - len(unique_semantic) > 0:
            logger.debug(
                f"Filtered {len(semantic_memory) - len(unique_semantic)} duplicate memories"
            )
        
        # Combine conversation history (working + episodic, already in order)
        # Working memory is most recent, so it should come last
        conversation_messages = []
        
        # Add episodic first (older context)
        seen_content = set()
        for msg in episodic_memory:
            content_key = (msg.role, self._normalize_content(msg.content))
            if content_key not in seen_content:
                conversation_messages.append(msg)
                seen_content.add(content_key)
        
        # Add working memory last (most recent)
        for msg in working_memory:
            content_key = (msg.role, self._normalize_content(msg.content))
            if content_key not in seen_content:
                conversation_messages.append(msg)
                seen_content.add(content_key)
        
        # Add messages within token limit (keep most recent)
        selected_messages = []
        dropped_count = 0
        
        for msg in reversed(conversation_messages[-20:]):  # Last 20 messages max
            msg_tokens = self._estimate_tokens(msg.content)
            
            if token_count + msg_tokens < max_tokens:
                selected_messages.insert(0, msg)
                token_count += msg_tokens
            else:
                dropped_count += 1
                logger.debug(f"Dropping message due to token limit")
                break
        
        messages.extend(selected_messages)
        
        logger.debug(
            f"Context: {len(messages)} messages, "
            f"~{token_count} tokens, "
            f"{len(unique_semantic)} semantic memories, "
            f"dropped {dropped_count} old messages"
        )
        
        return messages
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content for deduplication."""
        # Remove user name prefixes
        if ": " in content:
            content = content.split(": ", 1)[-1]
        
        # Lowercase and strip
        return content.strip().lower()
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (could use tiktoken for accuracy)."""
        # Basic estimation: ~4 chars per token for English
        return len(text) // 4
    
    def _build_system_prompt(
        self,
        emotional_context: dict,
        sensory_context: str,
        semantic_memories: List[Message]
    ) -> str:
        """Build dynamic system prompt with memory emphasis."""
        base_prompt = self.persona_config.system_prompt
        
        mood_desc = emotional_context.get('mood_description', 'neutral')
        circadian = emotional_context.get('circadian_phase', 'daytime')
        
        emotional_instruction = f"""
Current Emotional State: {mood_desc}
Time Context: {circadian}

Respond naturally according to this emotional state.
"""
        
        # Integrate memories into narrative
        memory_context = ""
        if semantic_memories:
            logger.debug(f"Injecting {len(semantic_memories)} memories into system prompt")
            memory_context = "\n\n=== IMPORTANT CONTEXT FROM PAST CONVERSATIONS ===\n"
            memory_context += "Remember and reference these details when relevant:\n\n"
            
            for i, mem in enumerate(semantic_memories[:5], 1):
                # Extract content without prefixes
                content = self._normalize_content(mem.content)
                # Capitalize first letter for readability
                content = content[0].upper() + content[1:] if content else content
                memory_context += f"{i}. {content}\n"
            
            memory_context += "\n" + "=" * 50 + "\n"
            memory_context += "☞ Reference these memories naturally when they're relevant.\n"
            memory_context += "☞ If the user mentions something you discussed before, acknowledge it.\n"
        
        full_prompt = f"""{base_prompt}

{emotional_instruction}

{sensory_context}
{memory_context}

CRITICAL INSTRUCTIONS:
- You have access to past conversation context above
- Reference previous discussions naturally when relevant
- If user says "remember when..." or "like I mentioned", use the context
- Maintain continuity across conversations
- You are a companion with memory, not a stateless assistant"""
        
        return full_prompt.strip()
    
    def build_impulse_prompt(
        self,
        trigger_reason: str,
        emotional_context: dict
    ) -> str:
        """Build prompt for autonomous initiation."""
        logger.debug(f"Building impulse prompt for trigger: {trigger_reason}")
        
        template = self.templates.get('impulse', {}).get('template', '''
[AUTONOMOUS INITIATION]
You noticed: {trigger}

Your current mood: {mood}

Send a brief, natural message to check in or comment on what you noticed. 
Keep it casual and appropriate to the situation. Don't ask too many questions.
''')
        
        prompt = template.format(
            trigger=trigger_reason,
            mood=emotional_context.get('mood_description', 'neutral')
        )
        
        return prompt
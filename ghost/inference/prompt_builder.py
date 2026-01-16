"""Dynamic prompt builder with context assembly."""

from typing import List, Dict, Any
import logging
from pathlib import Path
import yaml
import json

from ghost.core.interfaces import Message
from ghost.core.config import PersonaConfig

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds dynamic prompts with emotional and contextual awareness."""
    
    def __init__(self, persona_config: PersonaConfig):
        self.persona_config = persona_config
        self.templates = self._load_templates()
    
    def _load_templates(self) -> dict:
        """Load prompt templates from YAML."""
        template_path = Path("config/prompts.yaml")
        if template_path.exists():
            with open(template_path) as f:
                return yaml.safe_load(f)
        return {}
    
    def build_context(
        self,
        recent_messages: List[Message],
        relevant_memories: List[Message],
        emotional_context: dict,
        sensory_context: str,
        max_tokens: int = 3000
    ) -> List[Message]:
        """Build complete conversation context with token management."""

        # Get the content of the last 15 messages to check against
        recent_content = {msg.content.strip().lower() for msg in recent_messages[-15:]}
        
        unique_memories = []
        for mem in relevant_memories:
            # Extract actual content if it has "UserName:" prefix
            clean_mem = mem.content.split(": ", 1)[-1] if ": " in mem.content else mem.content
            
            # Only add if we haven't seen this exact sentence recently
            if clean_mem.strip().lower() not in recent_content:
                unique_memories.append(mem)

        logger.debug("=== START CONTEXT BUILD ===")
        logger.debug(f"Inputs: {len(recent_messages)} recent msgs, {len(relevant_memories)} memories")
        logger.debug(f"Emotional Context: {emotional_context}")
        
        messages = []
        
        system_content = self._build_system_prompt(
            emotional_context,
            sensory_context,
            relevant_memories
        )
        
        # DEBUG: Log the full system prompt to check for hallucinations/leaks
        logger.debug(f"--- SYSTEM PROMPT PREVIEW ---\n{system_content}\n-----------------------------")

        messages.append(Message(
            role="system",
            content=system_content,
            metadata={}
        ))
        
        token_count = self._estimate_tokens(system_content)
        logger.debug(f"System prompt tokens: ~{token_count}")
        
        selected_messages = []
        dropped_count = 0
        
        # Iterate backwards to keep most recent
        for msg in reversed(recent_messages[-15:]):
            msg_tokens = self._estimate_tokens(msg.content)
            
            if token_count + msg_tokens < max_tokens:
                selected_messages.insert(0, msg)
                token_count += msg_tokens
            else:
                dropped_count += 1
                logger.debug(f"Dropping message due to token limit: '{msg.content[:20]}...'")
                break
        
        messages.extend(selected_messages)
        
        logger.debug(f"Context Built: {len(messages)} total messages. Estimated total tokens: {token_count}")
        logger.debug(f"Dropped {dropped_count} messages from tail.")
        
        # DEBUG: Print the exact conversation flow being sent
        debug_flow = "\n".join([f"[{m.role.upper()}]: {m.content}" for m in messages])
        logger.debug(f"--- FINAL PROMPT FLOW ---\n{debug_flow}\n========================")
        
        return messages

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars for English)."""
        return len(text) // 4
    
    def _build_system_prompt(
        self,
        emotional_context: dict,
        sensory_context: str,
        relevant_memories: List[Message]
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
        if relevant_memories:
            logger.debug(f"Injecting {len(relevant_memories)} memories into system prompt")
            memory_context = "\n\n=== IMPORTANT CONTEXT FROM PAST CONVERSATIONS ===\n"
            memory_context += "Remember and reference these details when relevant:\n\n"
            
            for i, mem in enumerate(relevant_memories[:5], 1):
                # Extract content without "UserName:" prefix if present
                content = mem.content.split(": ", 1)[-1] if ": " in mem.content else mem.content
                memory_context += f"{i}. {content}\n"
            
            memory_context += "\n" + "=" * 50 + "\n"
            memory_context += "☞ Reference these memories naturally when they're relevant to the current conversation.\n"
            memory_context += "☞ If the user mentions something you discussed before, acknowledge it.\n"
        else:
            logger.debug("No relevant memories found for context injection")
    
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

Send a brief, natural message to check in or comment on what you noticed. Keep it casual and appropriate to the situation.
''')
        
        prompt = template.format(
            trigger=trigger_reason,
            mood=emotional_context.get('mood_description', 'neutral')
        )
        
        logger.debug(f"Generated Impulse Prompt:\n{prompt}")
        return prompt
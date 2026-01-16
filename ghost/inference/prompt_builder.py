"""Dynamic prompt builder with context assembly."""

from typing import List, Dict, Any
import logging
from pathlib import Path
import yaml

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
        sensory_context: str
    ) -> List[Message]:
        """Build complete conversation context."""
        messages = []
        
        # System message with dynamic context
        system_content = self._build_system_prompt(
            emotional_context,
            sensory_context,
            relevant_memories
        )
        messages.append(Message(
            role="system",
            content=system_content,
            metadata={}
        ))
        
        # Add recent conversation
        messages.extend(recent_messages[-8:])  # Last 8 messages
        
        return messages
    
    def _build_system_prompt(
        self,
        emotional_context: dict,
        sensory_context: str,
        relevant_memories: List[Message]
    ) -> str:
        """Build dynamic system prompt."""
        base_prompt = self.persona_config.system_prompt
        
        # Add emotional context
        mood_desc = emotional_context.get('mood_description', 'neutral')
        circadian = emotional_context.get('circadian_phase', 'daytime')
        
        emotional_instruction = f"""
Current Emotional State: {mood_desc}
Time Context: {circadian}

Respond naturally according to this emotional state. If you're feeling low energy, keep responses brief. If you're in a good mood, be more expressive.
"""
        
        # Add relevant memories if any
        memory_context = ""
        if relevant_memories:
            memory_context = "\n\nRelevant Past Context:\n"
            for mem in relevant_memories[:3]:  # Top 3 most relevant
                memory_context += f"- {mem.content}\n"
        
        # Combine all parts
        full_prompt = f"""{base_prompt}

{emotional_instruction}

{sensory_context}
{memory_context}

Remember: You are a companion, not an assistant. Respond naturally and personally."""
        
        return full_prompt.strip()
    
    def build_impulse_prompt(
        self,
        trigger_reason: str,
        emotional_context: dict
    ) -> str:
        """Build prompt for autonomous initiation."""
        template = self.templates.get('impulse', {}).get('template', '''
[AUTONOMOUS INITIATION]
You noticed: {trigger}

Your current mood: {mood}

Send a brief, natural message to check in or comment on what you noticed. Keep it casual and appropriate to the situation.
''')
        
        return template.format(
            trigger=trigger_reason,
            mood=emotional_context.get('mood_description', 'neutral')
        )
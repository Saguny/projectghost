import logging
import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from ghost.core.interfaces import Message
from ghost.inference.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


import logging
import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from ghost.core.interfaces import Message
from ghost.inference.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class ThinkOutput:
    intent: str
    emotion: str
    belief_updates: List[Dict[str, str]]
    memory_queries: List[str]
    needs_update: Dict[str, float]
    action_request: Optional[str]
    speech_plan: str
    confidence: float
    reasoning_trace: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, json_str: str) -> "ThinkOutput":
        # 1. Strip Markdown and Code Blocks
        clean_str = re.sub(r'^```json\s*', '', json_str, flags=re.MULTILINE)
        clean_str = re.sub(r'^```\s*', '', clean_str, flags=re.MULTILINE)
        clean_str = re.sub(r'```$', '', clean_str, flags=re.MULTILINE).strip()

        # 2. Aggressive Comment Stripping (// and #)
        clean_str = re.sub(r'//.*', '', clean_str)
        clean_str = re.sub(r'#.*', '', clean_str)

        # 3. Try to find the largest JSON-like structure
        # (Greedy match to capture as much as possible, including broken ends)
        match = re.search(r'\{[\s\S]*', clean_str) 
        if match:
            clean_str = match.group(0)

        try:
            # First Attempt: Direct Parse
            data = json.loads(clean_str)
        except json.JSONDecodeError:
            try:
                # Second Attempt: Repair syntax
                logger.debug("JSON decode error, attempting aggressive repair...")
                repaired = cls._repair_json(clean_str)
                data = json.loads(repaired)
                logger.info("JSON auto-repair successful")
            except Exception as e:
                logger.error(f"JSON parsing failed after repair: {e}")
                return cls._sanity_fallback(json_str)

        return cls(
            intent=data.get("intent", "text_response"),
            emotion=data.get("emotion", "neutral"),
            belief_updates=data.get("belief_updates", []),
            memory_queries=data.get("memory_queries", []),
            needs_update=data.get("needs_update", {}),
            action_request=data.get("action_request"),
            speech_plan=data.get("speech_plan", "continue conversation"),
            confidence=data.get("confidence", 0.5),
            reasoning_trace=data.get("reasoning_trace", "")
        )

    @staticmethod
    def _repair_json(json_str: str) -> str:
        """
        Fixes missing commas, quotes, and unclosed braces.
        """
        # 1. Fix missing commas between key-value pairs
        # Look for "value" "next_key" pattern
        json_str = re.sub(r'(["\d\]\}truefalse])\s*\n\s*"', r'\1,\n"', json_str)
        
        # 2. Fix trailing commas before closing braces
        json_str = re.sub(r',\s*(\}|\])', r'\1', json_str)

        # 3. Balance Braces (The "Cut-off" Fix)
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')

        while open_brackets > close_brackets:
            json_str += ']'
            close_brackets += 1
            
        while open_braces > close_braces:
            json_str += '}'
            close_braces += 1
            
        return json_str

    @classmethod
    def _sanity_fallback(cls, raw_text: str) -> "ThinkOutput":
        # Keep existing fallback logic
        sanitized = re.sub(r'https?://\S+', '', raw_text).strip()
        speech_plan = sanitized[:100] if sanitized else "acknowledge"
        return cls(
            intent="text_response",
            emotion="neutral",
            belief_updates=[],
            memory_queries=[],
            needs_update={},
            action_request=None,
            speech_plan=speech_plan,
            confidence=0.3,
            reasoning_trace=f"Fallback: {len(raw_text)} chars"
        )


class CognitiveCore:
    def __init__(self, ollama_client: OllamaClient, persona_config):
        self.ollama_client = ollama_client
        self.persona_config = persona_config
        self.think_system_prompt = self._build_think_prompt()
        logger.info("Cognitive core initialized (bicameral architecture)")

    async def process(
        self,
        user_input: str,
        context: Dict[str, Any],
        beliefs: Dict[str, Any],
        needs: Dict[str, float]
    ) -> tuple[ThinkOutput, str]:

        # 1. THINK STAGE
        think_output = await self._think_stage(
            user_input=user_input,
            context=context,
            beliefs=beliefs,
            needs=needs
        )

        logger.debug(f"Think intent: {think_output.intent} | Emotion: {think_output.emotion}")

        # 2. SPEAK STAGE
        speech = await self._speak_stage(
            think_output=think_output,
            context=context,
            user_input=user_input
        )

        return think_output, speech

    async def _think_stage(
        self,
        user_input: str,
        context: Dict[str, Any],
        beliefs: Dict[str, Any],
        needs: Dict[str, float]
    ) -> ThinkOutput:

        think_messages = [
            Message(role="system", content=self.think_system_prompt, metadata={}),
            Message(
                role="user",
                content=self._format_think_input(user_input, context, beliefs, needs),
                metadata={}
            )
        ]

        try:
            think_json = await self.ollama_client.generate(
                messages=think_messages,
                temperature=0.3, # Low temp for logic
                max_tokens=600,
                json_mode=True   # Force JSON
            )
            return ThinkOutput.from_json(think_json)

        except Exception as e:
            logger.error(f"Think stage failed: {e}")
            return ThinkOutput(
                intent="error", emotion="confused", belief_updates=[], 
                memory_queries=[], needs_update={}, action_request=None, 
                speech_plan="apologize", confidence=0.0, reasoning_trace=str(e)
            )

    async def _speak_stage(
        self,
        think_output: ThinkOutput,
        context: Dict[str, Any],
        user_input: str
    ) -> str:
        
        # 1. Dynamic System Prompt (Inject the "Thought")
        system_content = (
            f"{self.persona_config.system_prompt}\n\n"
            f"[INTERNAL STATE]\n"
            f"Mood: {think_output.emotion}\n"
            f"Goal: {think_output.speech_plan}\n"
            f"Instruction: Respond naturally to the user. Do NOT mention your internal state."
        )

        messages = [
            Message(role="system", content=system_content, metadata={})
        ]
        
        # 2. FEW-SHOT EXAMPLES (The "How")
        # Fixes personality drift
        if hasattr(self.persona_config, 'examples') and self.persona_config.examples:
            for ex in self.persona_config.examples:
                parts = ex.split("\nAssistant:")
                if len(parts) == 2:
                    u_text = parts[0].replace("User:", "").strip()
                    a_text = parts[1].strip()
                    messages.append(Message(role="user", content=u_text, metadata={"type": "example"}))
                    messages.append(Message(role="assistant", content=a_text, metadata={"type": "example"}))

        # 3. Add Recent Conversation History (Context)
        recent_history = context.get("working", [])[-6:]
        for msg in recent_history:
            if msg.content.strip() != user_input.strip():
                messages.append(Message(
                    role=msg.role,
                    content=msg.content,
                    metadata={}
                ))

        # 4. Add Current User Input
        if not messages or messages[-1].content.strip() != user_input.strip():
             messages.append(Message(
                role="user",
                content=user_input,
                metadata={}
            ))
            
        # 5. PERSONA ANCHOR (The "Glue")
        messages.append(Message(
            role="system", 
            content=f"(Remember: You are {self.persona_config.name}. Speak with {think_output.emotion} energy.)", 
            metadata={"type": "anchor"}
        ))

        try:
            speech = await self.ollama_client.generate(
                messages=messages,
                temperature=self.persona_config.temperature,
                max_tokens=self.persona_config.max_output_tokens,
                stop_tokens=self.persona_config.stop_tokens
            )
            return speech.strip()

        except Exception as e:
            logger.error(f"Speak stage failed: {e}")
            return "..."

    def _format_think_input(
        self,
        user_input: str,
        context: Dict[str, Any],
        beliefs: Dict[str, Any],
        needs: Dict[str, float]
    ) -> str:
        
        # Format beliefs for clarity
        user_facts = []
        self_traits = []
        
        for k, v in beliefs.items():
            if k in ["is_ai", "can_think", "name"] or "likes" in k or "dislikes" in k: 
                self_traits.append(f"- {k}: {v}")
            else:
                user_facts.append(f"- {k}: {v}")

        belief_summary = "KNOWN FACTS (User):\n" + ("\n".join(user_facts[:5]) or "None")
        self_summary = "MY TRAITS (Self):\n" + ("\n".join(self_traits[:5]) or "None")
        
        return f"""USER: {user_input}
{belief_summary}
{self_summary}
NEEDS: {needs}
Analyze and output JSON."""

    def _build_think_prompt(self) -> str:
        return """You are the INTERNAL REASONING SYSTEM.
Output ONLY valid JSON.
{
  "intent": "str",
  "emotion": "str",
  "belief_updates": [{"entity": "agent", "relation": "likes", "value": "x"}],
  "memory_queries": [],
  "needs_update": {},
  "action_request": null,
  "speech_plan": "what to say",
  "confidence": 0.0,
  "reasoning_trace": "str"
}"""
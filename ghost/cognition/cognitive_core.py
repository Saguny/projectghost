"""
Cognitive Core: Bicameral Mind Implementation

Architecture:
    User Input → Think Stage → Validator → Speak Stage → Output
"""

import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from ghost.core.interfaces import Message
from ghost.inference.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class ThinkOutput:
    """Structured output from think stage (internal reasoning)"""
    intent: str
    emotion: str
    belief_updates: List[Dict[str, str]]
    memory_queries: List[str]
    needs_update: Dict[str, float]
    action_request: Optional[str]
    speech_plan: str
    confidence: float

    # Metadata
    reasoning_trace: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, json_str: str) -> "ThinkOutput":
        try:
            cleaned = json_str.strip()

            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            lines = cleaned.split("\n")
            json_lines = []
            for line in lines:
                if line.strip() and not line.strip().startswith("//"):
                    json_lines.append(line)

            cleaned = "\n".join(json_lines)
            data = json.loads(cleaned)

            return cls(
                intent=data.get("intent", "unknown"),
                emotion=data.get("emotion", "neutral"),
                belief_updates=data.get("belief_updates", []),
                memory_queries=data.get("memory_queries", []),
                needs_update=data.get("needs_update", {}),
                action_request=data.get("action_request"),
                speech_plan=data.get("speech_plan", ""),
                confidence=data.get("confidence", 0.5),
                reasoning_trace=data.get("reasoning_trace", "")
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse think output: {e}")
            logger.debug(f"Raw output: {json_str[:200]}...")

            return cls(
                intent="parse_error",
                emotion="confused",
                belief_updates=[],
                memory_queries=[],
                needs_update={},
                action_request=None,
                speech_plan="i had trouble processing that",
                confidence=0.0,
                reasoning_trace=f"Parse error: {e}"
            )


class CognitiveCore:
    """
    Bicameral Mind: Separates reasoning from speech.
    """

    def __init__(self, ollama_client: OllamaClient, persona_config):
        self.ollama_client = ollama_client
        self.persona_config = persona_config

        self.think_system_prompt = self._build_think_prompt()
        self.speak_system_prompt = self._build_speak_prompt()

        logger.info("Cognitive core initialized (bicameral architecture)")

    async def process(
        self,
        user_input: str,
        context: Dict[str, Any],
        beliefs: Dict[str, Any],
        needs: Dict[str, float]
    ) -> tuple[ThinkOutput, str]:

        think_output = await self._think_stage(
            user_input=user_input,
            context=context,
            beliefs=beliefs,
            needs=needs
        )

        logger.debug(
            f"Think output: intent={think_output.intent}, "
            f"confidence={think_output.confidence:.2f}"
        )

        speech = await self._speak_stage(
            think_output=think_output,
            context=context
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
                content=self._format_think_input(
                    user_input=user_input,
                    context=context,
                    beliefs=beliefs,
                    needs=needs
                ),
                metadata={}
            )
        ]

        try:
            think_json = await self.ollama_client.generate(
                messages=think_messages,
                temperature=0.4,
                max_tokens=600,
                stop_tokens=["```", "THINK_END"]
            )

            think_output = ThinkOutput.from_json(think_json)

        except Exception as e:
            logger.error(f"Think stage failed: {e}", exc_info=True)

            think_output = ThinkOutput(
                intent="error",
                emotion="confused",
                belief_updates=[],
                memory_queries=[],
                needs_update={},
                action_request=None,
                speech_plan="acknowledge error gracefully",
                confidence=0.0,
                reasoning_trace=f"Think stage exception: {e}"
            )

        return think_output

    async def _speak_stage(
        self,
        think_output: ThinkOutput,
        context: Dict[str, Any]
    ) -> str:

        speak_messages = [
            Message(role="system", content=self.speak_system_prompt, metadata={}),
            Message(
                role="user",
                content=self._format_speak_input(think_output, context),
                metadata={}
            )
        ]

        try:
            speech = await self.ollama_client.generate(
                messages=speak_messages,
                temperature=self.persona_config.temperature,
                max_tokens=self.persona_config.max_output_tokens,
                stop_tokens=self.persona_config.stop_tokens
            )

            return speech.strip()

        except Exception as e:
            logger.error(f"Speak stage failed: {e}", exc_info=True)
            return "sorry, i'm having trouble thinking right now..."

    def _format_think_input(
        self,
        user_input: str,
        context: Dict[str, Any],
        beliefs: Dict[str, Any],
        needs: Dict[str, float]
    ) -> str:

        memory_context = "\n".join(
            f"- {msg.content}" for msg in context.get("semantic", [])[:3]
        )

        belief_summary = "\n".join(
            f"- {k}: {v}" for k, v in list(beliefs.items())[:5]
        )

        needs_summary = "\n".join(
            f"- {k}: {v:.2f}" for k, v in needs.items()
        )

        return f"""
USER INPUT: "{user_input}"

RECALLED FACTS:
{memory_context or "None"}

CURRENT BELIEFS:
{belief_summary or "None"}

INTERNAL NEEDS:
{needs_summary}

TASK: Analyze this input and output structured reasoning as JSON.
"""

    def _format_speak_input(
        self,
        think_output: ThinkOutput,
        context: Dict[str, Any]
    ) -> str:

        recent = context.get("working", [])[-3:]
        recent_text = "\n".join(
            f"{msg.role}: {msg.content}" for msg in recent
        )

        return f"""
INTERNAL REASONING:
Intent: {think_output.intent}
Emotion: {think_output.emotion}
Speech Plan: {think_output.speech_plan}

RECENT CONVERSATION:
{recent_text}

TASK: Generate natural dialogue based on your internal reasoning.
Stay in character. Use your personality.
"""

    def _build_think_prompt(self) -> str:
        return """
You are the INTERNAL REASONING SYSTEM for an AI agent.

Your job is to THINK, not speak.

Output structured JSON reasoning in this exact format:

{
  "intent": "what user wants",
  "emotion": "detected emotional tone",
  "belief_updates": [
    {"entity": "user", "relation": "likes", "value": "cats"}
  ],
  "memory_queries": ["specific facts to recall"],
  "needs_update": {
    "social": 0.1,
    "energy": -0.05
  },
  "action_request": null,
  "speech_plan": "brief summary of what to say",
  "confidence": 0.8,
  "reasoning_trace": "why you made these decisions"
}

CRITICAL RULES:
- You are NOT speaking to the user
- Output ONLY valid JSON (no markdown, no preamble)
- Be analytical, not conversational
- Focus on facts and logic
- Identify belief updates to store
- Plan speech without generating it
"""

    def _build_speak_prompt(self) -> str:
        base = self.persona_config.system_prompt

        return f"""
{base}

COGNITIVE MODE: SPEAK

You've already done your internal reasoning.
Now generate natural dialogue based on your reasoning output.

Rules:
- Stay in character
- Use your personality
- Reference your internal speech plan
- Be natural and conversational
- Don't mention "internal reasoning"
"""

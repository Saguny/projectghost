"""Unit tests for inference system."""

import pytest
from ghost.inference.prompt_builder import PromptBuilder
from ghost.core.config import PersonaConfig
from ghost.core.interfaces import Message


class TestPromptBuilder:
    """Test prompt builder."""
    
    @pytest.fixture
    def persona_config(self):
        """Create test persona config."""
        return PersonaConfig(
            name="TestBot",
            system_prompt="You are a helpful assistant.",
            temperature=0.8
        )
    
    @pytest.fixture
    def prompt_builder(self, persona_config):
        """Create prompt builder."""
        return PromptBuilder(persona_config)
    
    def test_build_context(self, prompt_builder):
        """Test context building."""
        recent_messages = [
            Message(role="user", content="Hello", metadata={}),
            Message(role="assistant", content="Hi!", metadata={})
        ]
        
        emotional_context = {
            "mood_description": "positive",
            "circadian_phase": "morning"
        }
        
        messages = prompt_builder.build_context(
            recent_messages=recent_messages,
            relevant_memories=[],
            emotional_context=emotional_context,
            sensory_context=""
        )
        
        assert len(messages) >= 2
        assert messages[0].role == "system"
        assert "positive" in messages[0].content.lower()
    
    def test_impulse_prompt(self, prompt_builder):
        """Test impulse prompt building."""
        emotional_context = {"mood_description": "energetic"}
        
        prompt = prompt_builder.build_impulse_prompt(
            trigger_reason="prolonged silence",
            emotional_context=emotional_context
        )
        
        assert "silence" in prompt.lower()
        assert isinstance(prompt, str)
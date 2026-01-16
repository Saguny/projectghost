"""Pytest configuration and fixtures."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil

from ghost.core.config import SystemConfig, PersonaConfig, MemoryConfig, OllamaConfig
from ghost.core.events import EventBus


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_data_dir):
    """Create test configuration."""
    config = SystemConfig()
    config.debug_mode = True
    config.log_level = "DEBUG"
    
    config.memory.vector_db_path = str(temp_data_dir / "vector_db")
    config.memory.episodic_buffer_size = 10
    
    config.persona = PersonaConfig(
        name="TestBot",
        system_prompt="You are a test bot.",
        temperature=0.7
    )
    
    return config


@pytest.fixture
async def event_bus():
    """Create and start event bus."""
    bus = EventBus()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    from ghost.core.interfaces import Message
    
    return [
        Message(role="user", content="Hello", metadata={}),
        Message(role="assistant", content="Hi there!", metadata={}),
        Message(role="user", content="How are you?", metadata={}),
    ]
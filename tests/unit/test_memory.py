"""Unit tests for memory system."""

import pytest
from ghost.memory.episodic_buffer import EpisodicBuffer
from ghost.core.interfaces import Message


class TestEpisodicBuffer:
    """Test episodic buffer."""
    
    def test_initialization(self):
        """Test buffer initialization."""
        buffer = EpisodicBuffer(max_size=5)
        assert buffer.size() == 0
    
    def test_add_message(self):
        """Test adding messages."""
        buffer = EpisodicBuffer(max_size=3)
        
        msg1 = Message(role="user", content="Test 1", metadata={})
        msg2 = Message(role="user", content="Test 2", metadata={})
        
        buffer.add(msg1)
        buffer.add(msg2)
        
        assert buffer.size() == 2
    
    def test_max_size_limit(self):
        """Test max size enforcement."""
        buffer = EpisodicBuffer(max_size=2)
        
        for i in range(5):
            msg = Message(role="user", content=f"Test {i}", metadata={})
            buffer.add(msg)
        
        assert buffer.size() == 2
        recent = buffer.get_recent(limit=10)
        assert recent[-1].content == "Test 4"
    
    def test_get_recent(self):
        """Test getting recent messages."""
        buffer = EpisodicBuffer(max_size=10)
        
        for i in range(5):
            buffer.add(Message(role="user", content=f"Msg {i}", metadata={}))
        
        recent = buffer.get_recent(limit=3)
        assert len(recent) == 3
        assert recent[0].content == "Msg 2"
    
    def test_clear(self):
        """Test clearing buffer."""
        buffer = EpisodicBuffer()
        buffer.add(Message(role="user", content="Test", metadata={}))
        
        buffer.clear()
        assert buffer.size() == 0
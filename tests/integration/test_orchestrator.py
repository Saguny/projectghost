"""Integration tests for orchestrator."""

import pytest
from ghost.core.orchestrator import Orchestrator
from ghost.core.events import EventBus, MessageReceived
from ghost.core.config import SystemConfig
from tests.fixtures.mock_services import (
    MockMemoryProvider,
    MockEmotionProvider,
    MockInferenceEngine,
    MockCryostasisController
)


@pytest.mark.asyncio
class TestOrchestrator:
    """Test orchestrator integration."""
    
    @pytest.fixture
    async def orchestrator(self, test_config):
        """Create orchestrator with mock services."""
        event_bus = EventBus()
        await event_bus.start()
        
        orchestrator = Orchestrator(
            config=test_config,
            event_bus=event_bus,
            memory=MockMemoryProvider(),
            emotion=MockEmotionProvider(),
            inference=MockInferenceEngine("Test response"),
            cryostasis=MockCryostasisController(),
            sensors=[]
        )
        
        yield orchestrator
        await event_bus.stop()
    
    async def test_handle_message(self, orchestrator):
        """Test message handling."""
        event = MessageReceived(
            user_id="123",
            user_name="TestUser",
            content="Hello!",
            channel_id="456"
        )
        
        response = await orchestrator.handle_message(event)
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    async def test_health_check(self, orchestrator):
        """Test health check."""
        health = await orchestrator.health_check()
        
        assert "inference_available" in health
        assert "hibernating" in health
        assert health["inference_available"] is True
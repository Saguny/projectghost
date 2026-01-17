"""Unit tests for autonomy triggers."""

import pytest
from datetime import datetime, timedelta, timezone
from ghost.autonomy.triggers import TriggerEvaluator
from ghost.core.config import AutonomyConfig as TriggerConfig

class TestAutonomyTriggers:
    
    @pytest.fixture
    def trigger_config(self):
        """Create a config for testing impatience."""
        config = TriggerConfig()
        # Set silence threshold to 1 hour for the test
        config.silence_threshold_minutes = 60
        return config

    def test_user_gone_too_long(self, trigger_config):
        """Test if the bot wakes up after prolonged silence."""
        evaluator = TriggerEvaluator(trigger_config)
        
        # --- SCENARIO: User has been silent for 2 hours ---
        # We simulate that the last message was 2 hours ago
        mock_last_message_time = datetime.now(timezone.utc) - timedelta(hours=2)
        
        # Check if she should trigger
        should_trigger, reason = evaluator.should_trigger(
            last_message_time=mock_last_message_time, 
            current_mood={'arousal': 0.5} # She has energy
        )
        
        print(f"\n[Test] Time since last msg: 2 hours")
        print(f"[Test] Threshold: 1 hour")
        print(f"[Result] Should Trigger? {should_trigger} (Reason: {reason})")
        
        assert should_trigger is True
        assert reason == "silence_break"

    def test_user_just_spoke(self, trigger_config):
        """Test that she stays quiet if you just spoke."""
        evaluator = TriggerEvaluator(trigger_config)
        
        # --- SCENARIO: User spoke 5 minutes ago ---
        mock_last_message_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        should_trigger, reason = evaluator.should_trigger(
            last_message_time=mock_last_message_time, 
            current_mood={'arousal': 0.5}
        )
        
        print(f"\n[Test] Time since last msg: 5 mins")
        print(f"[Result] Should Trigger? {should_trigger} (Reason: {reason})")
        
        assert should_trigger is False
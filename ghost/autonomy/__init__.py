"""Autonomy module for proactive AI behavior.

This module enables the AI to initiate conversations based on:
- Prolonged silence detection
- Time-of-day triggers
- Circadian rhythm influence
- Random probability checks

Key Features:
- Configurable silence thresholds
- Circadian-aware proactivity
- Message activity tracking
- Event-driven architecture

Usage:
    from ghost.autonomy import AutonomyEngine, TriggerEvaluator
    from ghost.core.config import AutonomyConfig
    
    config = AutonomyConfig()
    engine = AutonomyEngine(config, event_bus, emotion_service)
    
    await engine.start()  # Begin monitoring
    # Engine will emit ProactiveImpulse events when triggers fire
"""

from ghost.autonomy.autonomy_engine import AutonomyEngine
from ghost.autonomy.triggers import TriggerEvaluator

__all__ = [
    "AutonomyEngine",
    "TriggerEvaluator",
]


def create_autonomy_engine(
    config,
    event_bus,
    emotion_service
) -> AutonomyEngine:
    """Factory function to create a configured autonomy engine.
    
    Args:
        config: AutonomyConfig with trigger settings
        event_bus: EventBus for publishing ProactiveImpulse events
        emotion_service: EmotionService for circadian modifiers
        
    Returns:
        Configured AutonomyEngine (not started)
    """
    return AutonomyEngine(config, event_bus, emotion_service)
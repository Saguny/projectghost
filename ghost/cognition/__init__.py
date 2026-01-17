"""
Cognitive Architecture Module

Components:
    - CognitiveCore: Bicameral mind (Think/Speak separation)
    - Validator: Reality firewall (hallucination prevention)
    - BeliefSystem: Knowledge graph for facts
    - BDIEngine: Belief-Desire-Intention autonomy
    - CognitiveOrchestrator: Main integration layer

Usage:
    from ghost.cognition import CognitiveOrchestrator
    
    orchestrator = CognitiveOrchestrator(
        config=config,
        event_bus=event_bus,
        memory=memory,
        emotion=emotion,
        ollama_client=ollama_client,
        cryostasis=cryostasis,
        sensors=sensors
    )
"""

from ghost.cognition.cognitive_orchestrator import CognitiveOrchestrator
from ghost.cognition.cognitive_core import CognitiveCore, ThinkOutput
from ghost.cognition.validator import RealityValidator, ValidationResult
from ghost.cognition.belief_system import BeliefSystem
from ghost.cognition.bdi_engine import BDIEngine, Need, Intention

__all__ = [
    # Main orchestrator
    "CognitiveOrchestrator",
    
    # Core components
    "CognitiveCore",
    "ThinkOutput",
    "RealityValidator",
    "ValidationResult",
    "BeliefSystem",
    "BDIEngine",
    "Need",
    "Intention",
]
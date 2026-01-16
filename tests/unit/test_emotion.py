"""Unit tests for emotion system."""

import pytest
from ghost.emotion.pad_model import PADModel
from ghost.emotion.circadian import CircadianRhythm
from ghost.core.interfaces import EmotionalState


class TestPADModel:
    """Test PAD emotional model."""
    
    def test_initialization(self):
        """Test PAD model initialization."""
        model = PADModel(initial_pleasure=0.5, initial_arousal=0.7, initial_dominance=0.3)
        state = model.get_state()
        
        assert state.pleasure == 0.5
        assert state.arousal == 0.7
        assert state.dominance == 0.3
    
    def test_update(self):
        """Test state update."""
        model = PADModel()
        state = model.update(pleasure_delta=0.2, arousal_delta=-0.1, dominance_delta=0.0)
        
        assert state.pleasure > 0.6  # Initial + delta - decay
        assert state.arousal < 0.7
    
    def test_clamping(self):
        """Test value clamping."""
        model = PADModel(initial_pleasure=0.9)
        state = model.update(pleasure_delta=0.5, arousal_delta=0.0, dominance_delta=0.0)
        
        assert state.pleasure <= 1.0
        assert state.pleasure >= -1.0
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis."""
        model = PADModel()
        
        deltas = model.analyze_sentiment("I love this! So happy!")
        assert deltas[0] > 0  # Pleasure should increase
        
        deltas = model.analyze_sentiment("This is terrible and frustrating")
        assert deltas[0] < 0  # Pleasure should decrease


class TestCircadianRhythm:
    """Test circadian rhythm."""
    
    def test_phase_description(self):
        """Test phase description generation."""
        rhythm = CircadianRhythm()
        phase = rhythm.get_phase_description()
        
        assert isinstance(phase, str)
        assert len(phase) > 0
    
    def test_emotional_influence(self):
        """Test emotional influence calculation."""
        rhythm = CircadianRhythm()
        influence = rhythm.get_emotional_influence()
        
        assert 'pleasure' in influence
        assert 'arousal' in influence
        assert 'dominance' in influence
    
    def test_proactivity_modifier(self):
        """Test proactivity modifier."""
        rhythm = CircadianRhythm()
        modifier = rhythm.get_proactivity_modifier()
        
        assert 0.0 <= modifier <= 1.0
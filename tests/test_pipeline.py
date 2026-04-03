"""Integration tests for affect-wave pipeline.

These tests verify the complete flow from input to output.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from affect_wave.affect.embedding import EmbeddingResult
from affect_wave.affect.inference import AffectInference, InferenceContext
from affect_wave.state.schemas import (
    EmotionScore,
    AppraisalScores,
    Trend,
    create_affect_state,
)
from affect_wave.wave.converter import convert_to_wave_parameter, render_wave_text


class TestAffectPipeline:
    """Tests for the complete affect inference pipeline."""

    def test_create_affect_state_pipeline(self):
        """Should create valid affect state from raw inputs."""
        # Simulate inference output
        emotions = [
            EmotionScore(name="joy", score=0.75),
            EmotionScore(name="curiosity", score=0.45),
            EmotionScore(name="calm", score=0.30),
        ]
        appraisal = AppraisalScores(
            social_reward=0.6,
            uncertainty=0.2,
        )
        trend = Trend(valence=0.4, arousal=0.5, stability=0.7)
        embedding = [0.1] * 1024

        state = create_affect_state(
            top_emotions=emotions,
            appraisal=appraisal,
            trend=trend,
            affect_embedding=embedding,
        )

        # Verify state structure
        assert len(state.top_emotions) == 3
        assert state.top_emotions[0].name == "joy"
        assert state.compact_state.dominant == "joy"
        assert -1.0 <= state.trend.valence <= 1.0

        # Verify dict conversion
        state_dict = state.to_dict()
        assert "turn_id" in state_dict
        assert "top_emotions" in state_dict

    def test_wave_conversion_pipeline(self):
        """Should convert affect state to wave parameter."""
        state = create_affect_state(
            top_emotions=[
                EmotionScore(name="joy", score=0.8),
                EmotionScore(name="curiosity", score=0.5),
            ],
            appraisal=AppraisalScores(social_reward=0.6),
            trend=Trend(valence=0.5, arousal=0.6, stability=0.8),
            affect_embedding=[0.1] * 512,
        )

        wave = convert_to_wave_parameter(state)

        # All values in range
        assert 0.0 <= wave.amplitude <= 1.0
        assert 0.0 <= wave.frequency <= 1.0
        assert 0.0 <= wave.jitter <= 1.0
        assert 0.0 <= wave.glow <= 1.0
        assert 0.0 <= wave.afterglow <= 1.0
        assert 0.0 <= wave.density <= 1.0

    def test_wave_rendering_pipeline(self):
        """Should render wave parameter to text."""
        state = create_affect_state(
            top_emotions=[EmotionScore(name="joy", score=0.7)],
            appraisal=AppraisalScores(),
            trend=Trend(valence=0.5, arousal=0.6),
            affect_embedding=[0.1] * 256,
        )

        wave = convert_to_wave_parameter(state)

        # Wave mode
        wave_text = render_wave_text(wave, mode="wave")
        assert isinstance(wave_text, str)
        assert len(wave_text) > 0

        # Params mode
        params_text = render_wave_text(wave, mode="params")
        import json
        params = json.loads(params_text)
        assert "amplitude" in params

    def test_deterministic_pipeline(self):
        """Should produce same output for same input."""
        state = create_affect_state(
            top_emotions=[
                EmotionScore(name="curiosity", score=0.7),
                EmotionScore(name="calm", score=0.4),
            ],
            appraisal=AppraisalScores(uncertainty=0.3),
            trend=Trend(valence=0.2, arousal=0.4),
            affect_embedding=[0.1, 0.2, 0.3],
        )

        wave1 = convert_to_wave_parameter(state)
        wave2 = convert_to_wave_parameter(state)

        assert wave1.amplitude == wave2.amplitude
        assert wave1.frequency == wave2.frequency
        assert wave1.glow == wave2.glow


class TestContractValidation:
    """Tests for contract requirements."""

    def test_top_emotions_exactly_three(self):
        """top_emotions must always have exactly 3 items."""
        # With 1 input
        state = create_affect_state(
            top_emotions=[EmotionScore(name="joy", score=0.8)],
            appraisal=AppraisalScores(),
            trend=Trend(),
            affect_embedding=[],
        )
        assert len(state.top_emotions) == 3

        # With 5 inputs (should truncate)
        state = create_affect_state(
            top_emotions=[
                EmotionScore(name=f"e{i}", score=0.9 - i * 0.1)
                for i in range(5)
            ],
            appraisal=AppraisalScores(),
            trend=Trend(),
            affect_embedding=[],
        )
        assert len(state.top_emotions) == 3

    def test_valence_range(self):
        """valence must be in -1.0 to 1.0 range."""
        for valence in [-0.8, 0.0, 0.5, 0.9]:
            trend = Trend(valence=valence)
            assert -1.0 <= trend.valence <= 1.0, f"valence {valence} out of range"

    def test_stability_enum_values(self):
        """stability must be low/medium/high."""
        from affect_wave.state.schemas import StabilityLevel, CompactState

        for stability in [StabilityLevel.LOW, StabilityLevel.MEDIUM, StabilityLevel.HIGH]:
            compact = CompactState(
                dominant="calm",
                tone="test",
                stability=stability,
            )
            assert compact.stability in [
                StabilityLevel.LOW,
                StabilityLevel.MEDIUM,
                StabilityLevel.HIGH,
            ]

    def test_wave_parameter_six_keys(self):
        """wave_parameter must have all 6 required keys."""
        state = create_affect_state(
            top_emotions=[EmotionScore(name="calm", score=0.5)],
            appraisal=AppraisalScores(),
            trend=Trend(),
            affect_embedding=[],
        )

        wave = convert_to_wave_parameter(state)
        d = wave.to_dict()

        required_keys = ["amplitude", "frequency", "jitter", "glow", "afterglow", "density"]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"
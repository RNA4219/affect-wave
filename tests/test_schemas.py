"""Tests for affect_wave state schemas."""

import pytest

from affect_wave.state.schemas import (
    EmotionScore,
    AppraisalScores,
    Trend,
    CompactState,
    RiskFlags,
    AffectState,
    WaveParameter,
    StabilityLevel,
    create_affect_state,
)


class TestWaveParameter:
    """Tests for WaveParameter."""

    def test_default_values(self):
        """Default values should be in valid range."""
        wave = WaveParameter()
        assert 0.0 <= wave.amplitude <= 1.0
        assert 0.0 <= wave.frequency <= 1.0
        assert 0.0 <= wave.jitter <= 1.0
        assert 0.0 <= wave.glow <= 1.0
        assert 0.0 <= wave.afterglow <= 1.0
        assert 0.0 <= wave.density <= 1.0

    def test_clamp_all(self):
        """Clamp should constrain all values to 0-1."""
        wave = WaveParameter(
            amplitude=1.5,
            frequency=-0.3,
            jitter=2.0,
            glow=-0.5,
            afterglow=0.8,
            density=0.5,
        )
        wave.clamp_all()
        assert wave.amplitude == 1.0
        assert wave.frequency == 0.0
        assert wave.jitter == 1.0
        assert wave.glow == 0.0
        assert wave.afterglow == 0.8
        assert wave.density == 0.5

    def test_to_dict(self):
        """to_dict should return properly rounded values."""
        wave = WaveParameter(amplitude=0.123456)
        d = wave.to_dict()
        assert d["amplitude"] == 0.123
        assert isinstance(d, dict)


class TestAffectState:
    """Tests for AffectState."""

    def test_top_emotions_sorting(self):
        """top_emotions should be sorted by score descending."""
        state = create_affect_state(
            top_emotions=[
                EmotionScore(name="calm", score=0.3),
                EmotionScore(name="joy", score=0.8),
                EmotionScore(name="curiosity", score=0.5),
            ],
            appraisal=AppraisalScores(),
            trend=Trend(),
            affect_embedding=[0.1, 0.2],
        )
        assert len(state.top_emotions) == 3
        assert state.top_emotions[0].name == "joy"
        assert state.top_emotions[0].score == 0.8
        assert state.top_emotions[1].name == "curiosity"
        assert state.top_emotions[2].name == "calm"

    def test_top_emotions_fixed_count(self):
        """Should always have exactly 3 emotions."""
        state = create_affect_state(
            top_emotions=[
                EmotionScore(name="joy", score=0.8),
            ],
            appraisal=AppraisalScores(),
            trend=Trend(),
            affect_embedding=[0.1, 0.2],
        )
        assert len(state.top_emotions) == 3
        # Should fill with calm
        assert state.top_emotions[1].name == "calm"
        assert state.top_emotions[2].name == "calm"

    def test_valence_range(self):
        """valence should be in -1.0 to 1.0 range."""
        trend = Trend(valence=0.5)
        assert -1.0 <= trend.valence <= 1.0

        trend2 = Trend(valence=-0.7)
        assert -1.0 <= trend2.valence <= 1.0

    def test_stability_level_enum(self):
        """stability should only accept defined enum values."""
        compact = CompactState(
            dominant="curiosity",
            tone="calm_stable",
            stability=StabilityLevel.MEDIUM,
        )
        assert compact.stability == StabilityLevel.MEDIUM
        assert compact.stability in [StabilityLevel.LOW, StabilityLevel.MEDIUM, StabilityLevel.HIGH]

    def test_to_dict_structure(self):
        """to_dict should have all required keys."""
        state = create_affect_state(
            top_emotions=[
                EmotionScore(name="curiosity", score=0.7),
                EmotionScore(name="calm", score=0.4),
                EmotionScore(name="joy", score=0.2),
            ],
            appraisal=AppraisalScores(threat=0.1, uncertainty=0.5),
            trend=Trend(valence=0.3, arousal=0.6),
            affect_embedding=[0.1, 0.2, 0.3],
        )
        d = state.to_dict()

        assert "turn_id" in d
        assert "timestamp" in d
        assert "top_emotions" in d
        assert "appraisal" in d
        assert "trend" in d
        assert "compact_state" in d

        # Check top_emotions structure
        assert len(d["top_emotions"]) == 3
        assert all("name" in e and "score" in e for e in d["top_emotions"])


class TestCompactState:
    """Tests for CompactState."""

    def test_required_fields(self):
        """Should have all required fields."""
        compact = CompactState(
            dominant="curiosity",
            tone="soft_rising",
            stability=StabilityLevel.HIGH,
        )
        assert compact.dominant == "curiosity"
        assert compact.tone == "soft_rising"
        assert compact.stability == StabilityLevel.HIGH

    def test_to_dict(self):
        """to_dict should use enum value."""
        compact = CompactState(
            dominant="joy",
            tone="rising_expansive",
            stability=StabilityLevel.LOW,
        )
        d = compact.to_dict()
        assert d["stability"] == "low"
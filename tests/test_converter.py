"""Tests for wave parameter converter."""

import pytest

from affect_wave.state.schemas import (
    AffectState,
    EmotionScore,
    AppraisalScores,
    Trend,
    RiskFlags,
    CompactState,
    StabilityLevel,
)
from affect_wave.wave.converter import convert_to_wave_parameter, render_wave_text


class TestWaveConverter:
    """Tests for wave parameter conversion."""

    def test_deterministic_conversion(self):
        """Same affect_state should produce same wave_parameter."""
        state = AffectState(
            turn_id="test-1",
            timestamp=None,
            top_emotions=[
                EmotionScore(name="curiosity", score=0.7),
                EmotionScore(name="calm", score=0.4),
                EmotionScore(name="joy", score=0.2),
            ],
            appraisal=AppraisalScores(
                threat=0.1,
                uncertainty=0.5,
                social_reward=0.6,
            ),
            trend=Trend(
                valence=0.3,
                arousal=0.6,
                stability=0.7,
            ),
        )

        wave1 = convert_to_wave_parameter(state)
        wave2 = convert_to_wave_parameter(state)

        assert wave1.amplitude == wave2.amplitude
        assert wave1.frequency == wave2.frequency
        assert wave1.jitter == wave2.jitter
        assert wave1.glow == wave2.glow
        assert wave1.afterglow == wave2.afterglow
        assert wave1.density == wave2.density

    def test_values_in_range(self):
        """All wave values should be in 0-1 range."""
        state = AffectState(
            turn_id="test-2",
            timestamp=None,
            top_emotions=[
                EmotionScore(name="anger", score=0.9),
                EmotionScore(name="fear", score=0.8),
                EmotionScore(name="tension", score=0.7),
            ],
            appraisal=AppraisalScores(
                threat=0.9,
                uncertainty=0.9,
                goal_blockage=0.8,
            ),
            trend=Trend(
                valence=-0.8,
                arousal=0.9,
                stability=0.1,
            ),
        )

        wave = convert_to_wave_parameter(state)

        assert 0.0 <= wave.amplitude <= 1.0
        assert 0.0 <= wave.frequency <= 1.0
        assert 0.0 <= wave.jitter <= 1.0
        assert 0.0 <= wave.glow <= 1.0
        assert 0.0 <= wave.afterglow <= 1.0
        assert 0.0 <= wave.density <= 1.0

    def test_amplitude_follows_arousal(self):
        """Amplitude should generally follow arousal."""
        low_arousal_state = AffectState(
            turn_id="test-low",
            timestamp=None,
            top_emotions=[EmotionScore(name="calm", score=0.8)],
            appraisal=AppraisalScores(),
            trend=Trend(arousal=0.2, valence=0.0),
        )

        high_arousal_state = AffectState(
            turn_id="test-high",
            timestamp=None,
            top_emotions=[EmotionScore(name="joy", score=0.8)],
            appraisal=AppraisalScores(),
            trend=Trend(arousal=0.8, valence=0.0),
        )

        low_wave = convert_to_wave_parameter(low_arousal_state)
        high_wave = convert_to_wave_parameter(high_arousal_state)

        assert high_wave.amplitude > low_wave.amplitude

    def test_glow_follows_positive_valence(self):
        """Glow should increase with positive valence."""
        negative_state = AffectState(
            turn_id="neg",
            timestamp=None,
            top_emotions=[EmotionScore(name="sadness", score=0.7)],
            appraisal=AppraisalScores(),
            trend=Trend(valence=-0.6, arousal=0.3),
        )

        positive_state = AffectState(
            turn_id="pos",
            timestamp=None,
            top_emotions=[EmotionScore(name="joy", score=0.7)],
            appraisal=AppraisalScores(social_reward=0.5),
            trend=Trend(valence=0.6, arousal=0.3),
        )

        neg_wave = convert_to_wave_parameter(negative_state)
        pos_wave = convert_to_wave_parameter(positive_state)

        assert pos_wave.glow > neg_wave.glow

    def test_jitter_follows_instability(self):
        """Jitter should increase with low stability."""
        stable_state = AffectState(
            turn_id="stable",
            timestamp=None,
            top_emotions=[EmotionScore(name="calm", score=0.8)],
            appraisal=AppraisalScores(uncertainty=0.1),
            trend=Trend(stability=0.9, arousal=0.3),
            risk_flags=RiskFlags(instability=0.1),
        )

        unstable_state = AffectState(
            turn_id="unstable",
            timestamp=None,
            top_emotions=[EmotionScore(name="fear", score=0.7)],
            appraisal=AppraisalScores(uncertainty=0.8),
            trend=Trend(stability=0.2, arousal=0.7),
            risk_flags=RiskFlags(instability=0.8),
        )

        stable_wave = convert_to_wave_parameter(stable_state)
        unstable_wave = convert_to_wave_parameter(unstable_state)

        assert unstable_wave.jitter > stable_wave.jitter


class TestWaveRenderer:
    """Tests for wave text rendering."""

    def test_wave_mode_returns_string(self):
        """Wave mode should return a string."""
        from affect_wave.state.schemas import WaveParameter

        wave = WaveParameter(amplitude=0.5, frequency=0.5)
        result = render_wave_text(wave, mode="wave")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_params_mode_returns_json(self):
        """Params mode should return valid JSON."""
        import json
        from affect_wave.state.schemas import WaveParameter

        wave = WaveParameter(
            amplitude=0.62,
            frequency=0.31,
        )
        result = render_wave_text(wave, mode="params")

        # Should be valid JSON
        parsed = json.loads(result)
        assert "amplitude" in parsed
        assert "frequency" in parsed

    def test_wave_display_includes_glow_prefix(self):
        """High glow should add glow prefix."""
        from affect_wave.state.schemas import WaveParameter

        wave = WaveParameter(glow=0.7)
        result = render_wave_text(wave, mode="wave")

        # ASCII safe glow marker
        assert "*" in result

    def test_wave_display_includes_jitter(self):
        """High jitter should add irregularity."""
        from affect_wave.state.schemas import WaveParameter

        wave = WaveParameter(jitter=0.5)
        result = render_wave_text(wave, mode="wave")

        # Should have mixed wave characters
        assert "^" in result or ":" in result or "!" in result

    def test_wave_rendering_changes_for_distinct_inputs(self):
        """Distinct wave parameters should not collapse to identical strings."""
        from affect_wave.state.schemas import WaveParameter

        calm_wave = WaveParameter(
            amplitude=0.45,
            frequency=0.4,
            jitter=0.15,
            glow=0.62,
            afterglow=0.7,
            density=0.35,
        )
        unstable_wave = WaveParameter(
            amplitude=0.62,
            frequency=0.8,
            jitter=0.93,
            glow=0.2,
            afterglow=0.12,
            density=0.82,
        )

        calm_result = render_wave_text(calm_wave, mode="wave")
        unstable_result = render_wave_text(unstable_wave, mode="wave")

        assert calm_result != unstable_result

    def test_density_hint_changes_with_sparse_vs_packed_wave(self):
        """Density extremes should render different textual hints."""
        from affect_wave.state.schemas import WaveParameter

        sparse_wave = WaveParameter(
            amplitude=0.35,
            frequency=0.35,
            jitter=0.18,
            glow=0.3,
            afterglow=0.2,
            density=0.12,
        )
        packed_wave = WaveParameter(
            amplitude=0.65,
            frequency=0.72,
            jitter=0.74,
            glow=0.35,
            afterglow=0.3,
            density=0.9,
        )

        sparse_result = render_wave_text(sparse_wave, mode="wave")
        packed_result = render_wave_text(packed_wave, mode="wave")

        assert sparse_result != packed_result
        assert "/ spare" in sparse_result
        assert "/ packed" in packed_result

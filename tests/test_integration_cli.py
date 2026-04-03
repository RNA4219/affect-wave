"""Tests for CLI adapter with state store (no LLM generation)."""

import pytest
from datetime import datetime, timezone

from affect_wave.adapters.cli import CLIAdapter
from affect_wave.state.schemas import AffectState, WaveParameter, EmotionScore, AppraisalScores, Trend
from affect_wave.config import Config


class TestCLIAdapterWithState:
    """Tests for CLI adapter state operations."""

    def test_cli_adapter_inspect_flow(self):
        """Should inspect stored turns."""
        config = Config()
        adapter = CLIAdapter(config)

        # Store a turn
        state = AffectState(
            turn_id="turn-test",
            timestamp=datetime.now(timezone.utc),
            top_emotions=[EmotionScore(name="joy", score=0.8)],
            appraisal=AppraisalScores(),
            trend=Trend(),
        )
        wave = WaveParameter(amplitude=0.5)

        adapter.state_store.store_turn("Hi", "Hello", state, wave)

        # Inspect
        result = adapter.inspect("turn-test")
        assert result is not None
        assert result["turn_id"] == "turn-test"
        assert result["user_message"] == "Hi"

    def test_cli_adapter_render_flow(self):
        """Should render wave parameter."""
        config = Config()
        adapter = CLIAdapter(config)

        # Store a turn
        state = AffectState(
            turn_id="turn-1",
            timestamp=datetime.now(timezone.utc),
            top_emotions=[EmotionScore(name="calm", score=0.7)],
            appraisal=AppraisalScores(),
            trend=Trend(),
        )
        wave = WaveParameter(amplitude=0.6, glow=0.8)
        adapter.state_store.store_turn("Hi", "Hello", state, wave)

        # Render wave mode
        wave_result = adapter.render("wave")
        assert wave_result is not None
        assert isinstance(wave_result, str)

        # Render params mode (returns None since it's string output)
        params_result = adapter.render("params")
        assert params_result is not None
        import json
        params = json.loads(params_result)
        assert "amplitude" in params

    def test_cli_get_recent_turns(self):
        """Should get recent turns."""
        config = Config()
        adapter = CLIAdapter(config)

        # Store multiple turns
        for i in range(5):
            state = AffectState(
                turn_id=f"turn-{i}",
                timestamp=datetime.now(timezone.utc),
                top_emotions=[EmotionScore(name="calm", score=0.5)],
                appraisal=AppraisalScores(),
                trend=Trend(),
            )
            adapter.state_store.store_turn(f"Q{i}", f"A{i}", state, WaveParameter())

        turns = adapter.get_recent_turns(3)
        assert len(turns) == 3

    def test_cli_clear_history(self):
        """Should clear all history."""
        config = Config()
        adapter = CLIAdapter(config)

        # Add some data
        state = AffectState(
            turn_id="turn-1",
            timestamp=datetime.now(timezone.utc),
            top_emotions=[EmotionScore(name="calm", score=0.5)],
            appraisal=AppraisalScores(),
            trend=Trend(),
        )
        adapter.state_store.store_turn("Hi", "Hello", state, WaveParameter())

        # Clear
        adapter.clear_history()

        assert len(adapter.state_store.turns) == 0


class TestCLIAdapterErrorHandling:
    """Tests for CLI adapter error handling."""

    def test_cli_inspect_nonexistent(self):
        """Should return None for nonexistent turn."""
        config = Config()
        adapter = CLIAdapter(config)

        result = adapter.inspect("nonexistent-turn")
        assert result is None

    def test_cli_render_empty(self):
        """Should return None when no turns to render."""
        config = Config()
        adapter = CLIAdapter(config)

        result = adapter.render("wave")
        assert result is None


class TestCLIAdapterConfiguration:
    """Tests for CLI adapter configuration."""

    def test_cli_adapter_with_custom_settings(self, tmp_path):
        """Should use custom configuration."""
        config = Config(
            state_log_enabled=True,
            state_log_path=tmp_path / "test-log.jsonl",
        )
        adapter = CLIAdapter(config)

        assert adapter.config.state_log_enabled is True
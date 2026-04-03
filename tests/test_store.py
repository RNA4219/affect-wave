"""Tests for state store."""

import pytest
from pathlib import Path
import json

from affect_wave.state.store import StateStore, StoredTurn
from affect_wave.state.schemas import (
    AffectState,
    WaveParameter,
    EmotionScore,
    AppraisalScores,
    Trend,
    CompactState,
    StabilityLevel,
)
from affect_wave.config import Config, StateLogMode


class TestStateStore:
    """Tests for StateStore."""

    def test_empty_store(self):
        """Should start empty."""
        config = Config()
        store = StateStore(config)
        assert len(store.turns) == 0

    def test_store_turn(self):
        """Should store a turn."""
        config = Config()
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-001",
            timestamp=None,
            top_emotions=[
                EmotionScore(name="joy", score=0.8),
            ],
            appraisal=AppraisalScores(),
            trend=Trend(),
            compact_state=CompactState(
                dominant="joy",
                tone="happy",
                stability=StabilityLevel.HIGH,
            ),
        )
        wave = WaveParameter(amplitude=0.5)

        turn = store.store_turn(
            user_message="Hello",
            assistant_message="Hi there",
            affect_state=state,
            wave_parameter=wave,
        )

        assert turn.turn_id == "turn-001"
        assert len(store.turns) == 1

    def test_get_turn(self):
        """Should get turn by ID."""
        config = Config()
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-123",
            timestamp=None,
            top_emotions=[EmotionScore(name="calm", score=0.5)],
            appraisal=AppraisalScores(),
            trend=Trend(),
        )
        wave = WaveParameter()

        store.store_turn("Hi", "Hello", state, wave)

        found = store.get_turn("turn-123")
        assert found is not None
        assert found.user_message == "Hi"

        # Not found
        assert store.get_turn("nonexistent") is None

    def test_get_latest_turn(self):
        """Should get most recent turn."""
        config = Config()
        store = StateStore(config)

        # Store multiple turns
        for i in range(3):
            state = AffectState(
                turn_id=f"turn-{i}",
                timestamp=None,
                top_emotions=[EmotionScore(name="calm", score=0.5)],
                appraisal=AppraisalScores(),
                trend=Trend(),
            )
            store.store_turn(f"Q{i}", f"A{i}", state, WaveParameter())

        latest = store.get_latest_turn()
        assert latest is not None
        assert latest.turn_id == "turn-2"

    def test_get_latest_turn_empty(self):
        """Should return None when empty."""
        config = Config()
        store = StateStore(config)
        assert store.get_latest_turn() is None

    def test_get_recent_turns(self):
        """Should get recent turns."""
        config = Config()
        store = StateStore(config)

        for i in range(5):
            state = AffectState(
                turn_id=f"turn-{i}",
                timestamp=None,
                top_emotions=[EmotionScore(name="calm", score=0.5)],
                appraisal=AppraisalScores(),
                trend=Trend(),
            )
            store.store_turn(f"Q{i}", f"A{i}", state, WaveParameter())

        recent = store.get_recent_turns(3)
        assert len(recent) == 3
        # Most recent first
        assert recent[0].turn_id == "turn-4"

    def test_get_prev_state_for_inference(self):
        """Should get previous state for inference."""
        config = Config()
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-1",
            timestamp=None,
            top_emotions=[EmotionScore(name="joy", score=0.7)],
            appraisal=AppraisalScores(),
            trend=Trend(valence=0.5),
        )
        store.store_turn("Hi", "Hello", state, WaveParameter())

        prev = store.get_prev_state_for_inference()
        assert prev is not None
        assert prev.trend.valence == 0.5

    def test_clear(self):
        """Should clear all turns."""
        config = Config()
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-1",
            timestamp=None,
            top_emotions=[EmotionScore(name="calm", score=0.5)],
            appraisal=AppraisalScores(),
            trend=Trend(),
        )
        store.store_turn("Hi", "Hello", state, WaveParameter())

        store.clear()
        assert len(store.turns) == 0

    def test_trim_turns(self):
        """Should trim old turns."""
        config = Config()
        store = StateStore(config)
        store.max_turns = 5

        for i in range(10):
            state = AffectState(
                turn_id=f"turn-{i}",
                timestamp=None,
                top_emotions=[EmotionScore(name="calm", score=0.5)],
                appraisal=AppraisalScores(),
                trend=Trend(),
            )
            store.store_turn(f"Q{i}", f"A{i}", state, WaveParameter())

        assert len(store.turns) <= 5


class TestStateStoreLogging:
    """Tests for state logging."""

    def test_log_disabled(self, tmp_path: Path):
        """Should not log when disabled."""
        config = Config(
            state_log_enabled=False,
            state_log_path=tmp_path / "test.jsonl",
        )
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-1",
            timestamp=None,
            top_emotions=[EmotionScore(name="calm", score=0.5)],
            appraisal=AppraisalScores(),
            trend=Trend(),
        )
        store.store_turn("Hi", "Hello", state, WaveParameter())

        # No log file created
        assert not (tmp_path / "test.jsonl").exists()

    def test_log_enabled(self, tmp_path: Path):
        """Should log when enabled."""
        from datetime import datetime, timezone

        config = Config(
            state_log_enabled=True,
            state_log_path=tmp_path / "test.jsonl",
        )
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-1",
            timestamp=datetime.now(timezone.utc),
            top_emotions=[EmotionScore(name="joy", score=0.8)],
            appraisal=AppraisalScores(),
            trend=Trend(valence=0.5),
        )
        store.store_turn("Hi", "Hello", state, WaveParameter())

        # Log file created
        log_path = tmp_path / "test.jsonl"
        assert log_path.exists()

        # Verify content
        with open(log_path) as f:
            entry = json.loads(f.readline())
            assert entry["turn_id"] == "turn-1"
            assert "affect_state" in entry
            assert "wave_parameter" in entry

    def test_log_preview_mode(self, tmp_path: Path):
        """Should write message previews in preview mode."""
        config = Config(
            state_log_enabled=True,
            state_log_mode=StateLogMode.PREVIEW,
            state_log_path=tmp_path / "preview.jsonl",
        )
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-preview",
            timestamp=None,
            top_emotions=[EmotionScore(name="joy", score=0.8)],
            appraisal=AppraisalScores(),
            trend=Trend(valence=0.5),
        )
        store.store_turn("Hello user", "Hello assistant", state, WaveParameter())

        entry = json.loads((tmp_path / "preview.jsonl").read_text().splitlines()[0])
        assert "user_message_preview" in entry
        assert "assistant_message_preview" in entry
        assert "user_message" not in entry

    def test_log_redacted_mode(self, tmp_path: Path):
        """Should redact message bodies in redacted mode."""
        config = Config(
            state_log_enabled=True,
            state_log_mode=StateLogMode.REDACTED,
            state_log_path=tmp_path / "redacted.jsonl",
        )
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-redacted",
            timestamp=None,
            top_emotions=[EmotionScore(name="joy", score=0.8)],
            appraisal=AppraisalScores(),
            trend=Trend(valence=0.5),
        )
        store.store_turn("Hello user", "Hello assistant", state, WaveParameter())

        entry = json.loads((tmp_path / "redacted.jsonl").read_text().splitlines()[0])
        assert entry["user_message_redacted"] is True
        assert entry["assistant_message_redacted"] is True
        assert "user_message_preview" not in entry

    def test_log_full_mode(self, tmp_path: Path):
        """Should write full messages in full mode."""
        config = Config(
            state_log_enabled=True,
            state_log_mode=StateLogMode.FULL,
            state_log_path=tmp_path / "full.jsonl",
        )
        store = StateStore(config)

        state = AffectState(
            turn_id="turn-full",
            timestamp=None,
            top_emotions=[EmotionScore(name="joy", score=0.8)],
            appraisal=AppraisalScores(),
            trend=Trend(valence=0.5),
        )
        store.store_turn("Hello user", "Hello assistant", state, WaveParameter())

        entry = json.loads((tmp_path / "full.jsonl").read_text().splitlines()[0])
        assert entry["user_message"] == "Hello user"
        assert entry["assistant_message"] == "Hello assistant"

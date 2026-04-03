"""Test configuration."""

import pytest


@pytest.fixture
def sample_prototypes_dir(tmp_path):
    """Create sample prototype files for testing."""
    import json

    proto_dir = tmp_path / "prototypes"
    proto_dir.mkdir()

    # Emotion labels
    emotion_data = {
        "version": "1.0",
        "updated_at": "2026-04-03",
        "labels": [
            {"id": "emotion-curiosity", "label": "curiosity", "text": "interested", "valence_hint": 0.3, "arousal_hint": 0.5},
            {"id": "emotion-calm", "label": "calm", "text": "peaceful", "valence_hint": 0.2, "arousal_hint": 0.2},
            {"id": "emotion-joy", "label": "joy", "text": "happy", "valence_hint": 0.7, "arousal_hint": 0.5},
            {"id": "emotion-sadness", "label": "sadness", "text": "sad", "valence_hint": -0.6, "arousal_hint": 0.2},
        ]
    }
    (proto_dir / "emotion-labels.json").write_text(json.dumps(emotion_data))

    # Appraisal axes
    appraisal_data = {
        "version": "1.0",
        "axes": [
            {"id": "appraisal-threat", "label": "threat", "text": "danger", "direction": "negative"},
            {"id": "appraisal-uncertainty", "label": "uncertainty", "text": "uncertain", "direction": "neutral"},
        ]
    }
    (proto_dir / "appraisal-axes.json").write_text(json.dumps(appraisal_data))

    # Affect axes
    affect_data = {
        "version": "1.0",
        "axes": [
            {"id": "valence-pos", "label": "valence_positive", "text": "good", "direction": 1.0},
            {"id": "valence-neg", "label": "valence_negative", "text": "bad", "direction": -1.0},
        ]
    }
    (proto_dir / "affect-axes.json").write_text(json.dumps(affect_data))

    return proto_dir
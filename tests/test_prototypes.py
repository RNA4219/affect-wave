"""Tests for prototype loading."""

from pathlib import Path
import pytest

from affect_wave.config import Config
from affect_wave.affect.prototypes import (
    load_all_prototypes,
    load_emotion_prototypes,
    load_appraisal_prototypes,
    load_affect_prototypes,
)


class TestPrototypeLoading:
    """Tests for prototype file loading."""

    def test_load_emotion_prototypes(self, tmp_path: Path):
        """Should load emotion prototypes from JSON."""
        emotion_file = tmp_path / "emotion-labels.json"
        emotion_file.write_text("""{
            "version": "1.0",
            "updated_at": "2026-04-03",
            "labels": [
                {"id": "emotion-joy", "label": "joy", "text": "happy"},
                {"id": "emotion-calm", "label": "calm", "text": "peaceful"}
            ]
        }""")

        prototypes = load_emotion_prototypes(emotion_file)

        assert len(prototypes) == 2
        assert prototypes[0].id == "emotion-joy"
        assert prototypes[0].label == "joy"
        assert prototypes[0].text == "happy"
        assert prototypes[1].label == "calm"

    def test_load_appraisal_prototypes(self, tmp_path: Path):
        """Should load appraisal prototypes from JSON."""
        appraisal_file = tmp_path / "appraisal-axes.json"
        appraisal_file.write_text("""{
            "version": "1.0",
            "axes": [
                {"id": "appraisal-threat", "label": "threat", "text": "danger"}
            ]
        }""")

        prototypes = load_appraisal_prototypes(appraisal_file)

        assert len(prototypes) == 1
        assert prototypes[0].label == "threat"

    def test_load_all_prototypes(self, tmp_path: Path):
        """Should load all prototypes from config."""
        # Create all prototype files
        (tmp_path / "emotion-labels.json").write_text("""{
            "version": "1.0",
            "updated_at": "2026-04-03",
            "labels": [{"id": "e1", "label": "joy", "text": "happy"}]
        }""")
        (tmp_path / "appraisal-axes.json").write_text("""{
            "version": "1.0",
            "axes": [{"id": "a1", "label": "threat", "text": "danger"}]
        }""")
        (tmp_path / "affect-axes.json").write_text("""{
            "version": "1.0",
            "axes": [{"id": "v1", "label": "valence_positive", "text": "good"}]
        }""")

        config = Config(prototypes_dir=tmp_path)
        data = load_all_prototypes(config)

        assert len(data.emotions) == 1
        assert len(data.appraisals) == 1
        assert len(data.affect_axes) == 1
        assert data.version == "1.0"

    def test_get_canonical_labels(self, tmp_path: Path):
        """Should return list of canonical emotion labels."""
        (tmp_path / "emotion-labels.json").write_text("""{
            "version": "1.0",
            "labels": [
                {"id": "e1", "label": "joy", "text": "happy"},
                {"id": "e2", "label": "calm", "text": "peaceful"}
            ]
        }""")
        (tmp_path / "appraisal-axes.json").write_text('{"axes": []}')
        (tmp_path / "affect-axes.json").write_text('{"axes": []}')

        config = Config(prototypes_dir=tmp_path)
        data = load_all_prototypes(config)

        labels = data.get_canonical_labels()
        assert labels == ["joy", "calm"]

    def test_get_emotion_by_label(self, tmp_path: Path):
        """Should find emotion by label."""
        (tmp_path / "emotion-labels.json").write_text("""{
            "version": "1.0",
            "labels": [
                {"id": "e1", "label": "curiosity", "text": "interested"}
            ]
        }""")
        (tmp_path / "appraisal-axes.json").write_text('{"axes": []}')
        (tmp_path / "affect-axes.json").write_text('{"axes": []}')

        config = Config(prototypes_dir=tmp_path)
        data = load_all_prototypes(config)

        emotion = data.get_emotion_by_label("curiosity")
        assert emotion is not None
        assert emotion.id == "e1"

        # Non-existent label
        assert data.get_emotion_by_label("unknown") is None


class TestPrototypeFiles:
    """Tests for actual prototype files in data/prototypes."""

    @pytest.fixture
    def prototypes_dir(self) -> Path:
        """Get the actual prototypes directory."""
        return Path(__file__).parent.parent / "data" / "prototypes"

    def test_emotion_labels_exists(self, prototypes_dir: Path):
        """emotion-labels.json should exist."""
        emotion_file = prototypes_dir / "emotion-labels.json"
        assert emotion_file.exists()

        prototypes = load_emotion_prototypes(emotion_file)

        # Should have all 8 canonical emotions
        labels = [p.label for p in prototypes]
        expected = ["curiosity", "calm", "tension", "joy", "sadness", "anger", "fear", "surprise"]
        assert all(e in labels for e in expected)

    def test_appraisal_axes_exists(self, prototypes_dir: Path):
        """appraisal-axes.json should exist."""
        appraisal_file = prototypes_dir / "appraisal-axes.json"
        assert appraisal_file.exists()

        prototypes = load_appraisal_prototypes(appraisal_file)

        # Should have required appraisal axes
        labels = [p.label for p in prototypes]
        required = ["threat", "uncertainty", "goal_blockage", "social_reward"]
        assert all(r in labels for r in required)

    def test_affect_axes_exists(self, prototypes_dir: Path):
        """affect-axes.json should exist."""
        affect_file = prototypes_dir / "affect-axes.json"
        assert affect_file.exists()

        prototypes = load_affect_prototypes(affect_file)

        # Should have valence and arousal axes
        labels = [p.label for p in prototypes]
        assert any("valence" in l for l in labels)
        assert any("arousal" in l for l in labels)
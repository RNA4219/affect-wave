"""Prototype data loading and management."""

from dataclasses import dataclass
from pathlib import Path
import json

from affect_wave.config import Config


@dataclass
class EmotionPrototype:
    """Single emotion prototype definition."""
    id: str
    label: str
    text: str
    valence_hint: float = 0.0
    arousal_hint: float = 0.5


@dataclass
class ConceptPrototype:
    """Fine-grained emotion concept definition."""
    id: str
    label: str
    text: str
    canonical: str  # Maps to one of 8 canonical labels


@dataclass
class AppraisalPrototype:
    """Single appraisal axis prototype definition."""
    id: str
    label: str
    text: str
    direction: str = "neutral"


@dataclass
class AffectPrototype:
    """Single affect axis prototype definition."""
    id: str
    label: str
    text: str
    direction: float = 0.0


@dataclass
class PrototypeData:
    """All prototype definitions."""

    emotions: list[EmotionPrototype]
    concepts: list[ConceptPrototype]  # 171 fine-grained concepts
    concept_to_canonical: dict[str, str]  # concept_id -> canonical label
    appraisals: list[AppraisalPrototype]
    affect_axes: list[AffectPrototype]

    version: str = "1.0"
    updated_at: str = ""

    def get_emotion_by_label(self, label: str) -> EmotionPrototype | None:
        """Get emotion prototype by label.

        Args:
            label: Emotion label to find.

        Returns:
            EmotionPrototype or None if not found.
        """
        for e in self.emotions:
            if e.label == label:
                return e
        return None

    def get_canonical_labels(self) -> list[str]:
        """Get list of canonical emotion labels.

        Returns:
            List of emotion label strings.
        """
        return [e.label for e in self.emotions]

    def get_concepts_by_canonical(self, canonical: str) -> list[ConceptPrototype]:
        """Get all concepts that map to a canonical label.

        Args:
            canonical: Canonical label (e.g., 'joy').

        Returns:
            List of ConceptPrototype objects.
        """
        return [c for c in self.concepts if c.canonical == canonical]


def load_emotion_prototypes(path: Path) -> list[EmotionPrototype]:
    """Load emotion prototypes from JSON file.

    Args:
        path: Path to emotion-labels.json.

    Returns:
        List of EmotionPrototype objects.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    prototypes = []
    for item in data.get("labels", []):
        prototypes.append(EmotionPrototype(
            id=item.get("id", ""),
            label=item.get("label", ""),
            text=item.get("text", ""),
            valence_hint=item.get("valence_hint", 0.0),
            arousal_hint=item.get("arousal_hint", 0.5),
        ))
    return prototypes


def load_appraisal_prototypes(path: Path) -> list[AppraisalPrototype]:
    """Load appraisal prototypes from JSON file.

    Args:
        path: Path to appraisal-axes.json.

    Returns:
        List of AppraisalPrototype objects.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    prototypes = []
    for item in data.get("axes", []):
        prototypes.append(AppraisalPrototype(
            id=item.get("id", ""),
            label=item.get("label", ""),
            text=item.get("text", ""),
            direction=item.get("direction", "neutral"),
        ))
    return prototypes


def load_affect_prototypes(path: Path) -> list[AffectPrototype]:
    """Load affect axis prototypes from JSON file.

    Args:
        path: Path to affect-axes.json.

    Returns:
        List of AffectPrototype objects.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    prototypes = []
    for item in data.get("axes", []):
        prototypes.append(AffectPrototype(
            id=item.get("id", ""),
            label=item.get("label", ""),
            text=item.get("text", ""),
            direction=item.get("direction", 0.0),
        ))
    return prototypes


def load_concept_prototypes(path: Path) -> list[ConceptPrototype]:
    """Load fine-grained emotion concepts from JSON file.

    Args:
        path: Path to emotion-concepts-171.json.

    Returns:
        List of ConceptPrototype objects.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    prototypes = []
    for item in data.get("concepts", []):
        prototypes.append(ConceptPrototype(
            id=item.get("id", ""),
            label=item.get("label", ""),
            text=item.get("text", ""),
            canonical=item.get("canonical", ""),
        ))
    return prototypes


def load_concept_mapping(path: Path) -> dict[str, str]:
    """Load concept-to-canonical mapping from JSON file.

    Args:
        path: Path to concept-to-canonical-map.json.

    Returns:
        Dict mapping concept_id to canonical label.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return data.get("mapping", {})


def load_all_prototypes(config: Config) -> PrototypeData:
    """Load all prototype definitions from configuration.

    Args:
        config: Application configuration with prototypes_dir.

    Returns:
        PrototypeData with all prototypes loaded.

    Raises:
        FileNotFoundError: If prototype files are missing.
    """
    base_dir = config.prototypes_dir

    emotions_path = base_dir / "emotion-labels.json"
    appraisals_path = base_dir / "appraisal-axes.json"
    affect_path = base_dir / "affect-axes.json"
    concepts_path = base_dir / "emotion-concepts-171.json"
    mapping_path = base_dir / "concept-to-canonical-map.json"

    # Load emotion file to get version/updated_at
    with open(emotions_path, encoding="utf-8") as f:
        emotion_data = json.load(f)

    # Load concepts and mapping (optional, fallback to empty if not found)
    concepts = []
    mapping = {}
    try:
        if concepts_path.exists():
            concepts = load_concept_prototypes(concepts_path)
        if mapping_path.exists():
            mapping = load_concept_mapping(mapping_path)
    except (json.JSONDecodeError, KeyError):
        pass  # Use empty defaults

    return PrototypeData(
        emotions=load_emotion_prototypes(emotions_path),
        concepts=concepts,
        concept_to_canonical=mapping,
        appraisals=load_appraisal_prototypes(appraisals_path),
        affect_axes=load_affect_prototypes(affect_path),
        version=emotion_data.get("version", "1.0"),
        updated_at=emotion_data.get("updated_at", ""),
    )
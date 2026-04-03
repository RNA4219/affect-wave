"""Data schemas for affect_state and wave_parameter."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Literal
import uuid


class StabilityLevel(str, Enum):
    """Stability level for compact_state."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class EmotionScore:
    """Single emotion with score."""

    name: str
    score: float  # 0.0 to 1.0

    def to_dict(self) -> dict:
        """Convert to dict format."""
        return {"name": self.name, "score": self.score}


@dataclass
class ConceptScore:
    """Fine-grained concept score for 171 concept bank."""

    concept_id: str
    label: str
    canonical: str  # Maps to one of 8 canonical labels
    score: float  # 0.0 to 1.0

    def to_dict(self) -> dict:
        """Convert to dict format (matches docs specification)."""
        return {
            "id": self.concept_id,
            "label": self.label,
            "canonical": self.canonical,
            "score": self.score,
        }


@dataclass
class AppraisalScores:
    """Appraisal axis scores."""

    threat: float = 0.0  # 0.0 to 1.0
    uncertainty: float = 0.0
    goal_blockage: float = 0.0
    social_reward: float = 0.0
    novelty: float = 0.0
    control: float = 0.0


@dataclass
class Trend:
    """Trend values for affect state."""

    valence: float = 0.0  # -1.0 to 1.0
    arousal: float = 0.0  # 0.0 to 1.0
    stability: float = 0.5  # 0.0 to 1.0
    drift: float = 0.0
    momentum: float = 0.0


@dataclass
class CompactState:
    """Compact state for next turn feedback."""

    dominant: str  # emotion label
    tone: str  # tone descriptor
    stability: StabilityLevel

    def to_dict(self) -> dict:
        """Convert to dict format."""
        return {
            "dominant": self.dominant,
            "tone": self.tone,
            "stability": self.stability.value,
        }


@dataclass
class RiskFlags:
    """Risk indicators."""

    instability: float = 0.0
    negative_drift: bool = False
    high_arousal: bool = False


@dataclass
class AffectState:
    """Complete affect state for a turn."""

    turn_id: str
    timestamp: datetime
    top_emotions: list[EmotionScore]  # Always 3 items, sorted by score desc
    concept_scores: list[ConceptScore] = field(default_factory=list)  # 171 concepts
    appraisal: AppraisalScores = field(default_factory=AppraisalScores)
    trend: Trend = field(default_factory=Trend)
    affect_embedding: list[float] = field(default_factory=list)
    risk_flags: RiskFlags = field(default_factory=RiskFlags)
    compact_state: CompactState = field(default_factory=lambda: CompactState(
        dominant="calm",
        tone="neutral",
        stability=StabilityLevel.MEDIUM,
    ))

    def to_dict(self) -> dict:
        """Convert to dict for JSON output."""
        return {
            "turn_id": self.turn_id,
            "timestamp": self.timestamp.isoformat(),
            "top_emotions": [
                {"name": e.name, "score": round(e.score, 3)}
                for e in self.top_emotions
            ],
            "concept_count": len(self.concept_scores),
            "appraisal": {
                "threat": round(self.appraisal.threat, 3),
                "uncertainty": round(self.appraisal.uncertainty, 3),
                "goal_blockage": round(self.appraisal.goal_blockage, 3),
                "social_reward": round(self.appraisal.social_reward, 3),
                "novelty": round(self.appraisal.novelty, 3),
                "control": round(self.appraisal.control, 3),
            },
            "trend": {
                "valence": round(self.trend.valence, 3),
                "arousal": round(self.trend.arousal, 3),
                "stability": round(self.trend.stability, 3),
            },
            "affect_embedding": [round(v, 3) for v in self.affect_embedding[:8]],
            "risk_flags": {
                "instability": round(self.risk_flags.instability, 3),
            },
            "compact_state": self.compact_state.to_dict(),
        }

    def get_concept_scores_for_debug(self) -> list[dict]:
        """Get all concept scores for debug output.

        Returns:
            List of concept score dicts with id, label, canonical, score.
        """
        return [cs.to_dict() for cs in self.concept_scores]


@dataclass
class WaveParameter:
    """Wave parameter for UI rendering."""

    amplitude: float = 0.5  # 0.0 to 1.0
    frequency: float = 0.5
    jitter: float = 0.0
    glow: float = 0.5
    afterglow: float = 0.5
    density: float = 0.5

    def to_dict(self) -> dict:
        """Convert to dict for JSON output."""
        return {
            "amplitude": round(self.amplitude, 3),
            "frequency": round(self.frequency, 3),
            "jitter": round(self.jitter, 3),
            "glow": round(self.glow, 3),
            "afterglow": round(self.afterglow, 3),
            "density": round(self.density, 3),
        }

    def clamp_all(self) -> None:
        """Clamp all values to 0.0-1.0 range."""
        self.amplitude = max(0.0, min(1.0, self.amplitude))
        self.frequency = max(0.0, min(1.0, self.frequency))
        self.jitter = max(0.0, min(1.0, self.jitter))
        self.glow = max(0.0, min(1.0, self.glow))
        self.afterglow = max(0.0, min(1.0, self.afterglow))
        self.density = max(0.0, min(1.0, self.density))


def create_affect_state(
    top_emotions: list[EmotionScore],
    concept_scores: list[ConceptScore] | None = None,
    appraisal: AppraisalScores | None = None,
    trend: Trend | None = None,
    affect_embedding: list[float] | None = None,
    prev_state: AffectState | None = None,
) -> AffectState:
    """Create affect state with proper compact_state generation.

    Args:
        top_emotions: List of emotion scores (will be trimmed to top 3).
        concept_scores: List of 171 concept scores (optional).
        appraisal: Appraisal scores.
        trend: Trend values.
        affect_embedding: Affect embedding vector.
        prev_state: Previous state for continuity (optional).

    Returns:
        AffectState with turn_id and timestamp.
    """
    # Ensure exactly 3 emotions, sorted by score
    sorted_emotions = sorted(top_emotions, key=lambda e: e.score, reverse=True)[:3]

    # Fill missing slots with calm if needed
    while len(sorted_emotions) < 3:
        sorted_emotions.append(EmotionScore(name="calm", score=0.1))

    # Determine dominant emotion
    dominant = sorted_emotions[0].name if sorted_emotions else "calm"

    # Default values
    if appraisal is None:
        appraisal = AppraisalScores()
    if trend is None:
        trend = Trend()
    if affect_embedding is None:
        affect_embedding = []

    # Determine stability level
    if trend.stability < 0.3:
        stability_level = StabilityLevel.LOW
    elif trend.stability > 0.7:
        stability_level = StabilityLevel.HIGH
    else:
        stability_level = StabilityLevel.MEDIUM

    # Determine tone based on valence and arousal
    if trend.valence > 0.3:
        if trend.arousal > 0.5:
            tone = "rising_expansive"
        else:
            tone = "soft_positive"
    elif trend.valence < -0.3:
        if trend.arousal > 0.5:
            tone = "tense_contracted"
        else:
            tone = "dull_negative"
    else:
        if trend.arousal > 0.5:
            tone = "alert_neutral"
        else:
            tone = "calm_stable"

    # Risk flags
    risk_flags = RiskFlags(
        instability=max(0.0, 1.0 - trend.stability),
        negative_drift=trend.valence < -0.3,
        high_arousal=trend.arousal > 0.7,
    )

    return AffectState(
        turn_id=f"turn-{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(timezone.utc),
        top_emotions=sorted_emotions,
        concept_scores=concept_scores or [],
        appraisal=appraisal,
        trend=trend,
        affect_embedding=affect_embedding,
        risk_flags=risk_flags,
        compact_state=CompactState(
            dominant=dominant,
            tone=tone,
            stability=stability_level,
        ),
    )
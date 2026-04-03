"""Affect inference using prototype similarity."""

from dataclasses import dataclass
import math

from affect_wave.affect.embedding import EmbeddingClient, EmbeddingResult
from affect_wave.affect.prototypes import (
    PrototypeData,
    EmotionPrototype,
    ConceptPrototype,
    AppraisalPrototype,
    AffectPrototype,
)
from affect_wave.state.schemas import (
    AffectState,
    EmotionScore,
    ConceptScore,
    AppraisalScores,
    Trend,
    create_affect_state,
)


@dataclass
class InferenceContext:
    """Context for affect inference."""

    user_message: str
    assistant_message: str
    conversation_context: str
    prev_state: AffectState | None = None


class AffectInference:
    """Affect inference engine using prototype similarity."""

    def __init__(
        self,
        embedding_client: EmbeddingClient,
        prototypes: PrototypeData,
    ):
        """Initialize affect inference.

        Args:
            embedding_client: Client for embedding retrieval.
            prototypes: Prototype definitions.
        """
        self.embedding_client = embedding_client
        self.prototypes = prototypes

        # Cache prototype embeddings
        self._prototype_embeddings: dict[str, list[float]] = {}
        self._concept_embeddings: dict[str, list[float]] = {}

    async def initialize(self) -> None:
        """Pre-compute prototype embeddings for efficiency."""
        # Get embeddings for all emotion prototypes
        for emotion in self.prototypes.emotions:
            emb = await self.embedding_client.get_embedding(emotion.text)
            self._prototype_embeddings[emotion.id] = emb.embedding

        # Get embeddings for appraisal prototypes
        for appraisal in self.prototypes.appraisals:
            emb = await self.embedding_client.get_embedding(appraisal.text)
            self._prototype_embeddings[appraisal.id] = emb.embedding

        # Get embeddings for affect prototypes
        for affect in self.prototypes.affect_axes:
            emb = await self.embedding_client.get_embedding(affect.text)
            self._prototype_embeddings[affect.id] = emb.embedding

        # Get embeddings for all 171 concepts
        for concept in self.prototypes.concepts:
            emb = await self.embedding_client.get_embedding(concept.text)
            self._concept_embeddings[concept.id] = emb.embedding

    async def infer(self, context: InferenceContext) -> AffectState:
        """Infer affect state from conversation context.

        Args:
            context: Inference context with messages.

        Returns:
            AffectState with inferred values.
        """
        # Combine context for embedding
        full_context = self._build_embedding_context(context)
        emb_result = await self.embedding_client.get_embedding(full_context)
        embedding = emb_result.embedding

        # Compute concept scores (171 concepts)
        concept_scores = self._compute_concept_scores(embedding)
        cue_scores = self._compute_textual_cues(context)

        # Compute emotion scores by aggregating concepts and refining with
        # direct canonical prototypes so buckets with many concepts do not
        # dominate every scene.
        direct_emotion_scores = self._compute_emotion_scores(embedding)
        emotion_scores = self._aggregate_to_emotions(concept_scores, direct_emotion_scores, cue_scores)

        # Compute appraisal scores
        appraisal_scores = self._compute_appraisal_scores(embedding)
        emotion_scores = self._apply_label_calibration(emotion_scores, cue_scores, appraisal_scores)

        # Compute trend
        trend = self._compute_trend(
            embedding,
            emotion_scores,
            appraisal_scores,
            context.prev_state,
        )

        # Create affect state
        return create_affect_state(
            top_emotions=emotion_scores,
            concept_scores=concept_scores,
            appraisal=appraisal_scores,
            trend=trend,
            affect_embedding=embedding,
            prev_state=context.prev_state,
        )

    def _build_embedding_context(self, context: InferenceContext) -> str:
        """Build text context for embedding.

        Args:
            context: Inference context.

        Returns:
            Combined text for embedding.
        """
        parts = []

        if context.conversation_context:
            parts.append(context.conversation_context)

        parts.append(f"User: {context.user_message}")
        parts.append(f"Assistant: {context.assistant_message}")

        return "\n".join(parts)

    def _compute_concept_scores(self, embedding: list[float]) -> list[ConceptScore]:
        """Compute concept scores for all 171 concepts.

        Args:
            embedding: Input embedding vector.

        Returns:
            List of ConceptScore objects for all concepts.
        """
        scores = []

        for concept in self.prototypes.concepts:
            concept_emb = self._concept_embeddings.get(concept.id)
            if concept_emb:
                similarity = cosine_similarity(embedding, concept_emb)
                # Normalize similarity to 0-1 range
                score = max(0.0, min(1.0, (similarity + 1.0) / 2.0))

                # Use mapping file as source of truth for canonical label
                canonical = self.prototypes.concept_to_canonical.get(concept.id, concept.canonical)

                scores.append(ConceptScore(
                    concept_id=concept.id,
                    label=concept.label,
                    canonical=canonical,
                    score=score,
                ))

        # Sort by score descending
        scores.sort(key=lambda c: c.score, reverse=True)

        return scores

    def _aggregate_to_emotions(
        self,
        concept_scores: list[ConceptScore],
        direct_emotion_scores: list[EmotionScore] | None = None,
        cue_scores: dict[str, float] | None = None,
    ) -> list[EmotionScore]:
        """Aggregate concept scores to canonical emotion scores.

        Args:
            concept_scores: List of concept scores.
            direct_emotion_scores: Direct prototype scores for canonical labels.

        Returns:
            List of EmotionScore objects (top 3).
        """
        # Aggregate by canonical label using peak-sensitive weighted top-k and
        # bucket-size normalization. This preserves strong local concepts,
        # reduces flattening caused by large concept counts, and then blends a
        # smaller amount of direct canonical prototype evidence.
        canonical_scores: dict[str, list[float]] = {}
        for cs in concept_scores:
            if cs.canonical not in canonical_scores:
                canonical_scores[cs.canonical] = []
            canonical_scores[cs.canonical].append(cs.score)

        direct_lookup = {
            score.name: score.score
            for score in (direct_emotion_scores or [])
        }
        emotion_scores = []
        for canonical, scores in canonical_scores.items():
            ranked = sorted(scores, reverse=True)
            top1 = ranked[0]
            top3_mean = sum(ranked[:3]) / min(3, len(ranked))
            top5_mean = sum(ranked[:5]) / min(5, len(ranked))
            local_mass = sum(max(0.0, score - 0.64) for score in ranked[:8])
            local_mass = min(1.0, local_mass / 1.6)
            bucket_size = len(ranked)
            bucket_penalty = min(0.18, max(0.0, (bucket_size - 18) * 0.008))
            sharp_gap = max(0.0, top1 - top3_mean)
            direct_score = direct_lookup.get(canonical, 0.0)
            cue_score = (cue_scores or {}).get(canonical, 0.0)

            aggregate_score = (
                top1 * 0.33 +
                top3_mean * 0.18 +
                top5_mean * 0.09 +
                local_mass * 0.22 +
                sharp_gap * 0.10 +
                direct_score * 0.12 +
                cue_score * 0.12 -
                bucket_penalty
            )
            emotion_scores.append(EmotionScore(name=canonical, score=aggregate_score))

        # Sort by score descending
        emotion_scores.sort(key=lambda e: e.score, reverse=True)

        # Return top 3
        return emotion_scores[:3]

    def _compute_textual_cues(self, context: InferenceContext) -> dict[str, float]:
        """Extract lightweight lexical cues from the current turn.

        This is a small nudge on top of embeddings so explicit affect words in
        Japanese or English can break ties in ambiguous literary passages.
        """
        text = " ".join(
            part for part in [
                context.user_message,
                context.assistant_message,
                context.conversation_context,
            ]
            if part
        ).lower()

        cue_map = {
            "anger": ["怒", "怒り", "憤", "苛立", "激怒", "呆れ", "憎", "resent", "fury", "frustrat", "betray"],
            "sadness": ["悲", "哀", "悔", "後悔", "羞恥", "恥", "淋", "寂", "喪", "remorse", "regret", "shame", "guilt", "loss"],
            "fear": ["恐", "怖", "不安", "怯", "震", "panic", "terror", "fear", "dread", "threat"],
            "tension": ["緊張", "張り", "焦", "揺", "不安定", "conflict", "ambival", "strain", "tense", "ためら", "迷"],
            "surprise": ["驚", "突然", "意外", "shock", "surpris", "epiphany"],
            "curiosity": ["知り", "問い", "探", "考え", "分析", "不思議", "inquire", "curious", "analy", "wonder"],
            "calm": ["静", "穏", "平静", "落ち着", "安ら", "安心", "満足", "足る", "calm", "steady", "peace"],
            "joy": ["喜", "希望", "嬉", "楽", "ありがたい", "ありがた", "hope", "joy", "warmth", "love", "trust"],
        }

        scores = {label: 0.0 for label in cue_map}
        for label, markers in cue_map.items():
            hits = sum(1 for marker in markers if marker in text)
            if hits:
                base = 0.06 if label in {"surprise", "anger"} else 0.08
                gain = 0.035 if label in {"surprise", "anger"} else 0.05
                scores[label] = min(1.0, base + hits * gain)
        return scores

    def _apply_label_calibration(
        self,
        emotion_scores: list[EmotionScore],
        cue_scores: dict[str, float],
        appraisal_scores: AppraisalScores,
    ) -> list[EmotionScore]:
        """Apply lightweight calibration to reduce persistent label bias."""
        gains = {
            "joy": 1.08,
            "calm": 1.10,
            "sadness": 1.06,
            "curiosity": 1.02,
            "tension": 1.00,
            "fear": 0.98,
            "anger": 0.94,
            "surprise": 0.90,
        }

        calibrated: list[EmotionScore] = []
        for emotion in emotion_scores:
            score = emotion.score * gains.get(emotion.name, 1.0)
            cue = cue_scores.get(emotion.name, 0.0)
            if cue > 0.0:
                score += cue * 0.18
            elif emotion.name in {"anger", "surprise"}:
                score -= 0.035

            if emotion.name == "calm" and appraisal_scores.threat < 0.48 and appraisal_scores.uncertainty < 0.56:
                score += 0.04
            if emotion.name == "joy" and appraisal_scores.social_reward > 0.45:
                score += 0.035
            if emotion.name == "sadness" and appraisal_scores.goal_blockage > 0.45:
                score += 0.03

            calibrated.append(EmotionScore(name=emotion.name, score=max(0.0, min(1.0, score))))

        calibrated.sort(key=lambda e: e.score, reverse=True)
        return calibrated[:3]

    def _compute_emotion_scores(self, embedding: list[float]) -> list[EmotionScore]:
        """Compute emotion scores via prototype similarity.

        Args:
            embedding: Input embedding vector.

        Returns:
            List of EmotionScore objects.
        """
        scores = []

        for emotion in self.prototypes.emotions:
            proto_emb = self._prototype_embeddings.get(emotion.id)
            if proto_emb:
                similarity = cosine_similarity(embedding, proto_emb)
                # Normalize similarity to 0-1 range
                score = max(0.0, min(1.0, (similarity + 1.0) / 2.0))
                scores.append(EmotionScore(name=emotion.label, score=score))

        # Sort by score descending
        scores.sort(key=lambda e: e.score, reverse=True)

        return scores

    def _compute_appraisal_scores(self, embedding: list[float]) -> AppraisalScores:
        """Compute appraisal scores via prototype similarity.

        Args:
            embedding: Input embedding vector.

        Returns:
            AppraisalScores object.
        """
        scores = {}
        appraisal_labels = [
            "threat", "uncertainty", "goal_blockage",
            "social_reward", "novelty", "control",
        ]

        for appraisal in self.prototypes.appraisals:
            proto_emb = self._prototype_embeddings.get(appraisal.id)
            if proto_emb:
                similarity = cosine_similarity(embedding, proto_emb)
                # Normalize to 0-1
                score = max(0.0, min(1.0, (similarity + 1.0) / 2.0))
                scores[appraisal.label] = score

        # Fill missing values
        for label in appraisal_labels:
            if label not in scores:
                scores[label] = 0.0

        return AppraisalScores(
            threat=scores["threat"],
            uncertainty=scores["uncertainty"],
            goal_blockage=scores["goal_blockage"],
            social_reward=scores["social_reward"],
            novelty=scores["novelty"],
            control=scores["control"],
        )

    def _compute_trend(
        self,
        embedding: list[float],
        emotion_scores: list[EmotionScore],
        appraisal_scores: AppraisalScores,
        prev_state: AffectState | None,
    ) -> Trend:
        """Compute trend values from embedding and context.

        Args:
            embedding: Input embedding.
            emotion_scores: Emotion scores.
            appraisal_scores: Appraisal scores.
            prev_state: Previous affect state.

        Returns:
            Trend object.
        """
        # Compute valence from affect axes prototypes
        valence_pos_emb = self._prototype_embeddings.get("affect-valence-positive")
        valence_neg_emb = self._prototype_embeddings.get("affect-valence-negative")

        valence = 0.0
        if valence_pos_emb and valence_neg_emb:
            pos_sim = cosine_similarity(embedding, valence_pos_emb)
            neg_sim = cosine_similarity(embedding, valence_neg_emb)
            # Valence: difference between positive and negative similarity
            valence = (pos_sim - neg_sim) / 2.0

        # Blend concept-derived polarity so scene differences are less compressed.
        concept_valence = self._compute_concept_valence(emotion_scores)
        valence = valence * 0.55 + concept_valence * 0.45
        valence = max(-1.0, min(1.0, valence))

        # Compute arousal from affect axes prototypes
        arousal_high_emb = self._prototype_embeddings.get("affect-arousal-high")
        arousal_low_emb = self._prototype_embeddings.get("affect-arousal-low")

        arousal = 0.5
        if arousal_high_emb and arousal_low_emb:
            high_sim = cosine_similarity(embedding, arousal_high_emb)
            low_sim = cosine_similarity(embedding, arousal_low_emb)
            arousal = (high_sim - low_sim + 1.0) / 2.0
            arousal = max(0.0, min(1.0, arousal))

        # Stability starts from the current concept/emotion distribution even on
        # the first turn, so isolated comparisons do not collapse to 0.0.
        stability = self._compute_intrinsic_stability(emotion_scores, appraisal_scores)
        if prev_state:
            stability = prev_state.trend.stability * 0.45 + stability * 0.55
            if appraisal_scores.uncertainty > 0.65:
                stability -= 0.06
            if appraisal_scores.threat > 0.65:
                stability -= 0.08
            stability = max(0.0, min(1.0, stability))

        # Drift: change in valence from previous
        drift = 0.0
        if prev_state:
            drift = valence - prev_state.trend.valence

        return Trend(
            valence=valence,
            arousal=arousal,
            stability=stability,
            drift=drift,
            momentum=abs(drift) if prev_state else 0.0,
        )

    def _compute_intrinsic_stability(
        self,
        emotion_scores: list[EmotionScore],
        appraisal_scores: AppraisalScores,
    ) -> float:
        """Estimate current stability from score shape and appraisal pressure."""
        if not emotion_scores:
            return 0.5

        ranked = sorted(emotion_scores, key=lambda e: e.score, reverse=True)[:3]
        top_score = ranked[0].score
        second_score = ranked[1].score if len(ranked) > 1 else 0.0
        third_score = ranked[2].score if len(ranked) > 2 else 0.0

        gap = max(0.0, top_score - second_score)
        concentration = min(1.0, (top_score * 0.7 + gap * 1.2))
        tail_pressure = max(0.0, third_score - 0.55) * 0.8
        appraisal_pressure = (
            appraisal_scores.uncertainty * 0.35 +
            appraisal_scores.threat * 0.25 +
            appraisal_scores.goal_blockage * 0.15 +
            appraisal_scores.novelty * 0.10 -
            appraisal_scores.control * 0.10 -
            appraisal_scores.social_reward * 0.15
        )

        stability = 0.52 + concentration * 0.30 - tail_pressure * 0.18 - appraisal_pressure * 0.28
        return max(0.08, min(0.92, stability))

    def _compute_concept_valence(self, emotion_scores: list[EmotionScore]) -> float:
        """Estimate valence from aggregated canonical emotions."""
        polarity = {
            "joy": 0.9,
            "calm": 0.45,
            "curiosity": 0.2,
            "surprise": 0.05,
            "tension": -0.45,
            "sadness": -0.75,
            "anger": -0.7,
            "fear": -0.85,
        }

        numerator = 0.0
        denominator = 0.0
        for emotion in emotion_scores:
            weight = polarity.get(emotion.name, 0.0)
            numerator += emotion.score * weight
            denominator += emotion.score

        if denominator == 0.0:
            return 0.0

        return max(-1.0, min(1.0, numerator / denominator))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity (-1 to 1).
    """
    if len(a) != len(b):
        # Handle different lengths by using minimum
        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)

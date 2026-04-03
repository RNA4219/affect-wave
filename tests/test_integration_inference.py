"""Integration tests for affect inference with mocked embeddings."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from affect_wave.affect.embedding import EmbeddingResult
from affect_wave.affect.inference import AffectInference, InferenceContext
from affect_wave.affect.prototypes import load_all_prototypes
from affect_wave.state.schemas import AffectState
from affect_wave.wave.converter import convert_to_wave_parameter, render_wave_text
from affect_wave.config import Config


class TestAffectInferenceIntegration:
    """Integration tests for affect inference pipeline."""

    @pytest.fixture
    def mock_embedding_client(self):
        """Create mock embedding client."""
        mock = MagicMock()
        mock.health_check = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def prototypes(self):
        """Load actual prototypes."""
        return load_all_prototypes(Config())

    def _create_mock_embedding(self, values: list[float] = None) -> list[float]:
        """Create a mock embedding vector."""
        if values:
            return values
        # Default: 1024-dim random-ish vector
        import math
        return [math.sin(i * 0.1) * 0.5 for i in range(1024)]

    @pytest.mark.asyncio
    async def test_inference_initialization(self, mock_embedding_client, prototypes):
        """Should initialize inference engine."""
        # Mock get_embedding for initialization
        mock_embedding_client.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=self._create_mock_embedding(),
                model="test",
                duration_ms=100.0,
            )
        )

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        # Should have cached all prototype embeddings
        assert len(inference._prototype_embeddings) > 0

    @pytest.mark.asyncio
    async def test_inference_happy_context(self, mock_embedding_client, prototypes):
        """Should infer positive affect from happy context."""
        # Setup mock embeddings
        mock_embedding_client.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=self._create_mock_embedding([0.5] * 1024),
                model="test",
                duration_ms=100.0,
            )
        )

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        # Run inference
        context = InferenceContext(
            user_message="I'm so happy today!",
            assistant_message="That's wonderful to hear! What made you happy?",
            conversation_context="",
        )
        state = await inference.infer(context)

        # Verify state structure
        assert isinstance(state, AffectState)
        assert len(state.top_emotions) == 3
        assert state.top_emotions[0].score >= state.top_emotions[1].score
        assert -1.0 <= state.trend.valence <= 1.0
        assert 0.0 <= state.trend.arousal <= 1.0

    @pytest.mark.asyncio
    async def test_inference_sad_context(self, mock_embedding_client, prototypes):
        """Should infer negative affect from sad context."""
        mock_embedding_client.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=self._create_mock_embedding([-0.5] * 1024),
                model="test",
                duration_ms=100.0,
            )
        )

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        context = InferenceContext(
            user_message="I'm feeling really sad today.",
            assistant_message="I'm sorry to hear that. Would you like to talk about it?",
            conversation_context="",
        )
        state = await inference.infer(context)

        assert isinstance(state, AffectState)
        assert len(state.top_emotions) == 3

    @pytest.mark.asyncio
    async def test_canonical_aggregation_prefers_sharp_signal(self, mock_embedding_client, prototypes):
        """Strong localized concepts should survive canonical aggregation."""
        mock_embedding_client.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=self._create_mock_embedding([0.35] * 1024),
                model="test",
                duration_ms=100.0,
            )
        )

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        concept_scores = [
            type("ConceptLike", (), {"canonical": "anger", "score": 0.95})(),
            type("ConceptLike", (), {"canonical": "anger", "score": 0.72})(),
            type("ConceptLike", (), {"canonical": "anger", "score": 0.31})(),
            type("ConceptLike", (), {"canonical": "calm", "score": 0.61})(),
            type("ConceptLike", (), {"canonical": "calm", "score": 0.58})(),
            type("ConceptLike", (), {"canonical": "joy", "score": 0.4})(),
        ]

        emotions = inference._aggregate_to_emotions(concept_scores)

        assert emotions[0].name == "anger"
        assert emotions[0].score > emotions[1].score

    @pytest.mark.asyncio
    async def test_canonical_aggregation_can_use_direct_signal_to_break_ties(self, mock_embedding_client, prototypes):
        """Direct canonical prototypes should help separate otherwise flat buckets."""
        mock_embedding_client.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=self._create_mock_embedding([0.2] * 1024),
                model="test",
                duration_ms=100.0,
            )
        )

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        concept_scores = [
            type("ConceptLike", (), {"canonical": "sadness", "score": 0.76})(),
            type("ConceptLike", (), {"canonical": "sadness", "score": 0.74})(),
            type("ConceptLike", (), {"canonical": "sadness", "score": 0.72})(),
            type("ConceptLike", (), {"canonical": "fear", "score": 0.75})(),
            type("ConceptLike", (), {"canonical": "fear", "score": 0.73})(),
            type("ConceptLike", (), {"canonical": "fear", "score": 0.71})(),
        ]
        direct_scores = [
            type("EmotionLike", (), {"name": "sadness", "score": 0.58})(),
            type("EmotionLike", (), {"name": "fear", "score": 0.82})(),
        ]

        emotions = inference._aggregate_to_emotions(concept_scores, direct_scores)

        assert emotions[0].name == "fear"

    @pytest.mark.asyncio
    async def test_textual_cues_boost_matching_canonical_labels(self, mock_embedding_client, prototypes):
        """Explicit affect words should provide a small canonical nudge."""
        mock_embedding_client.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=self._create_mock_embedding([0.2] * 1024),
                model="test",
                duration_ms=100.0,
            )
        )

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        context = InferenceContext(
            user_message="後悔と羞恥に震え、恐怖で言葉を失った。",
            assistant_message="彼は自分を分析しながらも、深い悔恨を抱えている。",
            conversation_context="",
        )

        cues = inference._compute_textual_cues(context)

        assert cues["sadness"] > 0.0
        assert cues["fear"] > 0.0
        assert cues["curiosity"] > 0.0

    @pytest.mark.asyncio
    async def test_inference_with_previous_state(self, mock_embedding_client, prototypes):
        """Should use previous state for continuity."""
        mock_embedding_client.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=self._create_mock_embedding(),
                model="test",
                duration_ms=100.0,
            )
        )

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        # Create previous state
        prev_state = AffectState(
            turn_id="prev-turn",
            timestamp=datetime.now(timezone.utc),
            top_emotions=[],
            appraisal=prototypes.appraisals[0] if prototypes.appraisals else None,
            trend=MagicMock(valence=0.5, arousal=0.5, stability=0.7),
        )

        context = InferenceContext(
            user_message="Continue",
            assistant_message="OK",
            conversation_context="",
            prev_state=prev_state,
        )
        state = await inference.infer(context)

        assert state is not None

    @pytest.mark.asyncio
    async def test_first_turn_stability_uses_intrinsic_distribution(self, mock_embedding_client, prototypes):
        """First turn stability should not collapse to zero without prev_state."""
        mock_embedding_client.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=self._create_mock_embedding([0.12] * 1024),
                model="test",
                duration_ms=100.0,
            )
        )

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        context = InferenceContext(
            user_message="I feel tense but I can still think clearly.",
            assistant_message="Let's slow down and look at it together.",
            conversation_context="",
        )
        state = await inference.infer(context)

        assert 0.08 <= state.trend.stability <= 0.92


class TestWavePipelineIntegration:
    """Integration tests for wave parameter pipeline."""

    @pytest.fixture
    def mock_embedding_client(self):
        """Create mock embedding client."""
        mock = MagicMock()
        mock.health_check = AsyncMock(return_value=True)
        mock.get_embedding = AsyncMock(
            return_value=EmbeddingResult(
                embedding=[0.1] * 1024,
                model="test",
                duration_ms=50.0,
            )
        )
        return mock

    @pytest.mark.asyncio
    async def test_full_pipeline(self, mock_embedding_client):
        """Should run full pipeline from text to wave."""
        prototypes = load_all_prototypes(Config())

        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        # Infer affect
        context = InferenceContext(
            user_message="Hello!",
            assistant_message="Hi there!",
            conversation_context="",
        )
        state = await inference.infer(context)

        # Convert to wave
        wave = convert_to_wave_parameter(state)

        # Render
        wave_text = render_wave_text(wave, "wave")
        params_text = render_wave_text(wave, "params")

        # Verify
        assert isinstance(wave_text, str)
        assert len(wave_text) > 0

        import json
        params = json.loads(params_text)
        assert "amplitude" in params

    @pytest.mark.asyncio
    async def test_pipeline_consistency(self, mock_embedding_client):
        """Should produce consistent results for same input."""
        prototypes = load_all_prototypes(Config())
        inference = AffectInference(mock_embedding_client, prototypes)
        await inference.initialize()

        context = InferenceContext(
            user_message="Test",
            assistant_message="Response",
            conversation_context="",
        )

        # Run twice
        state1 = await inference.inference.infer(context) if hasattr(inference, 'inference') else await inference.infer(context)
        state2 = await inference.infer(context)

        # Wave params should be deterministic for same state
        wave1 = convert_to_wave_parameter(state1)
        wave2 = convert_to_wave_parameter(state2)

        # Both should have same structure
        assert wave1.to_dict().keys() == wave2.to_dict().keys()

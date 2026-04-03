"""Tests for HTTP API server."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from affect_wave.config import Config
from affect_wave.api.server import create_app
from affect_wave.affect.embedding import EmbeddingResult
from affect_wave.state.schemas import AffectState, EmotionScore, AppraisalScores, Trend


class TestAPIServer:
    """Tests for FastAPI server."""

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

    @pytest.fixture
    def mock_inference(self, mock_embedding_client):
        """Create mock inference engine."""
        from affect_wave.affect.inference import AffectInference
        from affect_wave.affect.prototypes import load_all_prototypes

        config = Config()
        prototypes = load_all_prototypes(config)
        inference = AffectInference(mock_embedding_client, prototypes)

        # Mock the infer method
        inference.infer = AsyncMock(
            return_value=AffectState(
                turn_id="test-turn",
                top_emotions=[
                    EmotionScore(name="joy", score=0.8),
                    EmotionScore(name="calm", score=0.5),
                    EmotionScore(name="curiosity", score=0.3),
                ],
                appraisal=AppraisalScores(),
                trend=Trend(valence=0.6, arousal=0.5),
            )
        )

        return inference

    def test_create_app(self):
        """Should create FastAPI app."""
        config = Config()
        app = create_app(config)

        assert app is not None
        assert app.title == "affect-wave API"

    def test_health_endpoint_structure(self):
        """Should have health endpoint."""
        config = Config()
        app = create_app(config)

        # Get routes
        routes = [route.path for route in app.routes]
        assert "/health" in routes

    def test_analyze_endpoint_structure(self):
        """Should have analyze endpoint."""
        config = Config()
        app = create_app(config)

        routes = [route.path for route in app.routes]
        assert "/analyze" in routes

    def test_recent_endpoint_structure(self):
        """Should have recent endpoint."""
        config = Config()
        app = create_app(config)

        routes = [route.path for route in app.routes]
        assert "/recent" in routes


class TestAnalyzeRequest:
    """Tests for analyze request model."""

    def test_request_defaults(self):
        """Should have default values."""
        from affect_wave.api.server import AnalyzeRequest

        request = AnalyzeRequest(
            user_message="Hello",
            agent_message="Hi there",
        )

        assert request.conversation_context == ""
        assert request.conversation_id == "default"
        assert request.output_mode == "params"

    def test_request_custom_mode(self):
        """Should accept custom mode."""
        from affect_wave.api.server import AnalyzeRequest

        request = AnalyzeRequest(
            user_message="Hello",
            agent_message="Hi there",
            conversation_id="case-1",
            output_mode="params",
        )

        assert request.conversation_id == "case-1"
        assert request.output_mode == "params"


class TestAnalyzeResponse:
    """Tests for analyze response model."""

    def test_response_structure(self):
        """Should have required fields per specification."""
        from affect_wave.api.server import AnalyzeResponse

        response = AnalyzeResponse(
            turn_id="test-123",
            mode="wave",
            top_emotions=[{"name": "joy", "score": 0.8}],
            trend={"valence": 0.5, "arousal": 0.3, "stability": 0.7},
            compact_state={"dominant": "joy", "tone": "happy", "stability": "high"},
            wave_parameter={"amplitude": 0.5},
            wave_output="~~~~",
        )

        assert response.turn_id == "test-123"
        assert response.mode == "wave"
        assert response.wave_parameter["amplitude"] == 0.5
        assert len(response.top_emotions) == 1
        assert response.trend["valence"] == 0.5
        assert response.wave_output == "~~~~"

    def test_response_params_mode(self):
        """Should allow None wave_output in params mode."""
        from affect_wave.api.server import AnalyzeResponse

        response = AnalyzeResponse(
            turn_id="test-123",
            mode="params",
            top_emotions=[{"name": "joy", "score": 0.8}],
            trend={"valence": 0.5, "arousal": 0.3, "stability": 0.7},
            compact_state={"dominant": "joy", "tone": "happy", "stability": "high"},
            wave_parameter={"amplitude": 0.5},
            wave_output=None,
        )

        assert response.mode == "params"
        assert response.wave_output is None


class TestHealthResponse:
    """Tests for health response model."""

    def test_response_ok(self):
        """Should indicate ok status."""
        from affect_wave.api.server import HealthResponse

        response = HealthResponse(status="ok", embedding_ready=True)

        assert response.status == "ok"
        assert response.embedding_ready is True

    def test_response_degraded(self):
        """Should indicate degraded status."""
        from affect_wave.api.server import HealthResponse

        response = HealthResponse(status="degraded", embedding_ready=False)

        assert response.status == "degraded"
        assert response.embedding_ready is False

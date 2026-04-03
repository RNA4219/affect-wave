"""Tests for embedding client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from affect_wave.affect.embedding import EmbeddingClient, EmbeddingResult
from affect_wave.config import Config


class TestEmbeddingClient:
    """Tests for EmbeddingClient."""

    def test_init(self):
        """Should initialize with config."""
        config = Config(
            llama_cpp_base_url="http://localhost:9999",
            embedding_model="test-model"
        )
        client = EmbeddingClient(config)

        assert client.base_url == "http://localhost:9999"
        assert client.model == "test-model"

    @pytest.mark.asyncio
    async def test_get_embedding_new_format(self):
        """Should parse new llama.cpp response format."""
        config = Config(llama_cpp_base_url="http://localhost:8080")
        client = EmbeddingClient(config)

        # Mock response with new format: [{"index":0,"embedding":[[...]]}]
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"index": 0, "embedding": [[0.1, 0.2, 0.3, 0.4, 0.5]]}
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await client.get_embedding("test text")

        assert len(result.embedding) == 5
        assert result.embedding[0] == 0.1

    @pytest.mark.asyncio
    async def test_get_embedding_flat_format(self):
        """Should parse flat embedding format."""
        config = Config(llama_cpp_base_url="http://localhost:8080")
        client = EmbeddingClient(config)

        # Mock response with flat format
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"index": 0, "embedding": [0.1, 0.2, 0.3]}
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            result = await client.get_embedding("test text")

        assert len(result.embedding) == 3

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Should return True for healthy server."""
        config = Config()
        client = EmbeddingClient(config)

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Should return False for unhealthy server."""
        config = Config()
        client = EmbeddingClient(config)

        import httpx
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("Connection failed")
            )
            result = await client.health_check()

        assert result is False


class TestEmbeddingResult:
    """Tests for EmbeddingResult."""

    def test_defaults(self):
        """Should have default values."""
        result = EmbeddingResult(
            embedding=[0.1, 0.2],
            model="test",
            duration_ms=100.0
        )

        assert result.embedding == [0.1, 0.2]
        assert result.model == "test"
        assert result.duration_ms == 100.0
        assert result.tokens_count is None
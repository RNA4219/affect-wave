"""Embedding retrieval via llama.cpp HTTP API."""

from dataclasses import dataclass
import time

import httpx

from affect_wave.config import Config


@dataclass
class EmbeddingResult:
    """Result of an embedding request."""

    embedding: list[float]
    model: str
    duration_ms: float
    tokens_count: int | None = None


class EmbeddingClient:
    """Client for llama.cpp embeddings HTTP API."""

    def __init__(self, config: Config):
        """Initialize embedding client.

        Args:
            config: Application configuration.
        """
        self.base_url = config.llama_cpp_base_url.rstrip("/")
        self.model = config.embedding_model
        self.timeout = httpx.Timeout(30.0, connect=5.0)

    async def get_embedding(self, text: str) -> EmbeddingResult:
        """Get embedding for text from llama.cpp server.

        Args:
            text: Text to embed.

        Returns:
            EmbeddingResult with embedding vector and metadata.

        Raises:
            httpx.HTTPError: If request fails.
            ValueError: If response is invalid.
        """
        start_time = time.time()

        # llama.cpp embeddings endpoint
        # POST /embeddings with body {"content": "text"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={"content": text},
            )
            response.raise_for_status()

        data = response.json()
        duration_ms = (time.time() - start_time) * 1000

        # llama.cpp returns [{"index":0,"embedding":[[float,...]]}]
        # or {"embedding": [float, ...]} depending on version
        embedding = []
        if isinstance(data, list) and len(data) > 0:
            # New format: [{"index":0,"embedding":[[...]]}]
            emb_data = data[0].get("embedding", [])
            if isinstance(emb_data, list) and len(emb_data) > 0:
                if isinstance(emb_data[0], list):
                    # Nested list: [[...]] -> flatten
                    embedding = emb_data[0]
                else:
                    embedding = emb_data
        elif isinstance(data, dict):
            # Old format: {"embedding": [...]}
            embedding = data.get("embedding", [])

        if not embedding:
            raise ValueError(f"No embedding in response: {data}")

        return EmbeddingResult(
            embedding=embedding,
            model=self.model,
            duration_ms=duration_ms,
            tokens_count=data.get("tokens_evaluated") if isinstance(data, dict) else None,
        )

    async def get_embeddings_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Get embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of EmbeddingResult objects.
        """
        # llama.cpp may not have batch endpoint, process sequentially
        results = []
        for text in texts:
            result = await self.get_embedding(text)
            results.append(result)
        return results

    async def health_check(self) -> bool:
        """Check if llama.cpp server is healthy.

        Returns:
            True if server is responding, False otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def get_model_info(self) -> dict | None:
        """Get model information from llama.cpp server.

        Returns:
            Dict with model info or None if unavailable.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/props")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError:
            return None
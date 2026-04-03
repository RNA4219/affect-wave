"""FastAPI server for affect-wave HTTP API."""

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from affect_wave.config import Config, OutputMode
from affect_wave.affect.embedding import EmbeddingClient
from affect_wave.affect.inference import AffectInference, InferenceContext
from affect_wave.affect.prototypes import load_all_prototypes
from affect_wave.state.store import StateStore
from affect_wave.state.schemas import AffectState, WaveParameter
from affect_wave.wave.converter import convert_to_wave_parameter, render_wave_text


class AnalyzeRequest(BaseModel):
    """Request for affect analysis."""
    user_message: str
    agent_message: str
    conversation_context: str = ""
    conversation_id: str = "default"
    output_mode: Literal["wave", "params"] = "wave"


class AnalyzeResponse(BaseModel):
    """Response from affect analysis (matches specification.md params mode)."""
    turn_id: str
    mode: str
    top_emotions: list[dict]
    trend: dict
    compact_state: dict | None = None
    wave_parameter: dict
    wave_output: str | None = None  # Rendered wave string for wave mode


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    embedding_ready: bool


# Global state for the server
_server_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup server resources."""
    config: Config = app.state.config

    # Initialize embedding client
    embedding_client = EmbeddingClient(config)

    # Check health
    if not await embedding_client.health_check():
        raise RuntimeError("Embedding server not available")

    # Load prototypes and initialize inference
    prototypes = load_all_prototypes(config)
    inference = AffectInference(embedding_client, prototypes)
    await inference.initialize()

    # Initialize per-conversation state stores
    state_stores: dict[str, StateStore] = {"default": StateStore(config)}

    # Store in global state
    _server_state["embedding_client"] = embedding_client
    _server_state["inference"] = inference
    _server_state["state_stores"] = state_stores
    _server_state["config"] = config

    yield

    # Cleanup
    _server_state.clear()


def create_app(config: Config) -> FastAPI:
    """Create FastAPI application.

    Args:
        config: Application configuration.

    Returns:
        FastAPI app instance.
    """
    app = FastAPI(
        title="affect-wave API",
        description="Affect expression interface for LLM conversations",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.config = config

    def get_state_store(conversation_id: str) -> StateStore:
        """Get or create a state store for a conversation."""
        state_stores = _server_state.get("state_stores")
        if state_stores is None:
            raise HTTPException(status_code=503, detail="Server not initialized")

        if conversation_id not in state_stores:
            state_stores[conversation_id] = StateStore(config)

        return state_stores[conversation_id]

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Check server health and embedding availability."""
        embedding_client = _server_state.get("embedding_client")
        embedding_ready = embedding_client is not None

        if embedding_ready:
            embedding_ready = await embedding_client.health_check()

        return HealthResponse(
            status="ok" if embedding_ready else "degraded",
            embedding_ready=embedding_ready,
        )

    @app.post("/analyze", response_model=AnalyzeResponse)
    async def analyze(request: AnalyzeRequest):
        """Analyze affect from user-agent message pair.

        Args:
            request: Analysis request with messages.

        Returns:
            Analysis result with wave parameter and output.
        """
        inference = _server_state.get("inference")

        if not inference:
            raise HTTPException(status_code=503, detail="Server not initialized")

        state_store = get_state_store(request.conversation_id)

        # Get previous state for continuity
        prev_state = state_store.get_prev_state_for_inference()

        # Run inference
        context = InferenceContext(
            user_message=request.user_message,
            assistant_message=request.agent_message,
            conversation_context=request.conversation_context,
            prev_state=prev_state,
        )
        affect_state = await inference.infer(context)

        # Convert to wave parameter
        wave_param = convert_to_wave_parameter(affect_state)

        # Store turn
        turn = state_store.store_turn(
            user_message=request.user_message,
            assistant_message=request.agent_message,
            affect_state=affect_state,
            wave_parameter=wave_param,
        )

        # Render output
        mode_str = "params" if request.output_mode == "params" else "wave"
        wave_output = None
        if mode_str == "wave":
            wave_output = render_wave_text(wave_param, "wave")

        return AnalyzeResponse(
            turn_id=turn.turn_id,
            mode=mode_str,
            top_emotions=[e.to_dict() for e in affect_state.top_emotions],
            trend={
                "valence": affect_state.trend.valence,
                "arousal": affect_state.trend.arousal,
                "stability": affect_state.trend.stability,
            },
            compact_state=affect_state.compact_state.to_dict() if affect_state.compact_state else None,
            wave_parameter=wave_param.to_dict(),
            wave_output=wave_output,
        )

    @app.get("/recent")
    async def get_recent_turns(limit: int = 10, conversation_id: str = "default"):
        """Get recent analyzed turns.

        Args:
            limit: Maximum number of turns to return.

        Returns:
            List of recent turns with summary info.
        """
        state_store = get_state_store(conversation_id)
        turns = state_store.get_recent_turns(limit)

        return [
            {
                "turn_id": t.turn_id,
                "user_message": t.user_message[:50] + "..." if len(t.user_message) > 50 else t.user_message,
                "dominant": t.affect_state.compact_state.dominant if t.affect_state.compact_state else None,
                "valence": t.affect_state.trend.valence,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            }
            for t in turns
        ]

    @app.get("/debug/concepts/{turn_id}")
    async def get_concept_scores(turn_id: str):
        """Get all 171 concept scores for a turn (debug endpoint).

        This endpoint exposes the fine-grained concept layer
        for debugging and analysis purposes.

        Args:
            turn_id: Turn ID to inspect.

        Returns:
            All concept scores with canonical mappings.
        """
        state_stores = _server_state.get("state_stores")
        if state_stores is None:
            raise HTTPException(status_code=503, detail="Server not initialized")

        turn = None
        for state_store in state_stores.values():
            turn = state_store.get_turn(turn_id)
            if turn:
                break
        if not turn:
            raise HTTPException(status_code=404, detail="Turn not found")

        concept_scores = turn.affect_state.get_concept_scores_for_debug()

        return {
            "turn_id": turn_id,
            "concept_count": len(concept_scores),
            "concept_scores": concept_scores,
            "canonical_distribution": _compute_canonical_distribution(concept_scores),
        }

    @app.get("/debug/concepts")
    async def get_latest_concept_scores(conversation_id: str = "default"):
        """Get concept scores for the latest turn (debug endpoint).

        Returns:
            All concept scores for the most recent turn.
        """
        state_store = get_state_store(conversation_id)
        turn = state_store.get_latest_turn()
        if not turn:
            raise HTTPException(status_code=404, detail="No turns available")

        concept_scores = turn.affect_state.get_concept_scores_for_debug()

        return {
            "turn_id": turn.turn_id,
            "concept_count": len(concept_scores),
            "concept_scores": concept_scores,
            "canonical_distribution": _compute_canonical_distribution(concept_scores),
        }

    return app


def _compute_canonical_distribution(concept_scores: list[dict]) -> dict[str, int]:
    """Compute distribution of concepts across canonical labels.

    Args:
        concept_scores: List of concept score dicts.

    Returns:
        Dict mapping canonical label to count.
    """
    distribution: dict[str, int] = {}
    for cs in concept_scores:
        canonical = cs.get("canonical", "unknown")
        distribution[canonical] = distribution.get(canonical, 0) + 1
    return distribution


def run_server(config: Config, host: str = None, port: int = None):
    """Run the HTTP server.

    Args:
        config: Application configuration.
        host: Override host address.
        port: Override port number.
    """
    host = host or config.api_host
    port = port or config.api_port

    app = create_app(config)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )

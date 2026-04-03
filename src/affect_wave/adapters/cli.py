"""CLI adapter for affect-wave state log inspection.

Note: LLM generation is handled by external agents via HTTP API.
This adapter is for local state log inspection only.
"""

from affect_wave.config import Config
from affect_wave.state.store import StateStore


class CLIAdapter:
    """CLI adapter for state log inspection (no LLM generation)."""

    def __init__(self, config: Config):
        """Initialize CLI adapter.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.state_store = StateStore(config)

    def inspect(self, turn_id: str | None = None) -> dict | None:
        """Inspect a specific turn.

        Args:
            turn_id: Turn ID to inspect. If None, inspects latest.

        Returns:
            Turn data dict or None.
        """
        if turn_id:
            turn = self.state_store.get_turn(turn_id)
        else:
            turn = self.state_store.get_latest_turn()

        if not turn:
            return None

        return {
            "turn_id": turn.turn_id,
            "timestamp": turn.timestamp.isoformat() if turn.timestamp else None,
            "user_message": turn.user_message[:100] + "..."
            if len(turn.user_message) > 100 else turn.user_message,
            "assistant_message": turn.assistant_message[:100] + "..."
            if len(turn.assistant_message) > 100 else turn.assistant_message,
            "affect_state": turn.affect_state.to_dict(),
            "wave_parameter": turn.wave_parameter.to_dict(),
        }

    def render(
        self,
        mode: str,
        turn_id: str | None = None,
    ) -> str | None:
        """Render wave parameter for a turn.

        Args:
            mode: Output mode ('wave' or 'params').
            turn_id: Turn ID. If None, uses latest.

        Returns:
            Rendered string or None.
        """
        from affect_wave.wave.converter import render_wave_text

        if turn_id:
            turn = self.state_store.get_turn(turn_id)
        else:
            turn = self.state_store.get_latest_turn()

        if not turn:
            return None

        return render_wave_text(turn.wave_parameter, mode)

    def get_recent_turns(self, count: int = 5) -> list[dict]:
        """Get recent turns summary.

        Args:
            count: Number of turns.

        Returns:
            List of turn summaries.
        """
        turns = self.state_store.get_recent_turns(count)
        return [
            {
                "turn_id": t.turn_id,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "dominant": t.affect_state.compact_state.dominant if t.affect_state.compact_state else None,
                "valence": round(t.affect_state.trend.valence, 2),
            }
            for t in turns
        ]

    def clear_history(self) -> None:
        """Clear all state."""
        self.state_store.clear()
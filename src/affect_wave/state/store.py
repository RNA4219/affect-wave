"""State store for turn-level affect state persistence."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

from affect_wave.state.schemas import AffectState, WaveParameter
from affect_wave.config import Config


@dataclass
class StoredTurn:
    """A stored turn with affect state and wave parameter."""

    turn_id: str
    timestamp: datetime
    user_message: str
    assistant_message: str
    affect_state: AffectState
    wave_parameter: WaveParameter


class StateStore:
    """Manages turn-level state storage."""

    def __init__(self, config: Config):
        """Initialize state store.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.turns: dict[str, StoredTurn] = {}
        self.turn_order: list[str] = []  # For ordering
        self.max_turns: int = 100

    def store_turn(
        self,
        user_message: str,
        assistant_message: str,
        affect_state: AffectState,
        wave_parameter: WaveParameter,
    ) -> StoredTurn:
        """Store a turn with its affect state.

        Args:
            user_message: User input.
            assistant_message: Assistant response.
            affect_state: Inferred affect state.
            wave_parameter: Derived wave parameter.

        Returns:
            StoredTurn object.
        """
        turn = StoredTurn(
            turn_id=affect_state.turn_id,
            timestamp=affect_state.timestamp,
            user_message=user_message,
            assistant_message=assistant_message,
            affect_state=affect_state,
            wave_parameter=wave_parameter,
        )

        self.turns[turn.turn_id] = turn
        self.turn_order.append(turn.turn_id)

        # Trim old turns
        self._trim_turns()

        # Write to log if enabled
        if self.config.state_log_enabled:
            self._write_log(turn)

        return turn

    def get_turn(self, turn_id: str) -> StoredTurn | None:
        """Get a stored turn by ID.

        Args:
            turn_id: Turn identifier.

        Returns:
            StoredTurn or None.
        """
        return self.turns.get(turn_id)

    def get_latest_turn(self) -> StoredTurn | None:
        """Get the most recent turn.

        Returns:
            Latest StoredTurn or None if empty.
        """
        if not self.turn_order:
            return None
        latest_id = self.turn_order[-1]
        return self.turns.get(latest_id)

    def get_recent_turns(self, count: int = 10) -> list[StoredTurn]:
        """Get recent turns.

        Args:
            count: Number of turns to retrieve.

        Returns:
            List of StoredTurn objects, newest first.
        """
        recent_ids = self.turn_order[-count:]
        turns = [self.turns[tid] for tid in recent_ids if tid in self.turns]
        return list(reversed(turns))  # Newest first

    def get_prev_state_for_inference(self) -> AffectState | None:
        """Get previous affect state for next inference.

        Returns:
            Previous AffectState or None.
        """
        latest = self.get_latest_turn()
        if latest:
            return latest.affect_state
        return None

    def clear(self) -> None:
        """Clear all stored turns."""
        self.turns.clear()
        self.turn_order.clear()

    def _trim_turns(self) -> None:
        """Trim turns to max limit."""
        if len(self.turn_order) <= self.max_turns:
            return

        excess = len(self.turn_order) - self.max_turns
        removed_ids = self.turn_order[:excess]
        self.turn_order = self.turn_order[excess:]

        for turn_id in removed_ids:
            self.turns.pop(turn_id, None)

    def _write_log(self, turn: StoredTurn) -> None:
        """Write turn to state log file.

        Args:
            turn: Turn to log.
        """
        log_path = self.config.state_log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create log entry (without sensitive data)
        # Include all concept scores for full debug capability
        affect_dict = turn.affect_state.to_dict()
        affect_dict["concept_scores"] = [
            cs.to_dict() for cs in turn.affect_state.concept_scores
        ]

        entry = {
            "turn_id": turn.turn_id,
            "timestamp": turn.timestamp.isoformat() if turn.timestamp else None,
            "user_message": turn.user_message[:200],  # Truncate for log
            "assistant_message": turn.assistant_message[:200],
            "affect_state": affect_dict,
            "wave_parameter": turn.wave_parameter.to_dict(),
        }

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
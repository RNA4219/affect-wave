"""Conversation history management."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
import uuid


@dataclass
class Message:
    """A single conversation message."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    turn_id: str = field(default_factory=lambda: f"turn-{uuid.uuid4().hex[:8]}")

    def to_api_format(self) -> dict:
        """Convert to API-compatible format.

        Returns:
            Dict with role and content keys.
        """
        return {"role": self.role, "content": self.content}


@dataclass
class ConversationHistory:
    """Manages conversation history for stateless API calls.

    The history is maintained on the application side and sent to the API
    on each call (stateless pattern).
    """

    messages: list[Message] = field(default_factory=list)
    max_turns: int = 20
    system_prompt: str | None = None

    def add_user_message(self, content: str) -> Message:
        """Add a user message to the history.

        Args:
            content: User message content.

        Returns:
            The created Message object.
        """
        msg = Message(role="user", content=content)
        self.messages.append(msg)
        self._trim_history()
        return msg

    def add_assistant_message(
        self, content: str, turn_id: str | None = None
    ) -> Message:
        """Add an assistant message to the history.

        Args:
            content: Assistant response content.
            turn_id: Optional turn ID to link with user message.

        Returns:
            The created Message object.
        """
        msg = Message(role="assistant", content=content, turn_id=turn_id or f"turn-{uuid.uuid4().hex[:8]}")
        self.messages.append(msg)
        self._trim_history()
        return msg

    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt for the conversation.

        Args:
            prompt: System prompt content.
        """
        self.system_prompt = prompt

    def get_api_messages(self) -> list[dict]:
        """Get messages in API-compatible format.

        Includes system prompt if set, followed by conversation messages.

        Returns:
            List of message dicts ready for API call.
        """
        result = []
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        result.extend([msg.to_api_format() for msg in self.messages])
        return result

    def get_last_turn(self) -> tuple[Message, Message] | None:
        """Get the last complete turn (user + assistant pair).

        Returns:
            Tuple of (user_message, assistant_message) or None if incomplete.
        """
        if len(self.messages) < 2:
            return None

        # Find last assistant message
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i].role == "assistant":
                # Find preceding user message
                for j in range(i - 1, -1, -1):
                    if self.messages[j].role == "user":
                        return (self.messages[j], self.messages[i])
        return None

    def get_turn_by_id(self, turn_id: str) -> Message | None:
        """Get a message by turn ID.

        Args:
            turn_id: Turn ID to search for.

        Returns:
            Message with matching turn_id or None.
        """
        for msg in self.messages:
            if msg.turn_id == turn_id:
                return msg
        return None

    def clear(self) -> None:
        """Clear all messages and system prompt."""
        self.messages.clear()
        self.system_prompt = None

    def _trim_history(self) -> None:
        """Trim history to max_turns limit.

        Keeps system prompt and most recent turns.
        """
        if len(self.messages) <= self.max_turns:
            return

        # Keep most recent messages
        excess = len(self.messages) - self.max_turns
        self.messages = self.messages[excess:]

    def get_context_for_embedding(self, include_latest_turn: bool = True) -> str:
        """Get concatenated context for embedding generation.

        Args:
            include_latest_turn: Whether to include the latest user/assistant
                pair in the returned context.

        Returns:
            String containing recent conversation context.
        """
        # Use last few turns for embedding context
        recent_messages = self.messages[-4:] if len(self.messages) >= 4 else self.messages
        if (
            not include_latest_turn
            and len(recent_messages) >= 2
            and recent_messages[-1].role == "assistant"
            and recent_messages[-2].role == "user"
        ):
            recent_messages = recent_messages[:-2]
        parts = []
        for msg in recent_messages:
            prefix = "User" if msg.role == "user" else "Assistant"
            parts.append(f"{prefix}: {msg.content}")
        return "\n".join(parts)

"""Tests for conversation history management."""

import pytest

from affect_wave.conversation.history import Message, ConversationHistory


class TestMessage:
    """Tests for Message."""

    def test_create_user_message(self):
        """Should create user message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.turn_id.startswith("turn-")

    def test_create_assistant_message(self):
        """Should create assistant message."""
        msg = Message(role="assistant", content="Hi there")
        assert msg.role == "assistant"

    def test_to_api_format(self):
        """Should convert to API format."""
        msg = Message(role="user", content="Test")
        api_msg = msg.to_api_format()
        assert api_msg == {"role": "user", "content": "Test"}


class TestConversationHistory:
    """Tests for ConversationHistory."""

    def test_empty_history(self):
        """Should start empty."""
        history = ConversationHistory()
        assert len(history.messages) == 0

    def test_add_user_message(self):
        """Should add user message."""
        history = ConversationHistory()
        msg = history.add_user_message("Hello")
        assert len(history.messages) == 1
        assert history.messages[0].role == "user"
        assert history.messages[0].content == "Hello"

    def test_add_assistant_message(self):
        """Should add assistant message."""
        history = ConversationHistory()
        history.add_user_message("Hello")
        history.add_assistant_message("Hi there")
        assert len(history.messages) == 2

    def test_get_api_messages(self):
        """Should return messages in API format."""
        history = ConversationHistory()
        history.set_system_prompt("You are helpful.")
        history.add_user_message("Hello")
        history.add_assistant_message("Hi")

        api_messages = history.get_api_messages()
        assert len(api_messages) == 3
        assert api_messages[0]["role"] == "system"
        assert api_messages[1]["role"] == "user"
        assert api_messages[2]["role"] == "assistant"

    def test_get_last_turn(self):
        """Should get last complete turn."""
        history = ConversationHistory()
        history.add_user_message("Q1")
        history.add_assistant_message("A1")
        history.add_user_message("Q2")
        history.add_assistant_message("A2")

        turn = history.get_last_turn()
        assert turn is not None
        user_msg, asst_msg = turn
        assert user_msg.content == "Q2"
        assert asst_msg.content == "A2"

    def test_get_last_turn_incomplete(self):
        """Should return None if no complete turn."""
        history = ConversationHistory()
        history.add_user_message("Hello")

        turn = history.get_last_turn()
        assert turn is None

    def test_get_turn_by_id(self):
        """Should find message by turn_id."""
        history = ConversationHistory()
        msg = history.add_user_message("Hello")

        found = history.get_turn_by_id(msg.turn_id)
        assert found is not None
        assert found.content == "Hello"

        # Not found
        assert history.get_turn_by_id("nonexistent") is None

    def test_clear(self):
        """Should clear all messages."""
        history = ConversationHistory()
        history.add_user_message("Hello")
        history.set_system_prompt("Test")
        history.clear()

        assert len(history.messages) == 0
        assert history.system_prompt is None

    def test_trim_history(self):
        """Should trim history to max_turns."""
        history = ConversationHistory(max_turns=5)
        for i in range(10):
            history.add_user_message(f"Q{i}")
            history.add_assistant_message(f"A{i}")

        # Should have at most max_turns * 2 messages (user + assistant pairs)
        assert len(history.messages) <= 10

    def test_get_context_for_embedding(self):
        """Should get context string for embedding."""
        history = ConversationHistory()
        history.add_user_message("Hello")
        history.add_assistant_message("Hi there")

        context = history.get_context_for_embedding()
        assert "User: Hello" in context
        assert "Assistant: Hi there" in context

    def test_get_context_for_embedding_excludes_latest_turn(self):
        """Should exclude latest user/assistant pair when requested."""
        history = ConversationHistory()
        history.add_user_message("Q1")
        history.add_assistant_message("A1")
        history.add_user_message("Q2")
        history.add_assistant_message("A2")

        context = history.get_context_for_embedding(include_latest_turn=False)

        assert "User: Q1" in context
        assert "Assistant: A1" in context
        assert "User: Q2" not in context
        assert "Assistant: A2" not in context


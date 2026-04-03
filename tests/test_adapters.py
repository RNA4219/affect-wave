"""Tests for output adapters."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from affect_wave.adapters.text import TextAdapter, format_wave_prefix, build_reply_with_wave
from affect_wave.state.schemas import WaveParameter


class TestTextAdapter:
    """Tests for text adapter."""

    def test_format_wave_prefix(self):
        """Should format wave as prefix."""
        wave = WaveParameter(amplitude=0.5, glow=0.7)
        prefix = format_wave_prefix(wave)

        assert isinstance(prefix, str)
        assert len(prefix) > 0

    def test_format_wave_prefix_max_length(self):
        """Should truncate to max length."""
        wave = WaveParameter(amplitude=1.0, glow=1.0)
        prefix = format_wave_prefix(wave, max_length=20)

        assert len(prefix) <= 20

    def test_build_reply_with_wave(self):
        """Should build reply with wave prefix."""
        wave = WaveParameter(amplitude=0.6)
        response = "Hello, how can I help?"

        reply = build_reply_with_wave(response, wave)

        assert "Hello, how can I help?" in reply
        assert "~" in reply  # Wave character

    def test_text_adapter_format_message(self):
        """Should format message with wave."""
        adapter = TextAdapter()
        wave = WaveParameter(amplitude=0.5)
        content = "Test response"

        formatted = adapter.format_message(content, wave)

        assert content in formatted

    def test_text_adapter_format_wave_only(self):
        """Should format just the wave."""
        adapter = TextAdapter()
        wave = WaveParameter(amplitude=0.5, jitter=0.3)

        wave_text = adapter.format_wave_only(wave)

        assert isinstance(wave_text, str)
        assert len(wave_text) > 0


class TestCLIAdapter:
    """Tests for CLI adapter (state log inspection only)."""

    def test_cli_adapter_init(self):
        """Should initialize CLI adapter."""
        from affect_wave.adapters.cli import CLIAdapter
        from affect_wave.config import Config

        config = Config()
        adapter = CLIAdapter(config)

        assert adapter.config == config
        assert adapter.state_store is not None

    def test_cli_adapter_inspect_empty(self):
        """Should return None when no turns."""
        from affect_wave.adapters.cli import CLIAdapter
        from affect_wave.config import Config

        config = Config()
        adapter = CLIAdapter(config)

        result = adapter.inspect()
        assert result is None

    def test_cli_adapter_render_empty(self):
        """Should return None when no turns to render."""
        from affect_wave.adapters.cli import CLIAdapter
        from affect_wave.config import Config

        config = Config()
        adapter = CLIAdapter(config)

        result = adapter.render("wave")
        assert result is None

    def test_cli_adapter_get_recent_turns_empty(self):
        """Should return empty list when no turns."""
        from affect_wave.adapters.cli import CLIAdapter
        from affect_wave.config import Config

        config = Config()
        adapter = CLIAdapter(config)

        turns = adapter.get_recent_turns()
        assert turns == []

    def test_cli_adapter_clear_history(self):
        """Should clear state store."""
        from affect_wave.adapters.cli import CLIAdapter
        from affect_wave.config import Config

        config = Config()
        adapter = CLIAdapter(config)
        adapter.clear_history()

        # Should not raise


class TestDiscordAdapter:
    """Tests for Discord adapter."""

    def test_discord_adapter_init(self):
        """Should initialize Discord adapter."""
        from affect_wave.adapters.discord import DiscordAdapter
        from affect_wave.config import Config

        config = Config()
        adapter = DiscordAdapter(config)

        assert adapter.config == config
        assert adapter._inference is None  # Lazy initialization

    def test_discord_adapter_channel_stores(self):
        """Should have separate channel stores."""
        from affect_wave.adapters.discord import DiscordAdapter
        from affect_wave.config import Config

        config = Config()
        adapter = DiscordAdapter(config)

        # Initially empty
        assert len(adapter.channel_stores) == 0

        # Creates on demand
        store = adapter._get_store(12345)
        assert store is not None
        assert 12345 in adapter.channel_stores

    def test_discord_adapter_params_trigger_bilingual(self):
        """Should detect Japanese and English params triggers."""
        from affect_wave.adapters.discord import DiscordAdapter

        assert DiscordAdapter.is_params_trigger("詳細を見せて")
        assert DiscordAdapter.is_params_trigger("show detail please")
        assert DiscordAdapter.is_params_trigger("params")
        assert not DiscordAdapter.is_params_trigger("hello there")

    def test_discord_adapter_build_params_payload(self):
        """Should build params payload from latest stored turn."""
        from affect_wave.adapters.discord import DiscordAdapter
        from affect_wave.config import Config
        from affect_wave.state.schemas import create_affect_state, EmotionScore, AppraisalScores, Trend

        config = Config()
        adapter = DiscordAdapter(config)
        store = adapter._get_store(42)
        affect_state = create_affect_state(
            top_emotions=[
                EmotionScore(name="joy", score=0.8),
                EmotionScore(name="calm", score=0.6),
                EmotionScore(name="curiosity", score=0.5),
            ],
            appraisal=AppraisalScores(),
            trend=Trend(valence=0.4, arousal=0.5, stability=0.7),
            affect_embedding=[0.1] * 8,
        )
        wave = WaveParameter(amplitude=0.5, jitter=0.2, density=0.4)
        store.store_turn(
            user_message="hi",
            assistant_message="hello",
            affect_state=affect_state,
            wave_parameter=wave,
        )

        payload = adapter._build_params_payload(42)

        assert payload is not None
        assert payload["mode"] == "params"
        assert payload["turn_id"] == affect_state.turn_id
        assert len(payload["top_emotions"]) == 3

    @pytest.mark.asyncio
    async def test_discord_adapter_create_bot(self):
        """Should create Discord bot."""
        from affect_wave.adapters.discord import DiscordAdapter
        from affect_wave.config import Config

        config = Config(
            discord_bot_token="test-token",
            embedding_model="test-embedding",
            api_llm_base_url="https://example.test/v1",
            api_llm_api_key="test-key",
            api_llm_model="test-model",
        )
        adapter = DiscordAdapter(config)

        client = adapter.create_bot()
        assert client is not None
        assert adapter._command_tree is not None
        commands = adapter._command_tree.get_commands()
        assert any(command.name == "affect" for command in commands)

    @pytest.mark.asyncio
    async def test_discord_adapter_process_message_generates_response(self):
        """Should generate a normal response instead of placeholder text."""
        from affect_wave.adapters.discord import DiscordAdapter
        from affect_wave.config import Config
        from affect_wave.state.schemas import create_affect_state, EmotionScore, AppraisalScores, Trend

        config = Config(
            discord_bot_token="test-token",
            embedding_model="test-embedding",
            api_llm_base_url="https://example.test/v1",
            api_llm_api_key="test-key",
            api_llm_model="test-model",
        )
        adapter = DiscordAdapter(config)
        adapter._inference = MagicMock()
        adapter._inference.infer = AsyncMock(
            return_value=create_affect_state(
                top_emotions=[EmotionScore(name="joy", score=0.8)],
                appraisal=AppraisalScores(),
                trend=Trend(valence=0.4, arousal=0.5, stability=0.7),
                affect_embedding=[0.1] * 8,
            )
        )
        adapter._llm_connector = MagicMock()
        adapter._llm_connector.generate_response = AsyncMock(
            return_value=MagicMock(content="生成された応答")
        )

        message = MagicMock()
        message.content = "こんにちは"
        message.channel.id = 123

        wave_display, response_text = await adapter.process_message(message)

        assert response_text == "生成された応答"
        assert "[External agent should provide LLM response]" not in response_text
        assert isinstance(wave_display, str)

    @pytest.mark.asyncio
    async def test_discord_adapter_send_response_webhook_fallback(self):
        """Should fall back to reply_prefix when webhook send fails."""
        from affect_wave.adapters.discord import DiscordAdapter
        from affect_wave.config import Config, DiscordTransport

        config = Config(
            discord_transport=DiscordTransport.WEBHOOK,
            discord_webhook_url="https://example.test/webhook",
        )
        adapter = DiscordAdapter(config)

        message = MagicMock()
        message.reply = AsyncMock()

        with patch("affect_wave.adapters.discord.httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=RuntimeError("boom"))
            mock_client_cls.return_value = mock_client

            await adapter.send_response(message, "~ ^ ~", "hello")

        message.reply.assert_awaited_once()
        sent_text = message.reply.await_args.args[0]
        assert "~ ^ ~" in sent_text
        assert "hello" in sent_text

    def test_discord_adapter_no_token(self):
        """Should raise without token."""
        from affect_wave.adapters.discord import DiscordAdapter
        from affect_wave.config import Config

        config = Config()
        adapter = DiscordAdapter(config)

        with pytest.raises(ValueError, match="DISCORD_BOT_TOKEN"):
            import asyncio
            asyncio.run(adapter.run())

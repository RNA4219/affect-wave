"""Tests for affect_wave configuration."""

import os
from pathlib import Path
import pytest

from affect_wave.config import Config, OutputMode, DiscordTransport, StateLogMode


class TestConfig:
    """Tests for configuration loading."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = Config()

        assert config.affect_output_mode == OutputMode.PARAMS
        assert config.discord_transport == DiscordTransport.REPLY_PREFIX
        assert config.state_log_enabled is False
        assert config.state_log_mode == StateLogMode.PREVIEW
        assert config.api_host == "127.0.0.1"
        assert config.api_port == 8081

    def test_from_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Should load from environment variables."""
        monkeypatch.setenv("AFFECT_OUTPUT_MODE", "params")
        monkeypatch.setenv("STATE_LOG_ENABLED", "true")
        monkeypatch.setenv("STATE_LOG_MODE", "redacted")
        monkeypatch.setenv("API_PORT", "9000")

        config = Config.from_env()

        assert config.state_log_enabled is True
        assert config.state_log_mode == StateLogMode.REDACTED
        assert config.api_port == 9000

    def test_output_mode_selection(self, monkeypatch: pytest.MonkeyPatch):
        """Should correctly select output mode."""
        monkeypatch.setenv("AFFECT_OUTPUT_MODE", "params")

        config = Config.from_env()
        assert config.affect_output_mode == OutputMode.PARAMS

    def test_discord_transport_selection(self, monkeypatch: pytest.MonkeyPatch):
        """Should correctly select Discord transport."""
        monkeypatch.setenv("DISCORD_TRANSPORT", "webhook")

        config = Config.from_env()
        assert config.discord_transport == DiscordTransport.WEBHOOK

    def test_validate_for_serve(self, monkeypatch: pytest.MonkeyPatch):
        """Should validate required keys for serve."""
        monkeypatch.setenv("EMBEDDING_MODEL", "")  # Empty

        config = Config.from_env()
        errors = config.validate_for_serve()

        assert any("EMBEDDING_MODEL" in e for e in errors)

    def test_validate_for_discord(self, monkeypatch: pytest.MonkeyPatch):
        """Should validate required keys for Discord."""
        monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)

        config = Config.from_env()
        errors = config.validate_for_discord()

        assert any("DISCORD_BOT_TOKEN" in e for e in errors)

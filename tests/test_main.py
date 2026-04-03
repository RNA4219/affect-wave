"""Tests for CLI main entry point."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from affect_wave.main import cli, serve, inspect, render, recent


class TestMainCLI:
    """Tests for main CLI commands."""

    def test_cli_version(self):
        """Should show version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert "0.1.0" in result.output

    def test_cli_help(self):
        """Should show help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert "Affect Wave" in result.output
        assert "serve" in result.output
        assert "inspect" in result.output

    def test_cli_commands_list(self):
        """Should list all commands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert "serve" in result.output
        assert "inspect" in result.output
        assert "render" in result.output
        assert "recent" in result.output
        assert "discord" in result.output


class TestServeCommand:
    """Tests for serve command."""

    def test_serve_help(self):
        """Should show serve help."""
        runner = CliRunner()
        result = runner.invoke(serve, ["--help"])
        assert "api" in result.output.lower() or "server" in result.output.lower()

    @patch("affect_wave.main.Config.from_env")
    @patch("affect_wave.api.server.uvicorn.run")
    def test_serve_creates_server(self, mock_run, mock_config):
        """Should create server with config."""
        mock_config.return_value = MagicMock(
            validate_for_serve=lambda: [],
            api_host="127.0.0.1",
            api_port=8080,
            llama_cpp_base_url="http://localhost:8080",
        )
        mock_run.side_effect = KeyboardInterrupt()

        runner = CliRunner()
        result = runner.invoke(serve, [])

        # uvicorn.run should be called
        mock_run.assert_called_once()

    @patch("affect_wave.main.Config.from_env")
    def test_serve_validation_error(self, mock_config):
        """Should fail validation."""
        mock_config.return_value = MagicMock(
            validate_for_serve=lambda: ["EMBEDDING_MODEL missing"],
        )

        runner = CliRunner()
        result = runner.invoke(serve, [])

        assert result.exit_code != 0


class TestInspectCommand:
    """Tests for inspect command."""

    def test_inspect_help(self):
        """Should show inspect help."""
        runner = CliRunner()
        result = runner.invoke(inspect, ["--help"])
        assert "affect" in result.output.lower() or "state" in result.output.lower()

    @patch("affect_wave.main.Config.from_env")
    def test_inspect_no_state_log(self, mock_config):
        """Should handle no state log."""
        from pathlib import Path

        mock_config.return_value = MagicMock(
            state_log_enabled=False,
            state_log_path=Path("nonexistent.jsonl"),
        )

        runner = CliRunner()
        result = runner.invoke(inspect, [])

        assert "No state log" in result.output


class TestRenderCommand:
    """Tests for render command."""

    def test_render_help(self):
        """Should show render help."""
        runner = CliRunner()
        result = runner.invoke(render, ["--help"])
        assert "wave" in result.output.lower() or "mode" in result.output.lower()

    @patch("affect_wave.main.Config.from_env")
    def test_render_no_state_log(self, mock_config):
        """Should handle no state log."""
        from pathlib import Path

        mock_config.return_value = MagicMock(
            state_log_enabled=False,
            state_log_path=Path("nonexistent.jsonl"),
        )

        runner = CliRunner()
        result = runner.invoke(render, ["--mode", "wave"])

        assert "No state log" in result.output


class TestRecentCommand:
    """Tests for recent command."""

    def test_recent_help(self):
        """Should show recent help."""
        runner = CliRunner()
        result = runner.invoke(recent, ["--help"])
        assert "recent" in result.output.lower()

    @patch("affect_wave.main.Config.from_env")
    def test_recent_no_state_log(self, mock_config):
        """Should handle no state log."""
        from pathlib import Path

        mock_config.return_value = MagicMock(
            state_log_enabled=False,
            state_log_path=Path("nonexistent.jsonl"),
        )

        runner = CliRunner()
        result = runner.invoke(recent, [])

        assert "No state log" in result.output


class TestDiscordCommand:
    """Tests for discord command."""

    def test_discord_help(self):
        """Should show discord help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["discord", "--help"])
        assert "discord" in result.output.lower() or "bot" in result.output.lower()

    @patch("affect_wave.main.Config.from_env")
    def test_discord_no_token(self, mock_config):
        """Should fail without token."""
        mock_config.return_value = MagicMock(
            discord_bot_token=None,
            validate_for_discord=lambda: ["DISCORD_BOT_TOKEN required"],
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["discord"])

        assert result.exit_code != 0


class TestEnvironmentConfiguration:
    """Tests for environment configuration."""

    @patch.dict("os.environ", {"AFFECT_OUTPUT_MODE": "params", "API_PORT": "9000"})
    def test_uses_env_vars(self):
        """Should use environment variables."""
        from affect_wave.config import Config

        config = Config.from_env()

        assert config.affect_output_mode.value == "params"
        assert config.api_port == 9000

    def test_env_file_option(self, tmp_path):
        """Should support custom env file."""
        env_file = tmp_path / ".env.test"
        env_file.write_text("API_PORT=8081\n")

        with patch.dict("os.environ", {}, clear=True):
            from affect_wave.config import Config
            config = Config.from_env(env_file)

            # Should have loaded from file
            assert config is not None
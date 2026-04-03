"""Configuration management for affect-wave."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
import os


class OutputMode(str, Enum):
    """Output display mode."""
    WAVE = "wave"
    PARAMS = "params"


class DiscordTransport(str, Enum):
    """Discord message transport method."""
    REPLY_PREFIX = "reply_prefix"
    WEBHOOK = "webhook"


class StateLogMode(str, Enum):
    """State log redaction mode."""
    PREVIEW = "preview"
    REDACTED = "redacted"
    FULL = "full"


@dataclass
class Config:
    """Application configuration loaded from environment."""

    # API LLM settings
    api_llm_base_url: str | None = None
    api_llm_api_key: str | None = None
    api_llm_model: str | None = None
    api_llm_system_prompt: str | None = None

    # llama.cpp embedding settings
    llama_cpp_base_url: str = "http://127.0.0.1:8080"
    embedding_model: str = ""

    # Discord settings
    discord_bot_token: str | None = None
    discord_webhook_url: str | None = None
    discord_transport: DiscordTransport = DiscordTransport.REPLY_PREFIX

    # Output settings
    affect_output_mode: OutputMode = OutputMode.PARAMS

    # State log settings
    state_log_enabled: bool = False
    state_log_mode: StateLogMode = StateLogMode.PREVIEW
    state_log_path: Path = field(default_factory=lambda: Path("./logs/affect-state.jsonl"))

    # Prototype settings
    prototypes_dir: Path = field(default_factory=lambda: Path("./data/prototypes"))

    # API server settings
    api_host: str = "127.0.0.1"
    api_port: int = 8081

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "Config":
        """Load configuration from environment variables.

        Args:
            env_path: Optional path to .env file. If None, searches default locations.

        Returns:
            Config instance with loaded values.
        """
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        output_mode_str = os.getenv("AFFECT_OUTPUT_MODE", "params").lower()
        output_mode = OutputMode.WAVE if output_mode_str == "wave" else OutputMode.PARAMS

        transport_str = os.getenv("DISCORD_TRANSPORT", "reply_prefix").lower()
        transport = (
            DiscordTransport.REPLY_PREFIX
            if transport_str == "reply_prefix"
            else DiscordTransport.WEBHOOK
        )

        return cls(
            api_llm_base_url=os.getenv("API_LLM_BASE_URL"),
            api_llm_api_key=os.getenv("API_LLM_API_KEY"),
            api_llm_model=os.getenv("API_LLM_MODEL"),
            api_llm_system_prompt=os.getenv("API_LLM_SYSTEM_PROMPT"),
            llama_cpp_base_url=os.getenv("LLAMA_CPP_BASE_URL", "http://127.0.0.1:8080"),
            embedding_model=os.getenv("EMBEDDING_MODEL", ""),
            discord_bot_token=os.getenv("DISCORD_BOT_TOKEN"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            discord_transport=transport,
            affect_output_mode=output_mode,
            state_log_enabled=os.getenv("STATE_LOG_ENABLED", "false").lower() == "true",
            state_log_mode=StateLogMode(os.getenv("STATE_LOG_MODE", "preview").lower()),
            state_log_path=Path(os.getenv("STATE_LOG_PATH", "./logs/affect-state.jsonl")),
            prototypes_dir=Path(os.getenv("PROTOTYPES_DIR", "./data/prototypes")),
            api_host=os.getenv("API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("API_PORT", "8081")),
        )

    def validate_for_serve(self) -> list[str]:
        """Validate configuration for API server operation.

        Returns:
            List of missing or invalid configuration keys.
        """
        errors = []

        if not self.embedding_model:
            errors.append("EMBEDDING_MODEL must be specified")

        return errors

    def validate_for_api_llm(self) -> list[str]:
        """Validate configuration for API LLM generation."""
        errors = []

        if not self.api_llm_base_url:
            errors.append("API_LLM_BASE_URL is required for response generation")
        if not self.api_llm_api_key:
            errors.append("API_LLM_API_KEY is required for response generation")
        if not self.api_llm_model:
            errors.append("API_LLM_MODEL is required for response generation")

        return errors

    def validate_for_discord(self) -> list[str]:
        """Validate configuration for Discord operation.

        Returns:
            List of missing or invalid configuration keys.
        """
        errors = self.validate_for_serve()
        errors.extend(self.validate_for_api_llm())

        if not self.discord_bot_token:
            errors.append("DISCORD_BOT_TOKEN is required for Discord adapter")

        return errors

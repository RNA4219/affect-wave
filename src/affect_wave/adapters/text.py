"""Text adapter for reply_prefix style wave display.

This is a platform-agnostic text adapter that can be reused
across different text-first platforms (Discord, Slack, etc.).
"""

from affect_wave.state.schemas import WaveParameter
from affect_wave.wave.converter import render_wave_text


def format_wave_prefix(wave: WaveParameter, max_length: int = 80) -> str:
    """Format wave parameter as a reply prefix.

    Args:
        wave: Wave parameter to format.
        max_length: Maximum character length for prefix.

    Returns:
        Formatted wave prefix string.
    """
    # Render wave text
    wave_text = render_wave_text(wave, mode="wave")

    # Truncate if needed
    if len(wave_text) > max_length:
        wave_text = wave_text[:max_length - 3] + "..."

    return wave_text


def build_reply_with_wave(
    response_text: str,
    wave: WaveParameter,
    max_prefix_length: int = 80,
) -> str:
    """Build a reply with wave prefix.

    The wave block is placed before the response text,
    separated by a blank line.

    Args:
        response_text: The main response content.
        wave: Wave parameter for prefix.
        max_prefix_length: Maximum length for wave prefix.

    Returns:
        Complete reply with wave prefix.
    """
    prefix = format_wave_prefix(wave, max_prefix_length)
    return f"{prefix}\n\n{response_text}"


class TextAdapter:
    """Text adapter for wave display in text-first platforms."""

    def __init__(self, max_prefix_length: int = 80):
        """Initialize text adapter.

        Args:
            max_prefix_length: Maximum length for wave prefix.
        """
        self.max_prefix_length = max_prefix_length

    def format_message(
        self,
        content: str,
        wave: WaveParameter,
    ) -> str:
        """Format a message with wave prefix.

        Args:
            content: Message content.
            wave: Wave parameter.

        Returns:
            Formatted message with wave prefix.
        """
        return build_reply_with_wave(content, wave, self.max_prefix_length)

    def format_wave_only(self, wave: WaveParameter) -> str:
        """Format just the wave portion.

        Args:
            wave: Wave parameter.

        Returns:
            Formatted wave string.
        """
        return format_wave_prefix(wave, self.max_prefix_length)
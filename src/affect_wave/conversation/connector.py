"""API LLM connector for conversation generation."""

from dataclasses import dataclass

import httpx

from affect_wave.conversation.history import ConversationHistory


@dataclass
class ChatCompletionResult:
    """Result of an API LLM chat completion."""

    content: str
    model: str


class ApiLLMConnector:
    """Minimal OpenAI-compatible chat completions connector."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        system_prompt: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.timeout_seconds = timeout_seconds

    async def generate_response(
        self,
        history: ConversationHistory,
    ) -> ChatCompletionResult:
        """Generate an assistant response from conversation history."""
        if self.system_prompt and not history.system_prompt:
            history.set_system_prompt(self.system_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": history.get_api_messages(),
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not content:
            raise ValueError("API LLM response content is empty")

        return ChatCompletionResult(
            content=content,
            model=data.get("model", self.model),
        )

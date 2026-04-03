"""Discord adapter for affect-wave.

Supports bot mode (primary) and webhook mode (optional).
Uses an API LLM connector for response generation and the text adapter
for reply_prefix style display.
"""

import json
import httpx

try:
    import discord
    from discord import app_commands
except ModuleNotFoundError:  # pragma: no cover - exercised only when extra missing
    discord = None
    app_commands = None

from affect_wave.config import Config, DiscordTransport, OutputMode
from affect_wave.affect.embedding import EmbeddingClient
from affect_wave.affect.prototypes import load_all_prototypes
from affect_wave.affect.inference import AffectInference, InferenceContext
from affect_wave.conversation.connector import ApiLLMConnector
from affect_wave.conversation.history import ConversationHistory
from affect_wave.state.store import StateStore
from affect_wave.wave.converter import convert_to_wave_parameter, render_wave_text


PARAMS_TRIGGER_JA = ("詳細", "感情波", "パラメータ")
PARAMS_TRIGGER_EN = ("detail", "details", "wave", "params")


class DiscordAdapter:
    """Discord adapter for affect-wave bot."""

    def __init__(self, config: Config):
        """Initialize Discord adapter.

        Args:
            config: Application configuration.
        """
        self.config = config

        # Per-channel state
        self.channel_stores: dict[int, StateStore] = {}
        self.channel_histories: dict[int, ConversationHistory] = {}

        # Components
        self._embedding_client: EmbeddingClient | None = None
        self._inference: AffectInference | None = None
        self._llm_connector: ApiLLMConnector | None = None
        self._bot: discord.Client | None = None
        self._command_tree: app_commands.CommandTree | None = None

    async def initialize(self) -> None:
        """Initialize async components."""
        errors = self.config.validate_for_discord()
        if errors:
            raise ValueError("\n".join(errors))

        self._embedding_client = EmbeddingClient(self.config)

        if not await self._embedding_client.health_check():
            print(f"Warning: llama.cpp server not responding at {self.config.llama_cpp_base_url}")

        prototypes = load_all_prototypes(self.config)
        self._inference = AffectInference(self._embedding_client, prototypes)
        await self._inference.initialize()
        self._llm_connector = ApiLLMConnector(
            base_url=self.config.api_llm_base_url or "",
            api_key=self.config.api_llm_api_key or "",
            model=self.config.api_llm_model or "",
            system_prompt=self.config.api_llm_system_prompt,
        )

    def _get_store(self, channel_id: int) -> StateStore:
        """Get or create state store for channel."""
        if channel_id not in self.channel_stores:
            self.channel_stores[channel_id] = StateStore(self.config)
        return self.channel_stores[channel_id]

    def _get_history(self, channel_id: int) -> ConversationHistory:
        """Get or create conversation history for channel."""
        if channel_id not in self.channel_histories:
            self.channel_histories[channel_id] = ConversationHistory()
        return self.channel_histories[channel_id]

    @staticmethod
    def is_params_trigger(content: str) -> bool:
        """Return True when content explicitly asks for params/detail mode."""
        normalized = content.strip().lower()
        if not normalized:
            return False

        if any(token in content for token in PARAMS_TRIGGER_JA):
            return True

        return any(token in normalized.split() or token in normalized for token in PARAMS_TRIGGER_EN)

    def _build_params_payload(self, channel_id: int) -> dict | None:
        """Build params mode payload for the latest turn in a channel."""
        store = self._get_store(channel_id)
        latest = store.get_latest_turn()
        if latest is None:
            return None

        affect_state = latest.affect_state
        return {
            "turn_id": latest.turn_id,
            "mode": "params",
            "top_emotions": [emotion.to_dict() for emotion in affect_state.top_emotions],
            "trend": {
                "valence": round(affect_state.trend.valence, 3),
                "arousal": round(affect_state.trend.arousal, 3),
                "stability": round(affect_state.trend.stability, 3),
            },
            "compact_state": affect_state.compact_state.to_dict(),
            "wave_parameter": latest.wave_parameter.to_dict(),
        }

    def _build_wave_display(self, channel_id: int) -> str | None:
        """Build wave mode text for the latest turn in a channel."""
        store = self._get_store(channel_id)
        latest = store.get_latest_turn()
        if latest is None:
            return None

        return render_wave_text(latest.wave_parameter, OutputMode.WAVE.value)

    async def handle_params_request(self, message: discord.Message) -> bool:
        """Handle an explicit params/detail request.

        Returns True when a params response was sent.
        """
        payload = self._build_params_payload(message.channel.id)
        if payload is None:
            await message.reply("No analyzed turn is available yet.")
            return True

        await message.reply(f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```")
        return True

    async def set_transport(self, transport: DiscordTransport) -> str:
        """Update Discord transport mode."""
        self.config.discord_transport = transport
        return f"Discord transport set to `{transport.value}`."

    async def process_message(
        self,
        message: discord.Message,
    ) -> tuple[str, str]:
        """Process a Discord message and generate response.

        Args:
            message: Discord message containing user input.

        Returns:
            Tuple of (wave_display, response_text).
        """
        if not self._inference or not self._llm_connector:
            await self.initialize()

        channel_id = message.channel.id
        store = self._get_store(channel_id)
        history = self._get_history(channel_id)

        history.add_user_message(message.content)
        llm_result = await self._llm_connector.generate_response(history)
        response_text = llm_result.content
        history.add_assistant_message(response_text)

        # Get previous state for continuity
        prev_state = store.get_prev_state_for_inference()

        # Run inference on user message
        context = InferenceContext(
            user_message=message.content,
            assistant_message=response_text,
            conversation_context=history.get_context_for_embedding(include_latest_turn=False),
            prev_state=prev_state,
        )
        affect_state = await self._inference.infer(context)

        # Convert to wave parameter
        wave_param = convert_to_wave_parameter(affect_state)

        # Store turn
        store.store_turn(
            user_message=message.content,
            assistant_message=response_text,
            affect_state=affect_state,
            wave_parameter=wave_param,
        )

        # Render wave based on mode
        wave_display = render_wave_text(
            wave_param,
            self.config.affect_output_mode.value,
        )

        return wave_display, response_text

    async def analyze_conversation(
        self,
        channel_id: int,
        user_message: str,
        assistant_message: str,
    ) -> tuple[str, dict]:
        """Analyze a conversation pair (user + assistant).

        This is the main method for external agents to use.

        Args:
            channel_id: Discord channel ID.
            user_message: User's message.
            assistant_message: Assistant's response.

        Returns:
            Tuple of (wave_display, wave_parameter dict).
        """
        if not self._inference:
            await self.initialize()

        store = self._get_store(channel_id)

        # Get previous state for continuity
        prev_state = store.get_prev_state_for_inference()

        # Run inference
        context = InferenceContext(
            user_message=user_message,
            assistant_message=assistant_message,
            conversation_context="",
            prev_state=prev_state,
        )
        affect_state = await self._inference.infer(context)

        # Convert to wave parameter
        wave_param = convert_to_wave_parameter(affect_state)

        # Store turn
        store.store_turn(
            user_message=user_message,
            assistant_message=assistant_message,
            affect_state=affect_state,
            wave_parameter=wave_param,
        )

        # Render wave
        wave_display = render_wave_text(
            wave_param,
            self.config.affect_output_mode.value,
        )

        return wave_display, wave_param.to_dict()

    async def send_response(
        self,
        message: discord.Message,
        wave_display: str,
        response_text: str,
    ) -> None:
        """Send response to Discord channel.

        Args:
            message: Original message (for reply).
            wave_display: Wave display string.
            response_text: Response content.
        """
        if self.config.discord_transport == DiscordTransport.REPLY_PREFIX:
            # Combine wave + response (wave_display is already rendered)
            full_response = f"{wave_display}\n\n{response_text}"
            await message.reply(full_response)

        elif self.config.discord_transport == DiscordTransport.WEBHOOK:
            # Webhook mode (optional)
            if self.config.discord_webhook_url:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            self.config.discord_webhook_url,
                            json={"content": wave_display},
                        )
                    await message.reply(response_text)
                except Exception:
                    full_response = f"{wave_display}\n\n{response_text}"
                    await message.reply(full_response)
            else:
                # Fallback to reply_prefix
                full_response = f"{wave_display}\n\n{response_text}"
                await message.reply(full_response)

    def create_bot(self) -> discord.Client:
        """Create and configure Discord bot.

        Returns:
            Configured discord.Client instance.
        """
        if discord is None or app_commands is None:
            raise ModuleNotFoundError(
                "discord.py is not installed. Install with `pip install .[discord]`."
            )

        intents = discord.Intents.default()
        intents.message_content = True

        client = discord.Client(intents=intents)
        self._bot = client
        tree = app_commands.CommandTree(client)
        self._command_tree = tree

        affect_group = app_commands.Group(name="affect", description="affect-wave controls")

        @affect_group.command(name="wave", description="Show the latest wave display")
        async def affect_wave(interaction: discord.Interaction) -> None:
            channel = interaction.channel
            channel_id = getattr(channel, "id", None)
            if channel_id is None:
                await interaction.response.send_message("Channel context is not available.", ephemeral=True)
                return

            wave_display = self._build_wave_display(channel_id)
            if wave_display is None:
                await interaction.response.send_message("No analyzed turn is available yet.", ephemeral=True)
                return

            await interaction.response.send_message(wave_display, ephemeral=True)

        @affect_group.command(name="params", description="Show the latest params payload")
        async def affect_params(interaction: discord.Interaction) -> None:
            channel = interaction.channel
            channel_id = getattr(channel, "id", None)
            if channel_id is None:
                await interaction.response.send_message("Channel context is not available.", ephemeral=True)
                return

            payload = self._build_params_payload(channel_id)
            if payload is None:
                await interaction.response.send_message("No analyzed turn is available yet.", ephemeral=True)
                return

            await interaction.response.send_message(
                f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```",
                ephemeral=True,
            )

        @affect_group.command(name="transport", description="Switch Discord transport")
        @app_commands.describe(mode="reply_prefix or webhook")
        async def affect_transport(
            interaction: discord.Interaction,
            mode: str,
        ) -> None:
            normalized = mode.strip().lower()
            if normalized not in {
                DiscordTransport.REPLY_PREFIX.value,
                DiscordTransport.WEBHOOK.value,
            }:
                await interaction.response.send_message(
                    "Transport must be `reply_prefix` or `webhook`.",
                    ephemeral=True,
                )
                return

            transport = DiscordTransport(normalized)
            result = await self.set_transport(transport)
            await interaction.response.send_message(result, ephemeral=True)

        tree.add_command(affect_group)

        @client.event
        async def on_ready() -> None:
            print(f"Logged in as {client.user}")
            print(f"Mode: {self.config.affect_output_mode.value}")
            try:
                await tree.sync()
            except Exception as e:
                print(f"Warning: failed to sync slash commands: {e}")

        @client.event
        async def on_message(message: discord.Message) -> None:
            # Ignore own messages
            if message.author == client.user:
                return

            # Only respond to mentions or DMs
            is_mentioned = client.user in message.mentions
            is_dm = isinstance(message.channel, discord.DMChannel)

            if not (is_mentioned or is_dm):
                return

            try:
                if self.is_params_trigger(message.content):
                    handled = await self.handle_params_request(message)
                    if handled:
                        return

                wave_display, response_text = await self.process_message(message)
                await self.send_response(message, wave_display, response_text)
            except Exception as e:
                error_msg = f"Error processing message: {e}"
                print(error_msg)
                await message.reply("Sorry, an error occurred.")

        return client

    async def run(self) -> None:
        """Run the Discord bot."""
        if not self.config.discord_bot_token:
            raise ValueError("DISCORD_BOT_TOKEN is required")

        await self.initialize()
        client = self.create_bot()
        await client.start(self.config.discord_bot_token)

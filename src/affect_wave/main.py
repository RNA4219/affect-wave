"""Main CLI entry point for affect-wave."""

import json
from pathlib import Path
from typing import Optional

import click

from affect_wave.config import Config, OutputMode


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Affect Wave - Affect expression interface for LLM conversations."""
    ctx.ensure_object(dict)


@cli.command()
@click.option(
    "--host",
    default=None,
    help="Host address (overrides API_HOST env var)",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="Port number (overrides API_PORT env var)",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to .env file",
)
@click.pass_context
def serve(
    ctx: click.Context,
    host: Optional[str],
    port: Optional[int],
    env_file: Optional[Path],
) -> None:
    """Start HTTP API server for external agent integration."""
    from affect_wave.api.server import run_server

    config = Config.from_env(env_file)

    # Validate
    errors = config.validate_for_serve()
    if errors:
        for error in errors:
            click.echo(f"ERROR: {error}", err=True)
        ctx.exit(1)

    click.echo(f"Starting affect-wave API server...")
    click.echo(f"Host: {host or config.api_host}")
    click.echo(f"Port: {port or config.api_port}")
    click.echo(f"Embedding URL: {config.llama_cpp_base_url}")

    try:
        run_server(config, host, port)
    except KeyboardInterrupt:
        click.echo("\nServer stopped.")


@cli.command()
@click.option("--turn", "turn_id", default=None, help="Turn ID to inspect")
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to .env file",
)
@click.pass_context
def inspect(ctx: click.Context, turn_id: Optional[str], env_file: Optional[Path]) -> None:
    """Inspect affect state for a turn (from state log)."""
    config = Config.from_env(env_file)

    # Read from state log if available
    if not config.state_log_enabled or not config.state_log_path.exists():
        click.echo("No state log available.", err=True)
        ctx.exit(1)

    turns = []
    with open(config.state_log_path) as f:
        for line in f:
            if line.strip():
                turns.append(json.loads(line))

    if turn_id:
        found = None
        for t in turns:
            if t.get("turn_id") == turn_id:
                found = t
                break
        if found:
            click.echo(json.dumps(found, indent=2))
        else:
            click.echo(f"Turn '{turn_id}' not found.", err=True)
    else:
        # Show latest turn
        if turns:
            click.echo(json.dumps(turns[-1], indent=2))
        else:
            click.echo("No turns available.", err=True)


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["wave", "params"]),
    default="wave",
    help="Render mode",
)
@click.option("--turn", "turn_id", default=None, help="Turn ID to render")
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to .env file",
)
@click.pass_context
def render(
    ctx: click.Context,
    mode: str,
    turn_id: Optional[str],
    env_file: Optional[Path],
) -> None:
    """Render wave parameter for a turn (from state log)."""
    config = Config.from_env(env_file)

    if not config.state_log_enabled or not config.state_log_path.exists():
        click.echo("No state log available.", err=True)
        ctx.exit(1)

    turns = []
    with open(config.state_log_path) as f:
        for line in f:
            if line.strip():
                turns.append(json.loads(line))

    if turn_id:
        found = None
        for t in turns:
            if t.get("turn_id") == turn_id:
                found = t
                break
        if found:
            wave_param = found.get("wave_parameter", {})
            if mode == "wave":
                from affect_wave.wave.converter import render_wave_text
                from affect_wave.state.schemas import WaveParameter
                wp = WaveParameter(**wave_param)
                click.echo(render_wave_text(wp, "wave"))
            else:
                click.echo(json.dumps(wave_param, indent=2))
        else:
            click.echo(f"Turn '{turn_id}' not found.", err=True)
    else:
        # Render latest turn
        if turns:
            wave_param = turns[-1].get("wave_parameter", {})
            if mode == "wave":
                from affect_wave.wave.converter import render_wave_text
                from affect_wave.state.schemas import WaveParameter
                wp = WaveParameter(**wave_param)
                click.echo(render_wave_text(wp, "wave"))
            else:
                click.echo(json.dumps(wave_param, indent=2))
        else:
            click.echo("No turns available.", err=True)


@cli.command()
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Number of recent turns to show",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to .env file",
)
@click.pass_context
def recent(ctx: click.Context, limit: int, env_file: Optional[Path]) -> None:
    """Show recent turns (from state log)."""
    config = Config.from_env(env_file)

    if not config.state_log_enabled or not config.state_log_path.exists():
        click.echo("No state log available.", err=True)
        ctx.exit(1)

    turns = []
    with open(config.state_log_path) as f:
        for line in f:
            if line.strip():
                turns.append(json.loads(line))

    # Show last N turns
    recent_turns = turns[-limit:] if len(turns) > limit else turns

    if recent_turns:
        for t in reversed(recent_turns):
            affect = t.get("affect_state", {})
            compact = affect.get("compact_state", {})
            trend = affect.get("trend", {})
            click.echo(
                f"[{t.get('turn_id')}] {compact.get('dominant', 'N/A')} "
                f"(valence: {trend.get('valence', 0):.2f}) {t.get('timestamp', '')}"
            )
    else:
        click.echo("No turns available.")


@cli.command()
@click.option("--turn", "turn_id", default=None, help="Turn ID to debug")
@click.option(
    "--top",
    type=int,
    default=20,
    help="Number of top concepts to show",
)
@click.option(
    "--all-concepts",
    is_flag=True,
    default=False,
    help="Show all 171 concepts",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to .env file",
)
@click.pass_context
def debug(
    ctx: click.Context,
    turn_id: Optional[str],
    top: int,
    all_concepts: bool,
    env_file: Optional[Path],
) -> None:
    """Debug: Show all 171 concept scores for a turn."""
    config = Config.from_env(env_file)

    if not config.state_log_enabled or not config.state_log_path.exists():
        click.echo("No state log available.", err=True)
        ctx.exit(1)

    turns = []
    with open(config.state_log_path) as f:
        for line in f:
            if line.strip():
                turns.append(json.loads(line))

    # Find the turn
    target_turn = None
    if turn_id:
        for t in turns:
            if t.get("turn_id") == turn_id:
                target_turn = t
                break
        if not target_turn:
            click.echo(f"Turn '{turn_id}' not found.", err=True)
            ctx.exit(1)
    else:
        # Use latest turn
        if turns:
            target_turn = turns[-1]
        else:
            click.echo("No turns available.", err=True)
            ctx.exit(1)

    # Get concept scores from stored state
    affect_state = target_turn.get("affect_state", {})
    concept_scores = affect_state.get("concept_scores", [])
    concept_count = len(concept_scores)

    click.echo(f"Turn: {target_turn.get('turn_id')}")
    click.echo(f"Concept count: {concept_count}")
    click.echo(f"Top emotions: {affect_state.get('top_emotions', [])}")
    click.echo("")

    # Show concept scores
    if concept_scores:
        show_count = len(concept_scores) if all_concepts else min(top, len(concept_scores))
        click.echo(f"Concept scores (top {show_count}):")
        click.echo("-" * 60)

        for cs in concept_scores[:show_count]:
            click.echo(
                f"  {cs.get('id', 'unknown'):15} | "
                f"{cs.get('label', 'unknown'):20} | "
                f"{cs.get('canonical', 'unknown'):10} | "
                f"{cs.get('score', 0):.3f}"
            )

        if not all_concepts and len(concept_scores) > top:
            click.echo(f"  ... and {len(concept_scores) - top} more (use --all-concepts to see all)")
    else:
        click.echo("No concept scores stored. Run analysis with STATE_LOG_ENABLED=true")


@cli.command(name="discord")
@click.option(
    "--env-file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to .env file",
)
@click.pass_context
def discord_cmd(ctx: click.Context, env_file: Optional[Path]) -> None:
    """Run Discord bot."""
    import asyncio

    from affect_wave.adapters.discord import DiscordAdapter

    config = Config.from_env(env_file)

    errors = config.validate_for_discord()
    if errors:
        for error in errors:
            click.echo(f"ERROR: {error}", err=True)
        ctx.exit(1)

    adapter = DiscordAdapter(config)

    try:
        asyncio.run(adapter.run())
    except KeyboardInterrupt:
        click.echo("\nBot stopped.")


if __name__ == "__main__":
    cli()
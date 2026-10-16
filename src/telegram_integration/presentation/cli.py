"""Command-line interface built with Typer.

This module is intentionally thin: each command instantiates the required
infrastructure adapters, injects them into an application use case and calls
``execute``. All presentation concerns (echoing, exit codes, ``Ctrl+C``
handling) stay here, while the use cases remain framework-free.

Two console entry points are exposed:

* ``telegram-send`` / ``telegram-listen`` -- single-command apps kept for
  backwards compatibility and shell ergonomics.
* ``telegram-integration`` -- a unified app exposing ``send`` and ``listen``
  as subcommands, plus a hidden ``completion`` command.
"""

from __future__ import annotations

from typing import Any, NoReturn

import typer

from ..application import ListenMessagesUseCase, SendMessageUseCase
from ..client import TelegramClient
from ..domain import TelegramIntegrationError
from ..infrastructure import (
    ScriptRunner,
    SqliteStateRepository,
    TelegramConfig,
    TelegramConfigError,
    load_config,
)
from .completions import register_completion

app = typer.Typer(
    help="Send and receive Telegram messages through the Bot API.",
    no_args_is_help=True,
)
send_app = typer.Typer(help="Send a message to a Telegram channel.")
listen_app = typer.Typer(help="Listen for messages in a Telegram channel.")


def _resolve_config(token: str | None, channel_id: str | None) -> TelegramConfig:
    """Build the configuration from CLI flags, the XDG file and the environment.

    Explicit ``--token`` / ``--channel-id`` flags win; any value not provided
    on the command line is completed from the XDG configuration file (or the
    ``TELEGRAM_TOKEN`` / ``TELEGRAM_CHANNEL_ID`` environment fallback).

    Args:
        token: Bot token passed on the command line, if any.
        channel_id: Channel id passed on the command line, if any.

    Returns:
        A validated configuration.

    Raises:
        telegram_integration.infrastructure.ConfigFileNotFoundError: When a
            value is missing on the command line and no configuration file or
            environment fallback exists.
    """
    if token is None or channel_id is None:
        stored = load_config()
        token = token if token is not None else stored.token
        channel_id = channel_id if channel_id is not None else stored.chat_id
    return TelegramConfig(token=token, chat_id=channel_id)


def _build_client(config: TelegramConfig) -> TelegramClient:
    """Create the Telegram gateway from a resolved configuration.

    Args:
        config: The application configuration.

    Returns:
        A ready-to-use :class:`~telegram_integration.client.TelegramClient`.
    """
    return TelegramClient(token=config.token, channel_id=config.chat_id)


def _fail(message: object) -> NoReturn:
    """Print an error message to stderr and abort with exit code 1.

    Args:
        message: The error to display.
    """
    typer.secho(f"Error: {message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


@send_app.command("send")
def send(
    message: str = typer.Argument(..., help="Message to send."),
    mode: str = typer.Option(
        "markdown",
        "--mode",
        "-m",
        help="Message parse mode: markdown, html or plain.",
    ),
    token: str | None = typer.Option(
        None, "--token", envvar="TELEGRAM_TOKEN", help="Telegram bot token."
    ),
    channel_id: str | None = typer.Option(
        None,
        "--channel-id",
        envvar="TELEGRAM_CHANNEL_ID",
        help="Telegram channel or chat id.",
    ),
) -> None:
    """Send a message to a Telegram channel.

    The message text is sent using the requested parse mode so that Markdown
    or HTML formatting is preserved in Telegram.
    """
    try:
        config = _resolve_config(token, channel_id)
        result = SendMessageUseCase(_build_client(config), config).execute(
            message, mode
        )
    except (TelegramIntegrationError, TelegramConfigError) as exc:
        _fail(exc)

    typer.echo(
        "Message sent successfully: "
        f"id={result.message_id} chat={result.chat_id} mode={result.mode}"
    )


@listen_app.command("listen")
def listen(
    timeout: int = typer.Option(30, "--timeout", help="Long polling timeout."),
    interval: float = typer.Option(1.0, "--interval", help="Poll interval seconds."),
    scripts: list[str] | None = typer.Option(
        None,
        "--scripts",
        "-s",
        help=(
            "External scripts to run for each received message. The update is "
            "passed as JSON through the TELEGRAM_MESSAGE environment variable."
        ),
    ),
    token: str | None = typer.Option(
        None, "--token", envvar="TELEGRAM_TOKEN", help="Telegram bot token."
    ),
    channel_id: str | None = typer.Option(
        None,
        "--channel-id",
        envvar="TELEGRAM_CHANNEL_ID",
        help="Telegram channel or chat id.",
    ),
) -> None:
    """Listen for incoming Telegram messages until interrupted (Ctrl+C).

    The last processed offset is persisted under the XDG data directory so
    that restarting does not reprocess already handled updates.
    """
    script_runner = ScriptRunner(scripts) if scripts else None

    def on_update(update: dict[str, Any]) -> None:
        """Echo the update and, when configured, trigger external scripts."""
        typer.echo(f"Update received: {update}")
        if script_runner is not None:
            script_runner.run(update)

    try:
        config = _resolve_config(token, channel_id)
        use_case = ListenMessagesUseCase(
            _build_client(config),
            config,
            SqliteStateRepository(),
            timeout=timeout,
            poll_interval=interval,
        )
        use_case.execute(on_update)
    except KeyboardInterrupt:
        typer.echo("\nStopped listening.", err=True)
    except (TelegramIntegrationError, TelegramConfigError) as exc:
        _fail(exc)


# The unified `telegram-integration` app exposes the two main commands.
app.command("send")(send)
app.command("listen")(listen)
register_completion(app)


if __name__ == "__main__":
    app()

"""Command-line interface built with Typer.

This module exposes two standalone Typer applications, one for sending
messages and another for listening for incoming updates. The same functions
power the repository ``scripts/`` and the ``telegram-send`` /
``telegram-listen`` console entry points.
"""

from typing import List, Optional

import typer

from .receiver import MessageReceiver
from .sender import MessageSender

send_app = typer.Typer(help="Send a message to a Telegram channel.")
listen_app = typer.Typer(help="Listen for messages in a Telegram channel.")


def _message_handler(message: dict) -> None:
    """Default handler that echoes any received update to the console."""
    typer.echo(f"Update received: {message}")


@send_app.command("send")
def send(
    message: str = typer.Argument(..., help="Message to send."),
    mode: str = typer.Option(
        "markdown",
        "--mode",
        "-m",
        help="Message parse mode: markdown, html or plain.",
    ),
    token: Optional[str] = typer.Option(
        None, "--token", envvar="TELEGRAM_TOKEN", help="Telegram bot token."
    ),
    channel_id: Optional[str] = typer.Option(
        None,
        "--channel-id",
        envvar="TELEGRAM_CHANNEL_ID",
        help="Telegram channel or chat id.",
    ),
) -> None:
    """Send a message to a Telegram channel.

    The message text is sent using the requested parse mode so that
    Markdown or HTML formatting is preserved in Telegram.
    """
    if token or channel_id:
        from .client import TelegramClient

        sender = MessageSender(TelegramClient(token=token, channel_id=channel_id))
    else:
        sender = MessageSender()

    mode = mode.lower()
    if mode == "html":
        result = sender.send_html(message)
    elif mode == "plain":
        result = sender.send_plain(message)
    else:
        result = sender.send_markdown(message)

    if isinstance(result, dict) and result.get("ok"):
        typer.echo(f"Message sent successfully: {result}")
        raise typer.Exit(0)
    typer.echo(f"Failed to send message: {result}", err=True)
    raise typer.Exit(1)


@listen_app.command("listen")
def listen(
    timeout: int = typer.Option(30, "--timeout", help="Long polling timeout."),
    interval: float = typer.Option(1.0, "--interval", help="Poll interval seconds."),
    scripts: Optional[List[str]] = typer.Option(
        None,
        "--scripts",
        "-s",
        help="External scripts to trigger for each received message.",
    ),
    token: Optional[str] = typer.Option(
        None, "--token", envvar="TELEGRAM_TOKEN", help="Telegram bot token."
    ),
    channel_id: Optional[str] = typer.Option(
        None,
        "--channel-id",
        envvar="TELEGRAM_CHANNEL_ID",
        help="Telegram channel or chat id.",
    ),
) -> None:
    """Listen for incoming Telegram messages continuously.

    Each received update is passed to the registered callback and any
    configured ``--scripts`` are triggered via a subprocess.
    """
    if token or channel_id:
        from .client import TelegramClient

        receiver = MessageReceiver(
            TelegramClient(token=token, channel_id=channel_id)
        )
    else:
        receiver = MessageReceiver()

    receiver.register_callback(_message_handler)
    if scripts:
        receiver.register_callback(
            lambda update: receiver.trigger_scripts(update, scripts)
        )

    receiver.listen(timeout=timeout, poll_interval=interval)


if __name__ == "__main__":
    send_app()
"""Telegram Bot API client.

The :class:`TelegramClient` is a thin wrapper around the Telegram Bot
HTTP API. It handles authentication via the bot token and exposes two
common operations: sending a message and long-polling for updates.

Credentials are resolved through
:func:`telegram_integration.infrastructure.load_config`, which reads the XDG
configuration file (``~/.config/telegram-send/config.toml``) and falls back to
the ``TELEGRAM_TOKEN`` and ``TELEGRAM_CHANNEL_ID`` environment variables.
"""

from typing import Any, cast

import requests

from .infrastructure import load_config

API_BASE = "https://api.telegram.org"


class TelegramClient:
    """Handles communication with the Telegram Bot API.

    The bot token and the default chat (channel) identifier are read from the
    XDG configuration file unless explicitly provided, falling back to the
    ``TELEGRAM_TOKEN`` and ``TELEGRAM_CHANNEL_ID`` environment variables.

    Args:
        token: Telegram bot token obtained from BotFather. When omitted it is
            read from the configuration.
        channel_id: Chat or channel id where messages are sent. When omitted
            it is read from the configuration.

    Raises:
        telegram_integration.infrastructure.ConfigFileNotFoundError: When no
            explicit credentials are given and neither a configuration file
            nor the environment fallback provides them.
    """

    def __init__(self, token: str | None = None, channel_id: str | None = None) -> None:
        if token is None or channel_id is None:
            config = load_config()
            token = token if token is not None else config.token
            channel_id = channel_id if channel_id is not None else config.chat_id

        self.token = token
        self.channel_id = channel_id
        self.base_url = f"{API_BASE}/bot{self.token}"

    def send_message(
        self, text: str, parse_mode: str | None = "Markdown"
    ) -> dict[str, Any]:
        """Send a text message to the configured channel.

        Args:
            text: The message body to send.
            parse_mode: ``Markdown``, ``HTML`` or ``None`` for plain text.

        Returns:
            The Telegram API response dictionary.

        Raises:
            requests.HTTPError: When the API returns an error status code.
        """
        response = requests.post(
            f"{self.base_url}/sendMessage",
            json={
                "chat_id": self.channel_id,
                "text": text,
                "parse_mode": parse_mode,
            },
        )
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    def get_updates(
        self, offset: int | None = None, timeout: int = 30
    ) -> dict[str, Any]:
        """Long-poll for incoming updates.

        Args:
            offset: Update id from which to start receiving updates.
            timeout: Polling timeout in seconds.

        Returns:
            The Telegram API response with a ``result`` list.

        Raises:
            requests.HTTPError: When the API returns an error status code.
        """
        params: dict[str, int] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        response = requests.get(
            f"{self.base_url}/getUpdates",
            params=params,
        )
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

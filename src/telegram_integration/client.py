"""Telegram Bot API client.

The :class:`TelegramClient` is a thin wrapper around the Telegram Bot
HTTP API. It handles authentication via the bot token and exposes two
common operations: sending a message and long-polling for updates.
"""

import os
from typing import Any, Dict, Optional

import dotenv
import requests

dotenv.load_dotenv()

API_BASE = "https://api.telegram.org"


class TelegramClient:
    """Handles communication with the Telegram Bot API.

    The bot token and the default chat (channel) identifier are read from
    the ``TELEGRAM_TOKEN`` and ``TELEGRAM_CHANNEL_ID`` environment
    variables unless explicitly provided.

    :param token: Telegram bot token obtained from BotFather.
    :param channel_id: Chat or channel id where messages are sent.
    :raises ValueError: When the token or channel id are missing.
    """

    def __init__(self, token: Optional[str] = None, channel_id: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_TOKEN")
        self.channel_id = channel_id or os.getenv("TELEGRAM_CHANNEL_ID")

        if not self.token:
            raise ValueError("TELEGRAM_TOKEN is required")
        if not self.channel_id:
            raise ValueError("TELEGRAM_CHANNEL_ID is required")

        self.base_url = f"{API_BASE}/bot{self.token}"

    def send_message(self, text: str, parse_mode: str = "Markdown") -> Dict[str, Any]:
        """Send a text message to the configured channel.

        :param text: The message body to send.
        :param parse_mode: ``Markdown``, ``HTML`` or ``None`` for plain.
        :returns: The Telegram API response dictionary.
        :raises requests.HTTPError: When the API returns an error.
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
        return response.json()

    def get_updates(self, offset: Optional[int] = None, timeout: int = 30) -> Dict[str, Any]:
        """Long-poll for incoming updates.

        :param offset: Update id from which to start receiving updates.
        :param timeout: Polling timeout in seconds.
        :returns: The Telegram API response with a ``result`` list.
        :raises requests.HTTPError: When the API returns an error.
        """
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        response = requests.get(
            f"{self.base_url}/getUpdates",
            params=params,
        )
        response.raise_for_status()
        return response.json()
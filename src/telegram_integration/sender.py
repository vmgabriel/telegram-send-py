"""Message sending helpers.

The :class:`MessageSender` wraps a
:class:`telegram_integration.client.TelegramClient` and provides convenience
methods for the different Telegram parse modes.
"""

from typing import Any

from .client import TelegramClient


class MessageSender:
    """Sends messages through a Telegram client.

    Args:
        client: A :class:`TelegramClient` instance. When omitted a new client
            is created from the configuration.
    """

    def __init__(self, client: TelegramClient | None = None) -> None:
        self.client = client or TelegramClient()

    def send_markdown(self, markdown_text: str) -> dict[str, Any]:
        """Send a message using Markdown formatting.

        Args:
            markdown_text: Message body with Markdown markup.

        Returns:
            The Telegram API response.
        """
        return self.client.send_message(text=markdown_text, parse_mode="Markdown")

    def send_plain(self, text: str) -> dict[str, Any]:
        """Send a plain text message without formatting.

        Args:
            text: Message body.

        Returns:
            The Telegram API response.
        """
        return self.client.send_message(text=text, parse_mode=None)

    def send_html(self, html_text: str) -> dict[str, Any]:
        """Send a message using HTML formatting.

        Args:
            html_text: Message body with HTML markup.

        Returns:
            The Telegram API response.
        """
        return self.client.send_message(text=html_text, parse_mode="HTML")

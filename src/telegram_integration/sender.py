"""Message sending helpers.

The :class:`MessageSender` wraps a :class:`telegram_integration.client.TelegramClient`
and provides convenience methods for the different Telegram parse modes.
"""

from typing import Optional

from .client import TelegramClient


class MessageSender:
    """Sends messages through a Telegram client.

    :param client: A :class:`TelegramClient` instance. When omitted a new
        client is created from the environment configuration.
    """

    def __init__(self, client: Optional[TelegramClient] = None):
        self.client = client or TelegramClient()

    def send_markdown(self, markdown_text: str) -> dict:
        """Send a message using Markdown formatting.

        :param markdown_text: Message body with Markdown markup.
        :returns: The Telegram API response.
        """
        return self.client.send_message(text=markdown_text, parse_mode="Markdown")

    def send_plain(self, text: str) -> dict:
        """Send a plain text message without formatting.

        :param text: Message body.
        :returns: The Telegram API response.
        """
        return self.client.send_message(text=text, parse_mode=None)

    def send_html(self, html_text: str) -> dict:
        """Send a message using HTML formatting.

        :param html_text: Message body with HTML markup.
        :returns: The Telegram API response.
        """
        return self.client.send_message(text=html_text, parse_mode="HTML")
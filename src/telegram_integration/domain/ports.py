"""Outbound ports (gateways) for the domain and application layers.

Ports describe the behaviour the application needs from the outside world
without committing to any implementation. The concrete adapters live in the
infrastructure layer and satisfy these protocols through structural typing.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TelegramGateway(Protocol):
    """Port describing the Telegram Bot API operations used by the application.

    :class:`telegram_integration.client.TelegramClient` is the production
    adapter; a hand-written fake or a :class:`unittest.mock.Mock` can be used
    in tests.
    """

    def send_message(
        self,
        text: str,
        parse_mode: str | None = "Markdown",
        chat_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a text message.

        Args:
            text: The message body to send.
            parse_mode: ``Markdown``, ``HTML`` or ``None`` for plain text.
            chat_id: Target chat. When ``None`` the adapter default is used.

        Returns:
            The raw Telegram API response as a dictionary.
        """
        ...

    def get_updates(
        self, offset: int | None = None, timeout: int = 30
    ) -> dict[str, Any]:
        """Long-poll for incoming updates.

        Args:
            offset: Update id from which to start receiving updates.
            timeout: Polling timeout in seconds.

        Returns:
            The raw Telegram API response as a dictionary.
        """
        ...

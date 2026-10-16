"""Send-message use case.

The use case depends only on the ``TelegramGateway`` port and the application
configuration, both injected through the constructor. It knows nothing about
Typer, ``requests`` or the terminal.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.exceptions import (
    InvalidMessageError,
    InvalidMessageModeError,
    MessageSendError,
)
from ..domain.ports import TelegramGateway
from ..infrastructure import TelegramConfig

_MODE_TO_PARSE_MODE: dict[str, str | None] = {
    "markdown": "Markdown",
    "html": "HTML",
    "plain": None,
}


@dataclass(frozen=True, slots=True)
class SendMessageResult:
    """Outcome of a successful :class:`SendMessageUseCase` execution.

    Attributes:
        message_id: Identifier assigned by Telegram, or ``None`` when the API
            did not return one.
        chat_id: Chat the message was sent to.
        mode: Normalised parse mode used to send the message.
    """

    message_id: int | None
    chat_id: str
    mode: str


class SendMessageUseCase:
    """Send a single message through the Telegram gateway.

    Args:
        gateway: Outbound port used to talk to the Telegram Bot API.
        config: Application configuration providing the target chat.
    """

    def __init__(self, gateway: TelegramGateway, config: TelegramConfig) -> None:
        self._gateway = gateway
        self._config = config

    def execute(self, text: str, mode: str) -> SendMessageResult:
        """Send ``text`` to the configured chat using ``mode``.

        Args:
            text: Message body.
            mode: One of ``markdown``, ``html`` or ``plain``
                (case-insensitive).

        Returns:
            The result of the operation.

        Raises:
            InvalidMessageError: If ``text`` is empty or blank.
            InvalidMessageModeError: If ``mode`` is not supported.
            MessageSendError: If the Telegram API rejects the message.
        """
        if not text.strip():
            raise InvalidMessageError("The message text must not be empty")

        normalized_mode = mode.strip().lower()
        if normalized_mode not in _MODE_TO_PARSE_MODE:
            supported = ", ".join(sorted(_MODE_TO_PARSE_MODE))
            raise InvalidMessageModeError(
                f"Unsupported mode {mode!r}; expected one of: {supported}"
            )

        response = self._gateway.send_message(
            text=text,
            parse_mode=_MODE_TO_PARSE_MODE[normalized_mode],
            chat_id=self._config.chat_id,
        )
        if not response.get("ok"):
            raise MessageSendError(
                str(response.get("description", "Telegram API rejected the message"))
            )

        payload = response.get("result")
        message_id = payload.get("message_id") if isinstance(payload, dict) else None
        return SendMessageResult(
            message_id=int(message_id) if message_id is not None else None,
            chat_id=self._config.chat_id,
            mode=normalized_mode,
        )

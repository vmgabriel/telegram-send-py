"""Domain exceptions.

Use cases signal failures with these exceptions so that callers (the CLI,
scripts, tests, ...) never need to depend on an infrastructure library such as
``requests`` or ``sqlite3``.
"""

from __future__ import annotations


class TelegramIntegrationError(Exception):
    """Base class for every domain error raised by the application."""


class InvalidMessageError(TelegramIntegrationError, ValueError):
    """Raised when a message body is empty or otherwise invalid."""


class InvalidMessageModeError(TelegramIntegrationError, ValueError):
    """Raised when an unsupported message parse mode is requested."""


class MessageSendError(TelegramIntegrationError):
    """Raised when the Telegram API rejects a message."""


class PollingError(TelegramIntegrationError):
    """Raised when polling Telegram for updates fails."""

"""Telegram integration package.

Public API exposing :class:`~telegram_integration.client.TelegramClient`,
:class:`~telegram_integration.sender.MessageSender` and
:class:`~telegram_integration.receiver.MessageReceiver`.
"""

from .client import TelegramClient
from .receiver import MessageReceiver
from .sender import MessageSender

__version__ = "1.0.0"
__all__ = ["TelegramClient", "MessageSender", "MessageReceiver"]

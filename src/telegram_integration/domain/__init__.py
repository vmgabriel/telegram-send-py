"""Domain layer.

This package holds the pure business objects, the domain exceptions and the
repository/gateway *ports* (interfaces) that the application depends on. It
must not import any infrastructure concern such as :mod:`sqlite3`,
:mod:`platformdirs` or :mod:`requests`.
"""

from .entities import ListenerState
from .exceptions import (
    InvalidMessageError,
    InvalidMessageModeError,
    MessageSendError,
    PollingError,
    TelegramIntegrationError,
)
from .ports import TelegramGateway
from .repositories import ListenerStateRepository

__all__ = [
    "InvalidMessageError",
    "InvalidMessageModeError",
    "ListenerState",
    "ListenerStateRepository",
    "MessageSendError",
    "PollingError",
    "TelegramGateway",
    "TelegramIntegrationError",
]

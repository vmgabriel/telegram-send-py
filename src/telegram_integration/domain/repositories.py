"""Repository ports (interfaces) for the domain layer.

Defining the persistence contract as a :class:`typing.Protocol` keeps the
domain and application layers independent from any concrete adapter: the
SQLite implementation in the infrastructure layer simply satisfies the
protocol through structural typing (dependency inversion).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from .entities import ListenerState


@runtime_checkable
class ListenerStateRepository(Protocol):
    """Persistence port for the listener state.

    Any object exposing the methods below satisfies this protocol, so it can
    be substituted in tests by an in-memory fake without importing SQLite.
    """

    def get_offset(self) -> int | None:
        """Return the persisted offset.

        Returns:
            The stored offset, or ``None`` when nothing has been persisted yet.
        """
        ...

    def get_state(self) -> ListenerState | None:
        """Return the full persisted state.

        Returns:
            The stored :class:`ListenerState`, or ``None`` when nothing has
            been persisted yet.
        """
        ...

    def save_offset(self, offset: int, updated_at: datetime | None = None) -> None:
        """Persist the listener offset.

        Args:
            offset: Offset to consume next (``update_id + 1``).
            updated_at: Timestamp of the update. When omitted, the current UTC
                time is used.
        """
        ...

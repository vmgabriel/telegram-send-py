"""Domain entities for the Telegram integration.

Entities are pure business objects with no dependency on frameworks, I/O or
persistence. They live in the *domain* layer and are shared by the
application and infrastructure layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ListenerState:
    """Last known state of the Telegram update listener.

    The listener stores the offset it must send to the Bot API ``getUpdates``
    method so that restarts do not reprocess already handled updates.

    Attributes:
        last_offset: Offset to consume next, i.e. the ``update_id`` of the last
            processed update plus one.
        last_update_date: Timestamp of the last processed update.

    Raises:
        ValueError: If ``last_offset`` is negative.
    """

    last_offset: int
    last_update_date: datetime

    def __post_init__(self) -> None:
        """Validate the entity invariants after construction."""
        if self.last_offset < 0:
            raise ValueError("last_offset must be greater than or equal to 0")

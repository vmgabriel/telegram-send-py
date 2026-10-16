"""Listen-messages use case.

The use case long-polls the Telegram Bot API and persists the offset of the
last processed update through the injected
:class:`~telegram_integration.domain.repositories.ListenerStateRepository`
port. All collaborators are constructor-injected, so the use case has no
knowledge of Typer, ``sqlite3`` or the terminal: it returns data and raises
domain exceptions only.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ..domain.exceptions import PollingError
from ..domain.ports import TelegramGateway
from ..domain.repositories import ListenerStateRepository
from ..infrastructure import TelegramConfig

UpdateCallback = Callable[[dict[str, Any]], None]
"""Callback invoked with each received update."""


class ListenMessagesUseCase:
    """Long-poll Telegram keeping track of the last processed offset.

    Args:
        gateway: Outbound port used to talk to the Telegram Bot API.
        config: Application configuration.
        state_repository: Port persisting the last processed offset.
        timeout: Long-polling timeout in seconds.
        poll_interval: Delay between consecutive polls in seconds.
    """

    def __init__(
        self,
        gateway: TelegramGateway,
        config: TelegramConfig,
        state_repository: ListenerStateRepository,
        *,
        timeout: int = 30,
        poll_interval: float = 1.0,
    ) -> None:
        self._gateway = gateway
        self._config = config
        self._state_repository = state_repository
        self._timeout = timeout
        self._poll_interval = poll_interval
        self._running = False

    @property
    def config(self) -> TelegramConfig:
        """Return the injected application configuration."""
        return self._config

    @property
    def offset(self) -> int | None:
        """Return the last offset persisted in the state repository."""
        return self._state_repository.get_offset()

    def poll_once(
        self,
        callback: UpdateCallback | None = None,
        *,
        timeout: int | None = None,
    ) -> list[dict[str, Any]]:
        """Run a single polling cycle.

        The stored offset (when any) is sent to ``getUpdates`` so already
        processed updates are not received again. Every received update is
        persisted before being handed to ``callback``.

        Args:
            callback: Optional callable invoked once per received update.
            timeout: Overrides the configured long-polling timeout.

        Returns:
            The updates received during this cycle, in order.

        Raises:
            PollingError: If the Telegram API rejects the call or an update is
                malformed.
        """
        offset = self._state_repository.get_offset()
        response = self._gateway.get_updates(
            offset=offset,
            timeout=self._timeout if timeout is None else timeout,
        )

        if not response.get("ok"):
            raise PollingError(
                str(response.get("description", "Telegram API rejected getUpdates"))
            )

        result = response.get("result")
        updates: list[dict[str, Any]] = list(result) if isinstance(result, list) else []

        for update in updates:
            self._persist_offset(update)
            if callback is not None:
                callback(update)

        return updates

    def execute(
        self,
        callback: UpdateCallback | None = None,
        *,
        max_iterations: int | None = None,
    ) -> int | None:
        """Continuously poll for updates until stopped.

        Args:
            callback: Optional callable invoked once per received update.
            max_iterations: Optional safety bound on the number of polling
                cycles to run. ``None`` polls until :meth:`stop` is called or
                the process is interrupted.

        Returns:
            The last offset persisted when the loop finishes, or ``None`` when
            nothing was ever stored.
        """
        self._running = True
        iterations = 0
        try:
            while self._running:
                self.poll_once(callback)
                iterations += 1
                if max_iterations is not None and iterations >= max_iterations:
                    break
                if self._poll_interval:
                    time.sleep(self._poll_interval)
        finally:
            self._running = False
        return self._state_repository.get_offset()

    def stop(self) -> None:
        """Ask the polling loop to stop after the current cycle."""
        self._running = False

    def _persist_offset(self, update: dict[str, Any]) -> None:
        """Store ``update_id + 1`` as the next offset to consume.

        Args:
            update: A Telegram update dictionary.

        Raises:
            PollingError: If the update does not carry a valid ``update_id``.
        """
        update_id = update.get("update_id")
        if not isinstance(update_id, int):
            raise PollingError("Received an update without a valid 'update_id'")
        self._state_repository.save_offset(update_id + 1)

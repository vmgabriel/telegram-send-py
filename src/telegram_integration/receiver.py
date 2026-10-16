"""Message receiving and script triggering.

The :class:`MessageReceiver` long-polls the Telegram Bot API for updates
and dispatches each one to any registered callbacks. External scripts can
be triggered per message through :meth:`MessageReceiver.trigger_scripts`.
"""

import os
import subprocess
import time
from collections.abc import Callable
from typing import Any

from .client import TelegramClient


class MessageReceiver:
    """Receives Telegram updates and runs callbacks.

    Args:
        client: A :class:`TelegramClient` instance. When omitted a new client
            is created from the configuration.
    """

    def __init__(self, client: TelegramClient | None = None) -> None:
        self.client = client or TelegramClient()
        self.last_update_id: int | None = None
        self.callbacks: list[Callable[[dict[str, Any]], None]] = []

    def register_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback invoked for every received update.

        Args:
            callback: Function accepting the update dictionary.
        """
        self.callbacks.append(callback)

    def trigger_scripts(self, message: dict[str, Any], scripts: list[str]) -> None:
        """Trigger external scripts for a received message.

        Each script is launched as a subprocess and receives the full update
        payload through the ``TELEGRAM_MESSAGE`` environment variable.

        Args:
            message: The Telegram update dictionary.
            scripts: Paths of the scripts to execute.
        """
        env = {**os.environ, "TELEGRAM_MESSAGE": str(message)}
        for script in scripts:
            try:
                subprocess.Popen(["python", script], env=env)
            except Exception as exc:
                print(f"Error triggering script {script}: {exc}")

    def process_update(self, update: dict[str, Any]) -> None:
        """Dispatch a single update to all registered callbacks.

        Args:
            update: The Telegram update dictionary.
        """
        for callback in self.callbacks:
            callback(update)

    def listen(self, timeout: int = 30, poll_interval: float = 1.0) -> None:
        """Continuously poll for updates and dispatch them.

        Blocks until interrupted with ``Ctrl+C``. The offset is tracked so
        already processed updates are not received a second time.

        Args:
            timeout: Long-polling timeout in seconds.
            poll_interval: Delay between polls in seconds.
        """
        print("Starting message listener...")
        while True:
            try:
                response = self.client.get_updates(
                    offset=self.last_update_id,
                    timeout=timeout,
                )

                if response.get("ok") and response.get("result"):
                    for update in response["result"]:
                        self.process_update(update)
                        self.last_update_id = update["update_id"] + 1

                time.sleep(poll_interval)
            except KeyboardInterrupt:
                print("Stopping listener...")
                break
            except Exception as exc:
                print(f"Error: {exc}")
                time.sleep(poll_interval)

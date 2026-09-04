"""Message receiving and script triggering.

The :class:`MessageReceiver` long-polls the Telegram Bot API for updates
and dispatches each one to any registered callbacks. External scripts can
be triggered per message through :meth:`MessageReceiver.trigger_scripts`.
"""

import os
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional

from .client import TelegramClient


class MessageReceiver:
    """Receives Telegram updates and runs callbacks.

    :param client: A :class:`TelegramClient` instance. When omitted a new
        client is created from the environment configuration.
    """

    def __init__(self, client: Optional[TelegramClient] = None):
        self.client = client or TelegramClient()
        self.last_update_id: Optional[int] = None
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback invoked for every received update.

        :param callback: Function accepting the update dictionary.
        """
        self.callbacks.append(callback)

    def trigger_scripts(self, message: Dict[str, Any], scripts: List[str]) -> None:
        """Trigger external scripts for a received message.

        Each script is launched as a subprocess and receives the full
        update payload through the ``TELEGRAM_MESSAGE`` environment
        variable.

        :param message: The Telegram update dictionary.
        :param scripts: Paths of the scripts to execute.
        """
        env = {**os.environ, "TELEGRAM_MESSAGE": str(message)}
        for script in scripts:
            try:
                subprocess.Popen(["python", script], env=env)
            except Exception as exc:
                print(f"Error triggering script {script}: {exc}")

    def process_update(self, update: Dict[str, Any]) -> None:
        """Dispatch a single update to all registered callbacks.

        :param update: The Telegram update dictionary.
        """
        for callback in self.callbacks:
            callback(update)

    def listen(self, timeout: int = 30, poll_interval: float = 1.0) -> None:
        """Continuously poll for updates and dispatch them.

        Blocks until interrupted with ``Ctrl+C``. The offset is tracked so
        already processed updates are not received a second time.

        :param timeout: Long-polling timeout in seconds.
        :param poll_interval: Delay between polls in seconds.
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
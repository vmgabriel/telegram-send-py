"""External script triggering adapter.

Implements the "run one script per received update" behaviour. The full
Telegram update is exported to each script through the ``TELEGRAM_MESSAGE``
environment variable as a JSON document, mirroring the original behaviour.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from collections.abc import Iterable
from typing import Any

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_ENV: str = "TELEGRAM_MESSAGE"
"""Environment variable carrying the JSON-encoded Telegram update."""


class ScriptRunner:
    """Run external scripts once per received Telegram update.

    Args:
        scripts: Paths of the scripts to execute for every update.
        interpreter: Python interpreter used to run the scripts. Defaults to
            the interpreter currently running the application.
    """

    def __init__(
        self, scripts: Iterable[str], *, interpreter: str | None = None
    ) -> None:
        self._scripts = list(scripts)
        self._interpreter = interpreter or sys.executable

    @property
    def scripts(self) -> list[str]:
        """Return the configured scripts as a list."""
        return list(self._scripts)

    def run(self, update: dict[str, Any]) -> None:
        """Run every configured script for ``update``.

        A failure to spawn one script is logged and does not prevent the
        remaining scripts from running.

        Args:
            update: The Telegram update dictionary received from Telegram.
        """
        env = {**os.environ, TELEGRAM_MESSAGE_ENV: json.dumps(update)}
        for script in self._scripts:
            try:
                subprocess.Popen([self._interpreter, script], env=env)
            except OSError:
                logger.exception("Could not trigger script %s", script)

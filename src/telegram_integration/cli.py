"""Backwards-compatible import path for the command-line interface.

The CLI now lives in :mod:`telegram_integration.presentation.cli`. This module
re-exports its public objects so existing imports keep working unchanged.
"""

from .presentation.cli import app, listen, listen_app, send, send_app

__all__ = ["app", "listen", "listen_app", "send", "send_app"]

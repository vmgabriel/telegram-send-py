"""Presentation layer.

Typer-based command-line interface. It wires infrastructure adapters into the
application use cases and renders their results.
"""

from .cli import app, listen_app, send_app

__all__ = ["app", "listen_app", "send_app"]

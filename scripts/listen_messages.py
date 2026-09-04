#!/usr/bin/env python3
"""Listen for Telegram messages and optionally trigger external scripts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from telegram_integration.cli import listen_app

if __name__ == "__main__":
    listen_app()
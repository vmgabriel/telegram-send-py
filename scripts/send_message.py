#!/usr/bin/env python3
"""Send a message to a Telegram channel from the command line."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from telegram_integration.cli import send_app

if __name__ == "__main__":
    send_app()
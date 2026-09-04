import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

os.environ.setdefault("TELEGRAM_TOKEN", "test_token")
os.environ.setdefault("TELEGRAM_CHANNEL_ID", "test_channel_id")
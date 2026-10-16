import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture(autouse=True)
def isolated_xdg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate every test from the real user XDG directories.

    The autouse fixture points ``XDG_CONFIG_HOME`` and ``XDG_DATA_HOME`` to a
    per-test temporary directory so that a developer's real
    ``~/.config/telegram-send/config.toml`` can never influence the suite. It
    also seeds the environment fallback used by tests that do not create a
    configuration file.
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("TELEGRAM_TOKEN", "test_token")
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "test_channel_id")

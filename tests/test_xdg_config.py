"""Tests for the XDG Base Directory configuration module."""

import stat
from pathlib import Path

import pytest

from telegram_integration.infrastructure import (
    ConfigFileNotFoundError,
    InvalidConfigError,
    TelegramConfig,
    ensure_config_dir,
    get_config_dir,
    get_config_file,
    get_data_dir,
    load_config,
    write_config,
)


class TestXdgPaths:
    """The resolved paths must follow the XDG Base Directory specification."""

    def test_config_dir_uses_xdg_config_home(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))

        assert get_config_dir() == tmp_path / "xdg-config" / "telegram-send"

    def test_config_file_is_config_toml(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))

        assert (
            get_config_file()
            == tmp_path / "xdg-config" / "telegram-send" / "config.toml"
        )

    def test_data_dir_uses_xdg_data_home(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))

        assert get_data_dir() == tmp_path / "xdg-data" / "telegram-send"


class TestLoadConfigFromFile:
    """The TOML document is the primary configuration source."""

    def _write(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, body: str
    ) -> Path:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
        config_file = get_config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(body, encoding="utf-8")
        return config_file

    def _clear_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)

    def test_reads_token_and_chat_id(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._clear_env(monkeypatch)
        self._write(
            monkeypatch,
            tmp_path,
            'token = "file_token"\nchat_id = "@file_channel"\n',
        )

        config = load_config()

        assert config.token == "file_token"
        assert config.chat_id == "@file_channel"

    def test_channel_id_alias_property(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._clear_env(monkeypatch)
        self._write(monkeypatch, tmp_path, 'token = "t"\nchat_id = "@chan"\n')

        assert load_config().channel_id == "@chan"

    def test_file_takes_precedence_over_env(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "env_token")
        monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@env_channel")
        self._write(
            monkeypatch,
            tmp_path,
            'token = "file_token"\nchat_id = "@file_channel"\n',
        )

        config = load_config()

        assert config.token == "file_token"
        assert config.chat_id == "@file_channel"

    def test_partial_file_is_completed_by_env(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@env_channel")
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        self._write(monkeypatch, tmp_path, 'token = "file_token"\n')

        config = load_config()

        assert config.token == "file_token"
        assert config.chat_id == "@env_channel"

    def test_explicit_path_is_honoured(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._clear_env(monkeypatch)
        custom = tmp_path / "custom.toml"
        custom.write_text('token = "custom"\nchat_id = "@custom"\n', encoding="utf-8")

        config = load_config(custom)

        assert config.token == "custom"
        assert config.chat_id == "@custom"


class TestLoadConfigFromEnvironment:
    """Environment variables act as a fallback for CI/CD and Docker."""

    def test_uses_channel_id_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "env_token")
        monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@env_channel")

        config = load_config()

        assert config.token == "env_token"
        assert config.chat_id == "@env_channel"

    def test_uses_chat_id_env_alias(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_TOKEN", "env_token")
        monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "@alias_channel")

        assert load_config().chat_id == "@alias_channel"


class TestConfigErrors:
    """Missing or malformed configuration must fail with a clear message."""

    def test_missing_file_and_env_raises_config_file_not_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)

        with pytest.raises(ConfigFileNotFoundError) as exc_info:
            load_config()

        message = str(exc_info.value)
        assert "config.toml" in message
        assert "TELEGRAM_TOKEN" in message
        assert "TELEGRAM_CHANNEL_ID" in message

    def test_invalid_toml_raises_invalid_config(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_file = get_config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("token = = broken\n", encoding="utf-8")

        with pytest.raises(InvalidConfigError):
            load_config()

    def test_missing_field_raises_invalid_config(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_file = get_config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text('token = "only_token"\n', encoding="utf-8")

        with pytest.raises(InvalidConfigError) as exc_info:
            load_config()

        assert "TELEGRAM_CHANNEL_ID" in str(exc_info.value)


class TestWriteConfig:
    """Writing the configuration must create private files and directories."""

    def test_write_config_creates_private_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))

        path = write_config(TelegramConfig(token="abc", chat_id="@chan"))

        assert path == get_config_file()
        assert path.read_text(encoding="utf-8").count('token = "abc"') == 1
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600

    def test_ensure_config_dir_creates_private_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))

        config_dir = ensure_config_dir()

        assert config_dir.is_dir()
        assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700

    def test_round_trip(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)

        write_config(TelegramConfig(token="round", chat_id="@trip"))

        assert load_config() == TelegramConfig(token="round", chat_id="@trip")

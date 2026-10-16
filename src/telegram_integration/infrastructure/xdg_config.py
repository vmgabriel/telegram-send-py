"""XDG Base Directory configuration for the Telegram integration.

This module belongs to the *infrastructure* layer. It resolves the
platform-specific directories described by the `XDG Base Directory
specification <https://specifications.freedesktop.org/basedir-spec/latest/>`_
through :mod:`platformdirs` and loads the application configuration from a
TOML document.

Configuration values are resolved, in order of precedence, from:

1. Explicit values passed when instantiating :class:`TelegramConfig`.
2. The XDG configuration file, i.e.
   ``$XDG_CONFIG_HOME/telegram-send/config.toml`` which defaults to
   ``~/.config/telegram-send/config.toml``.
3. Environment variables (``TELEGRAM_TOKEN`` and ``TELEGRAM_CHANNEL_ID``),
   used as a fallback for CI/CD pipelines and containerised deployments.

When neither the configuration file nor the environment fallback provide
the required credentials, :func:`load_config` raises
:class:`ConfigFileNotFoundError` with actionable instructions.
"""

from __future__ import annotations

import json
import os
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Final

import platformdirs
from pydantic import AliasChoices, Field, ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

APP_NAME: Final[str] = "telegram-send"
"""Name of the application, used to build the XDG directory names."""

CONFIG_FILENAME: Final[str] = "config.toml"
"""Name of the configuration document stored inside the XDG config directory."""

ENV_TOKEN: Final[str] = "TELEGRAM_TOKEN"
"""Environment variable consulted as a fallback for the bot token."""

ENV_CHANNEL_ID: Final[str] = "TELEGRAM_CHANNEL_ID"
"""Environment variable consulted as a fallback for the chat identifier."""

ENV_CHAT_ID: Final[str] = "TELEGRAM_CHAT_ID"
"""Alias environment variable for the chat identifier."""

_active_config_file: ContextVar[Path | None] = ContextVar(
    "_active_config_file", default=None
)


class TelegramConfigError(Exception):
    """Base class for every configuration error raised by this module."""


class ConfigFileNotFoundError(TelegramConfigError):
    """Raised when no configuration file and no environment fallback exist.

    This error is deliberately separate from
    :class:`InvalidConfigError` so callers can distinguish between *"the
    user never configured the application"* and *"the configuration is
    present but wrong"*.
    """


class InvalidConfigError(TelegramConfigError):
    """Raised when the configuration exists but cannot be parsed or validated."""


def _platform_dirs() -> platformdirs.PlatformDirs:
    """Build a :class:`platformdirs.PlatformDirs` instance for the application.

    A new instance is created on every call so that changes to the
    ``XDG_CONFIG_HOME`` and ``XDG_DATA_HOME`` environment variables are
    honoured (which keeps the code easy to test).

    Returns:
        A platform directory resolver configured for this application.
    """
    return platformdirs.PlatformDirs(APP_NAME, appauthor=False)


def get_config_dir() -> Path:
    """Return the XDG configuration directory of the application.

    Returns:
        ``$XDG_CONFIG_HOME/telegram-send`` (by default
        ``~/.config/telegram-send``).
    """
    return _platform_dirs().user_config_path


def get_data_dir() -> Path:
    """Return the XDG data directory of the application.

    Returns:
        ``$XDG_DATA_HOME/telegram-send`` (by default
        ``~/.local/share/telegram-send``).
    """
    return _platform_dirs().user_data_path


def get_config_file() -> Path:
    """Return the absolute path of the TOML configuration document.

    Returns:
        ``get_config_dir() / "config.toml"``.
    """
    return get_config_dir() / CONFIG_FILENAME


def ensure_config_dir() -> Path:
    """Create the XDG configuration directory if it does not exist yet.

    The directory is created with ``0700`` permissions so that credentials
    stored inside it are only readable by the owning user.

    Returns:
        The configuration directory.
    """
    config_dir = get_config_dir()
    config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    return config_dir


@contextmanager
def _using_config_file(config_file: Path | None) -> Iterator[None]:
    """Temporarily install the configuration file read by the settings source.

    Args:
        config_file: The document to read, or ``None`` to use the default
            XDG location.

    Yields:
        ``None`` once the override is active.
    """
    token = _active_config_file.set(config_file)
    try:
        yield
    finally:
        _active_config_file.reset(token)


def _source_config_file() -> Path:
    """Return the configuration file used by the settings source.

    Returns:
        The explicitly requested file when set, otherwise the XDG path.
    """
    return _active_config_file.get() or get_config_file()


class TelegramConfig(BaseSettings):
    """Validated application configuration.

    The model reads its values from the XDG configuration file and falls
    back to environment variables, keeping compatibility with CI/CD and
    Docker setups. See the module docstring for the full precedence order.

    Attributes:
        token: Telegram Bot API token obtained from ``@BotFather``.
        chat_id: Channel or chat identifier used as the default recipient.
    """

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
        validate_default=True,
    )

    token: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices(ENV_TOKEN, "token"),
        description="Telegram Bot API token obtained from @BotFather.",
    )
    chat_id: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices(ENV_CHANNEL_ID, ENV_CHAT_ID, "chat_id"),
        description="Default channel or chat identifier where messages are sent.",
    )

    @field_validator("token", "chat_id", mode="after")
    @classmethod
    def _strip_and_validate(cls, value: str) -> str:
        """Reject blank credentials and trim surrounding whitespace.

        Args:
            value: The raw value provided by any settings source.

        Returns:
            The stripped value.

        Raises:
            ValueError: If the value is empty after stripping.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty")
        return stripped

    @property
    def channel_id(self) -> str:
        """Backwards-compatible alias for :attr:`chat_id`.

        Returns:
            The configured chat identifier.
        """
        return self.chat_id

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Declare the settings sources and their precedence.

        The TOML file is placed before the environment source so that the
        XDG configuration takes precedence and the environment acts only as
        a fallback (or as an override of individual missing values).

        Args:
            settings_cls: The settings class being instantiated.
            init_settings: Source holding explicit constructor arguments.
            env_settings: Source reading environment variables.
            dotenv_settings: Unused ``.env`` source, kept for the signature.
            file_secret_settings: Source reading Docker secret files.

        Returns:
            The ordered sources, from highest to lowest priority.
        """
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=_source_config_file()),
            env_settings,
            file_secret_settings,
        )


def _missing_config_message(config_file: Path) -> str:
    """Build the actionable message shown when no configuration is found.

    Args:
        config_file: The configuration file that was expected.

    Returns:
        A multi-line, user-facing explanation.
    """
    template = "\n".join(
        (
            f"    token = {json.dumps('123456:ABC-DEF...')}",
            f"    chat_id = {json.dumps('@my_channel')}",
        )
    )
    return (
        "Telegram credentials were not found.\n"
        f"Expected a configuration file at:\n    {config_file}\n\n"
        "Create the file (run your initialization command or create it "
        "manually) with the following content:\n\n"
        f"{template}\n\n"
        f"Alternatively, export the {ENV_TOKEN} and {ENV_CHANNEL_ID} "
        "environment variables, for example in CI/CD or Docker."
    )


def load_config(config_file: Path | str | None = None) -> TelegramConfig:
    """Load and validate the application configuration.

    Args:
        config_file: Optional explicit path to the TOML document. When
            omitted the XDG location returned by :func:`get_config_file` is
            used.

    Returns:
        A fully validated :class:`TelegramConfig` instance.

    Raises:
        ConfigFileNotFoundError: If the configuration file does not exist
            and the environment fallback is not complete.
        InvalidConfigError: If the file exists but cannot be parsed or does
            not provide valid credentials.
    """
    path = Path(config_file) if config_file is not None else get_config_file()
    has_env_fallback = bool(
        os.environ.get(ENV_TOKEN)
        and (os.environ.get(ENV_CHANNEL_ID) or os.environ.get(ENV_CHAT_ID))
    )

    if not path.is_file() and not has_env_fallback:
        raise ConfigFileNotFoundError(_missing_config_message(path))

    try:
        with _using_config_file(path):
            return TelegramConfig()
    except ValidationError as exc:
        missing = ", ".join(
            ".".join(str(part) for part in error.get("loc", ()))
            for error in exc.errors()
        )
        raise InvalidConfigError(
            f"Invalid Telegram configuration in {path}. "
            f"Please provide valid values for: {missing or 'token, chat_id'}."
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise InvalidConfigError(
            f"The configuration file {path} is not valid TOML: {exc}"
        ) from exc


def write_config(
    config: TelegramConfig,
    config_file: Path | str | None = None,
) -> Path:
    """Persist a configuration instance to the XDG configuration file.

    The parent directory is created if needed and the document is written
    with ``0600`` permissions so that the bot token is not world readable.

    Args:
        config: The configuration to persist.
        config_file: Optional explicit destination. Defaults to the XDG
            location returned by :func:`get_config_file`.

    Returns:
        The path of the written document.
    """
    path = Path(config_file) if config_file is not None else get_config_file()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    lines = [
        "# Telegram integration configuration (XDG Base Directory spec).",
        "# Generated by telegram-integration. Keep this file private (chmod 600).",
        f"token = {json.dumps(config.token)}",
        f"chat_id = {json.dumps(config.chat_id)}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    path.chmod(0o600)
    return path

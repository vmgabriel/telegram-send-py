"""Infrastructure layer.

This package groups the adapters that talk to the outside world (the file
system, the XDG base directories, persistence, ...). The application and
domain layers depend on abstractions; the concrete implementations live
here.
"""

from .xdg_config import (
    APP_NAME,
    CONFIG_FILENAME,
    ConfigFileNotFoundError,
    InvalidConfigError,
    TelegramConfig,
    TelegramConfigError,
    ensure_config_dir,
    get_config_dir,
    get_config_file,
    get_data_dir,
    load_config,
    write_config,
)

__all__ = [
    "APP_NAME",
    "CONFIG_FILENAME",
    "ConfigFileNotFoundError",
    "InvalidConfigError",
    "TelegramConfig",
    "TelegramConfigError",
    "ensure_config_dir",
    "get_config_dir",
    "get_config_file",
    "get_data_dir",
    "load_config",
    "write_config",
]

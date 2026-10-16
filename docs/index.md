# Telegram Integration

A Python-based integration for sending and receiving messages through the
Telegram Bot API.

## Features

- Send **Markdown**, **HTML**, or **plain text** messages to any Telegram
  channel or chat.
- Listen for incoming messages and trigger external scripts in response.
- Command-line interface powered by **Typer**, with shell completion.
- Configuration in TOML following the **XDG Base Directory** specification.
- **pipx**-friendly packaging, a **systemd** user unit and a **man page**.
- Environments and tasks managed by **Hatch**.
- Generated documentation built with **MkDocs**.

## Quick start

```console
$ pipx install telegram-send-py
$ mkdir -p ~/.config/telegram-send              # then add token and chat_id
$ telegram-send "**Hello** from Telegram"
```

Or from a checkout, through Hatch:

```console
$ hatch run send "**Hello** from Telegram"
```

See [Usage](usage.md) for the full configuration guide.

## Project layout

```
telegram-send-py/
├── src/telegram_integration/   # Python package
│   ├── client.py               # Telegram Bot API wrapper
│   ├── sender.py               # Legacy message sending helper
│   ├── receiver.py             # Legacy update polling helper
│   ├── cli.py                  # Backwards-compatible import shim
│   ├── application/            # Use cases (framework-independent)
│   ├── domain/                 # Entities, exceptions and ports (DDD)
│   ├── infrastructure/         # XDG config, SQLite state, script runner
│   └── presentation/           # Typer CLI (send/listen + completion)
├── scripts/                    # Runnable entry-point scripts
├── tests/                      # Unit tests
├── docs/                       # MkDocs documentation sources
├── extras/                     # systemd unit and man page
├── examples/                   # Sample responses
├── mkdocs.yml                  # Documentation configuration
├── pyproject.toml              # Project and Hatch configuration
├── Makefile                    # Common task shortcuts
└── README.md
```

Check the [API reference](api.md) for the full package documentation.
# Telegram Integration

A Python-based integration for sending and receiving messages through the
Telegram Bot API.

## Features

- Send **Markdown**, **HTML**, or **plain text** messages to any Telegram
  channel or chat.
- Listen for incoming messages and trigger external scripts in response.
- Command-line interface powered by **Typer**.
- Configuration in TOML following the **XDG Base Directory** specification.
- Environments and tasks managed by **Hatch**.
- Generated documentation built with **MkDocs**.

## Quick start

```console
$ pip install -r requirements.txt
$ mkdir -p ~/.config/telegram-send              # then add token and chat_id
$ python scripts/send_message.py "**Hello** from Telegram"
```

Or through Hatch:

```console
$ hatch run send "**Hello** from Telegram"
```

See [Usage](usage.md) for the full configuration guide.

## Project layout

```
telegram_integration/
├── src/telegram_integration/   # Python package
│   ├── client.py               # Telegram Bot API wrapper
│   ├── sender.py               # Message sending logic
│   ├── receiver.py             # Update polling and script triggering
│   ├── cli.py                  # Typer command-line applications
│   └── infrastructure/         # XDG paths and TOML configuration
├── scripts/                    # Runnable entry-point scripts
├── tests/                      # Unit tests
├── docs/                       # MkDocs documentation sources
├── examples/                   # Sample responses
├── mkdocs.yml                  # Documentation configuration
├── pyproject.toml              # Project and Hatch configuration
├── Makefile                    # Common task shortcuts
└── README.md
```

Check the [API reference](api.md) for the full package documentation.
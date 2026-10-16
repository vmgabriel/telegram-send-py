# telegram-send-py

A small, Linux-friendly Python CLI for sending and receiving messages through
the Telegram Bot API, with external script triggering and XDG-compliant
configuration.

## Features

- Send **Markdown**, **HTML**, or **plain text** messages to any Telegram channel or chat
- Listen for incoming messages and trigger external scripts in response
- Command-line interface powered by **Typer** (with `send`, `listen` and shell completion)
- **XDG Base Directory** configuration (`~/.config/telegram-send/config.toml`) and state
- **pipx**-friendly packaging, a **systemd** user unit and a **man page**
- Clean architecture: domain, application, infrastructure and presentation layers
- Environments and task automation managed by **Hatch**
- Generated documentation with **MkDocs**

## Project Structure

```
telegram-send-py/
├── src/
│   └── telegram_integration/
│       ├── __init__.py         # Package exports
│       ├── client.py           # Telegram API communication
│       ├── sender.py           # Legacy message sending helper
│       ├── receiver.py         # Legacy message receiving helper
│       ├── cli.py              # Backwards-compatible import shim
│       ├── py.typed            # PEP 561 typing marker
│       ├── application/        # Use cases orchestrating the ports
│       │   ├── send_message.py
│       │   └── listen_messages.py
│       ├── domain/             # Entities, exceptions and ports (DDD)
│       │   ├── entities.py     # ListenerState entity
│       │   ├── exceptions.py   # Domain exceptions
│       │   ├── ports.py        # TelegramGateway port
│       │   └── repositories.py # ListenerStateRepository port
│       ├── infrastructure/     # Adapters (I/O, config, persistence)
│       │   ├── xdg_config.py   # XDG paths and TOML configuration model
│       │   ├── sqlite_state.py # SQLite listener-state repository
│       │   └── scripts.py      # External script runner
│       └── presentation/       # Typer command-line interface
│           ├── cli.py          # send / listen apps
│           └── completions.py  # Hidden `completion` command
├── scripts/
│   ├── send_message.py         # Convenience script to send a message
│   └── listen_messages.py      # Convenience script to listen
├── tests/                      # Unit tests
├── docs/                       # MkDocs documentation sources
├── extras/                     # Linux integration artifacts
│   ├── telegram-send.service.example  # systemd user unit
│   └── telegram-send.1                # man page (roff)
├── examples/
│   └── telegram_updates.json   # Example of a Telegram API response
├── pyproject.toml              # Project metadata, Hatch envs and scripts
├── mkdocs.yml                  # Documentation configuration
├── Makefile                    # Task shortcuts
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Requirements

- Python 3.11+
- A Telegram Bot token (obtained from [@BotFather](https://t.me/BotFather))
- A channel or chat where the bot is a member

## Installation

### With pipx (recommended on Linux)

[pipx](https://pipx.pypa.io/) installs the CLI in its own isolated
environment and exposes the console scripts on your `PATH`:

```bash
pipx install telegram-send-py
```

This installs three commands:

| Command                 | Description                                        |
|-------------------------|----------------------------------------------------|
| `telegram-send`         | Send a single message                              |
| `telegram-listen`       | Listen for incoming messages                       |
| `telegram-integration`  | Unified app: `send`, `listen` and `completion`     |

To upgrade or remove:

```bash
pipx upgrade telegram-send-py
pipx uninstall telegram-send-py
```

### From source (contributors)

The project uses [Hatch](https://hatch.pypa.io/) to manage isolated
environments and tasks, so no manual setup is needed:

```bash
git clone https://github.com/vmgabriel/telegram-send-py.git
cd telegram-send-py

make install-dev       # editable install with dev + docs tooling
make test              # run the test suite
```

A plain virtual environment also works:

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,docs]"
```

## Configuration

Credentials live in a TOML file that follows the XDG Base Directory
specification:

```
$XDG_CONFIG_HOME/telegram-send/config.toml   # defaults to ~/.config/telegram-send/config.toml
```

Create it with your token and chat id:

```bash
mkdir -p ~/.config/telegram-send
cat > ~/.config/telegram-send/config.toml <<'EOF'
token = "your_bot_token_here"
chat_id = "@your_channel_or_chat_id"
EOF
chmod 600 ~/.config/telegram-send/config.toml
```

Or generate it from Python:

```python
from telegram_integration.infrastructure import TelegramConfig, write_config

write_config(TelegramConfig(token="your_bot_token_here", chat_id="@your_channel"))
```

The channel id can be the username of a public channel (e.g. `@mychannel`) or
the numeric chat id for private groups.

### Environment fallback (CI / Docker)

For CI/CD and Docker you can instead export `TELEGRAM_TOKEN` and
`TELEGRAM_CHANNEL_ID`. They are used as a fallback when the file does not
exist (and fill in any missing value). Explicit `--token` / `--channel-id`
flags always win. If no credentials are found anywhere, a clear
`ConfigFileNotFoundError` explains how to fix it.

The listener persists its last processed offset in the XDG data directory:

```
~/.local/share/telegram-send/state.db
```

## Usage

### Sending messages

```bash
telegram-send "**Hello** from *Telegram*"          # Markdown (default)
telegram-send "Hello World" --mode plain           # Plain text
telegram-send "<b>Hello</b> World" --mode html     # HTML
```

### Listening for messages

```bash
telegram-listen
telegram-listen --timeout 60 --interval 2
```

Trigger external scripts whenever a message arrives:

```bash
telegram-listen --scripts ./my_handler.py --scripts ./another.py
```

Each triggered script receives the full Telegram update as JSON through the
`TELEGRAM_MESSAGE` environment variable.

### Unified app

The same actions are available as subcommands of a single command:

```bash
telegram-integration send "**Hello**"
telegram-integration listen --timeout 30
```

### From a checkout

The repository scripts and the Makefile shortcuts are handy during
development:

```bash
python scripts/send_message.py "**Hello** from *Telegram*"
hatch run send "**Hello** from *Telegram*"
make run-send MSG="**Hello** from *Telegram*"
```

## Shell completion

Every Typer app supports completion through its built-in flags:

```bash
telegram-integration --install-completion
```

The unified app also exposes a hidden `completion` command that prints the
script for `bash`, `zsh` or `fish`, which is convenient for packaging. The
`make completion` target writes all three scripts into `completions/`:

```bash
make completion
# completions/telegram-integration.bash
# completions/_telegram-integration        (zsh)
# completions/telegram-integration.fish
```

Or generate them by hand and install them system-wide:

```bash
telegram-integration completion bash > /etc/bash_completion.d/telegram-integration
telegram-integration completion zsh  > ~/.zsh/completions/_telegram-integration
telegram-integration completion fish > ~/.config/fish/completions/telegram-integration.fish

# A script for a different command name, e.g. telegram-send:
telegram-integration completion bash --program telegram-send
```

## Running as a systemd user service

`extras/telegram-send.service.example` is a ready-to-edit **user** unit that
runs `telegram-listen` in the background. It reads the credentials from
`~/.config/telegram-send/config.toml` and stores its state under
`~/.local/share/telegram-send/`.

```bash
mkdir -p ~/.config/systemd/user
cp extras/telegram-send.service.example ~/.config/systemd/user/telegram-send.service

# Edit ExecStart if telegram-listen is not at ~/.local/bin/telegram-listen:
$EDITOR ~/.config/systemd/user/telegram-send.service

systemctl --user daemon-reload
systemctl --user enable --now telegram-send.service
systemctl --user status telegram-send.service
journalctl --user -u telegram-send.service -f
```

To keep the service running after you log out, enable lingering once:

```bash
loginctl enable-linger "$USER"
```

The CLI shuts down cleanly on `Ctrl+C`, and the unit maps `systemctl stop` to
`SIGINT` (`KillSignal=SIGINT`) accordingly.

## Manual page

A basic roff man page is provided at `extras/telegram-send.1`. Install it for
all users:

```bash
sudo cp extras/telegram-send.1 /usr/local/share/man/man1/telegram-send.1
sudo mandb          # optional, refresh the man database
man telegram-send
```

Or preview it without installing:

```bash
man ./extras/telegram-send.1
```

## Using as a Python library

```python
from telegram_integration import MessageSender, MessageReceiver

# Send a message
sender = MessageSender()
sender.send_markdown("*Hello* from Python!")

# Receive messages
receiver = MessageReceiver()
receiver.register_callback(lambda update: print(update))
receiver.listen()
```

## Tests

```bash
hatch run test              # basic tests
hatch run test:test         # tests with coverage report
make test                   # via Makefile
make test-cov               # via Makefile (with coverage)
python -m pytest tests/ -v  # direct invocation
```

## Documentation

Generated documentation is built with MkDocs and served locally:

```bash
hatch run docs:build        # build site/ directory
hatch run docs:serve        # serve at http://localhost:8000
make docs-build             # via Makefile
make docs-serve             # via Makefile
```

## Makefile targets

All targets run through Hatch, so they always use the environment declared in
`pyproject.toml`.

| Target                                | Description                                    |
|---------------------------------------|------------------------------------------------|
| `make install`                        | Create the runtime Hatch environment           |
| `make install-dev`                    | Install editable with dev + docs extras        |
| `make test`                           | Run unit tests via Hatch                       |
| `make test-cov`                       | Run tests with coverage                        |
| `make test-filter K=-k send`          | Run a subset of tests                          |
| `make lint`                           | Run Ruff and mypy                              |
| `make format`                         | Auto-format with Ruff                          |
| `make build`                          | Build the sdist and wheel into `dist/`         |
| `make completion`                     | Generate bash/zsh/fish scripts into `completions/` |
| `make run-send MSG="hi" MODE=html`    | Send a message                                 |
| `make run-listen SCRIPTS="a.py"`      | Listen and trigger scripts                     |
| `make docs-build` / `make docs-serve` | Build / serve documentation                    |
| `make clean`                          | Remove artifacts, caches and generated files   |

## License

MIT

# Usage

## Requirements

- Python 3.11+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A channel or chat where the bot is a member

## Installation

### With pipx (recommended on Linux)

```console
$ pipx install telegram-send-py
```

This exposes the `telegram-send`, `telegram-listen` and `telegram-integration`
commands on your `PATH`.

### With Hatch (contributors)

Hatch manages isolated environments, so the project and all its dependencies
are installed automatically:

```console
$ hatch run test          # creates the environment on first run
$ make install-dev        # editable install with dev + docs tooling
```

### With a virtual environment

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev,docs]"
```

## Configuration

Credentials are read from the configuration file defined by the
[XDG Base Directory](https://specifications.freedesktop.org/basedir-spec/latest/)
specification:

```
$XDG_CONFIG_HOME/telegram-send/config.toml   # defaults to ~/.config/telegram-send/config.toml
```

The file uses the TOML format:

```toml
token = "your_bot_token_here"
chat_id = "@your_channel_or_chat_id"
```

You can create it by hand or generate it from Python:

```python
from telegram_integration.infrastructure import TelegramConfig, write_config

write_config(TelegramConfig(token="your_bot_token_here", chat_id="@your_channel"))
```

The file is created with `0600` permissions so that the token stays private.

For CI/CD and Docker, export the `TELEGRAM_TOKEN` and `TELEGRAM_CHANNEL_ID`
environment variables instead. They act as a fallback when the file is missing
and complete any value the file does not define. When no credentials are found,
a `ConfigFileNotFoundError` is raised with instructions to create the file.

The channel id can be a public channel username (e.g. `@mychannel`) or the
numeric chat id for private groups.

## Sending messages

### Markdown

```console
$ python scripts/send_message.py "**Hello** from *Telegram*"
$ hatch run send "**Hello** from *Telegram*"        # equivalent via Hatch
```

### Plain text or HTML

```console
$ python scripts/send_message.py "Hello World" --mode plain
$ python scripts/send_message.py "<b>Hello</b> World" --mode html
```

### Using the console entry point

With `pipx install telegram-send-py` (or `pip install -e .`) the same commands
are available globally:

```console
$ telegram-send "**Hello**" -m markdown
$ telegram-listen --timeout 30 --interval 1
$ telegram-integration send "**Hello**"           # unified app
```

## Listening for messages

Start the long-polling listener:

```console
$ python scripts/listen_messages.py
$ hatch run listen                # equivalent via Hatch
```

Trigger external scripts whenever a message arrives:

```console
$ python scripts/listen_messages.py --scripts ./my_handler.py --scripts ./other.py
```

Each triggered script receives the full Telegram update through the
`TELEGRAM_MESSAGE` environment variable.

### Polling options

| Option       | Default | Description                         |
|--------------|---------|-------------------------------------|
| `--timeout`  | `30`    | Long-polling timeout in seconds     |
| `--interval` | `1.0`   | Delay between polls in seconds      |
| `--scripts`  | —       | External scripts to run per message |

## Using as a Python library

```python
from telegram_integration import MessageSender, MessageReceiver

sender = MessageSender()
sender.send_markdown("*Hello* from Python!")

receiver = MessageReceiver()
receiver.register_callback(lambda update: print(update))
receiver.listen()
```

## Running from the Makefile

| Target                    | Description                                   |
|---------------------------|-----------------------------------------------|
| `make install`            | Create the runtime Hatch environment          |
| `make install-dev`        | Install editable with dev + docs extras       |
| `make test`               | Run unit tests via Hatch                      |
| `make test-cov`           | Run tests with a coverage report              |
| `make test-filter K=-k foo` | Run a subset of tests                     |
| `make lint`               | Run Ruff and mypy                             |
| `make format`             | Auto-format with Ruff                         |
| `make build`              | Build the sdist and wheel                     |
| `make completion`         | Generate bash/zsh/fish scripts into `completions/` |
| `make run-send MSG="hi"`  | Send a message                                |
| `make run-send MSG="hi" MODE=html` | Send as HTML                      |
| `make run-listen SCRIPTS="a.py"` | Listen and trigger scripts          |
| `make docs-build`         | Build the docs site                           |
| `make docs-serve`         | Serve docs at http://localhost:8000           |
| `make clean`              | Remove artifacts, caches and generated files  |

## Shell completion

```console
$ telegram-integration --install-completion
$ make completion        # writes bash/zsh/fish scripts into completions/
```

## Running as a systemd user service

A ready-to-edit user unit lives at `extras/telegram-send.service.example`. See
the "Running as a systemd user service" section of the README for install
steps. The CLI shuts down cleanly on `Ctrl+C`, and the unit maps
`systemctl stop` to `SIGINT`.

## Running tests

```console
$ hatch run test              # basic tests
$ hatch run test:test         # tests with coverage
$ python -m pytest tests/ -v  # direct invocation
```
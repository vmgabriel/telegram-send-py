# Telegram Integration

A Python-based integration for sending and receiving messages through the Telegram Bot API.

## Features

- Send **Markdown**, **HTML**, or **plain text** messages to any Telegram channel or chat
- Listen for incoming messages and trigger external scripts in response
- Command-line interface powered by **Typer**
- Environments and task automation managed by **Hatch**
- Generated documentation with **MkDocs**
- Convenient shortcuts through a **Makefile**

## Project Structure

```
telegram_integration/
├── src/
│   └── telegram_integration/
│       ├── __init__.py       # Package exports
│       ├── client.py         # Telegram API communication
│       ├── sender.py         # Message sending logic
│       ├── receiver.py       # Message receiving and script triggering
│       └── cli.py            # Typer command-line applications
├── scripts/
│   ├── send_message.py       # CLI to send markdown messages
│   └── listen_messages.py    # CLI to listen for messages
├── tests/
│   ├── conftest.py           # Shared test fixtures
│   ├── test_basic.py         # Unit tests for the package
│   └── test_cli.py           # Unit tests for the CLI
├── docs/                     # MkDocs documentation sources
├── examples/
│   └── telegram_updates.json # Example of a Telegram API response
├── pyproject.toml            # Project metadata, Hatch envs and scripts
├── mkdocs.yml                # Documentation configuration
├── Makefile                  # Task shortcuts
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Requirements

- Python 3.8+
- A Telegram Bot token (obtained from [@BotFather](https://t.me/BotFather))
- A channel or chat where the bot is a member

## Installation

### With Hatch (recommended)

Hatch manages isolated environments for you, so no manual setup is needed:

```bash
hatch run test        # creates the environment automatically on first run
```

### With a virtual environment

```bash
cd telegram_integration
python -m venv venv
source venv/bin/activate      # Linux / macOS
# venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Configure your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel_or_chat_id
```

The channel ID can be the username of a public channel (e.g. `@mychannel`) or the numeric chat ID for private groups.

## Usage

### Sending messages (Typer CLI)

Markdown:

```bash
python scripts/send_message.py "**Hello** from *Telegram*"
hatch run send "**Hello** from *Telegram*"          # via Hatch
make run-send MSG="**Hello** from *Telegram*"       # via Makefile
```

Plain text or HTML:

```bash
python scripts/send_message.py "Hello World" --mode plain
python scripts/send_message.py "<b>Hello</b> World" --mode html
```

Installed console entry points (`pip install -e .`):

```bash
telegram-send "**Hello**" -m markdown
telegram-listen --timeout 30 --interval 1
```

### Listening for messages

```bash
python scripts/listen_messages.py
hatch run listen                                 # via Hatch
make run-listen                                  # via Makefile
```

Trigger external scripts when messages arrive:

```bash
python scripts/listen_messages.py --scripts ./my_handler.py --scripts ./another.py
make run-listen SCRIPTS="my_handler.py another.py"
```

Each triggered script receives the full Telegram update via the `TELEGRAM_MESSAGE` environment variable.

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

| Target                                | Description                            |
|---------------------------------------|----------------------------------------|
| `make install`                        | Create venv and install dependencies   |
| `make install-dev`                    | Install package editable mode          |
| `make test`                           | Run unit tests via Hatch               |
| `make test-cov`                       | Run tests with coverage                |
| `make test-filter K=-k send`          | Run a subset of tests                  |
| `make run-send MSG="hi" MODE=html`    | Send a message                         |
| `make run-listen SCRIPTS="a.py"`      | Listen and trigger scripts             |
| `make docs-build` / `make docs-serve` | Build / serve documentation            |
| `make build`                          | Build a distributable package          |
| `make clean`                          | Remove artifacts and caches            |

## License

MIT
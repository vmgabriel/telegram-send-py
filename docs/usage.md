# Usage

## Requirements

- Python 3.8+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A channel or chat where the bot is a member

## Installation

### With Hatch (recommended)

Hatch manages isolated environments, so the project and all its dependencies
are installed automatically:

```console
$ hatch run test          # creates the environment on first run
```

### With a virtual environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then configure the environment variables:

```
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel_or_chat_id
```

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

After `pip install -e .`, the same commands are available globally:

```console
$ telegram-send "**Hello**" -m markdown
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
| `make install`            | Create venv and install dependencies          |
| `make install-dev`        | Install package editable with console scripts|
| `make test`               | Run unit tests via Hatch                      |
| `make test-cov`           | Run tests with a coverage report              |
| `make test-filter K=-k foo` | Run a subset of tests                     |
| `make run-send MSG="hi"`  | Send a message                                |
| `make run-send MSG="hi" MODE=html` | Send as HTML                      |
| `make run-listen SCRIPTS="a.py"` | Listen and trigger scripts          |
| `make docs-build`         | Build the docs site                           |
| `make docs-serve`         | Serve docs at http://localhost:8000           |
| `make build`              | Build a distributable package                 |
| `make clean`              | Remove artifacts and caches                   |

## Running tests

```console
$ hatch run test              # basic tests
$ hatch run test:test         # tests with coverage
$ python -m pytest tests/ -v  # direct invocation
```
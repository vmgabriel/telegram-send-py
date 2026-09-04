# Command Line Interface

Both commands are implemented with **Typer** and can be invoked through the
repository scripts, the console entry points, or Hatch.

## `send_message.py` / `telegram-send`

Send a message to a Telegram channel.

```console
$ python scripts/send_message.py [OPTIONS] MESSAGE

# or after installation:
$ telegram-send [OPTIONS] MESSAGE
```

| Option          | Short | Type   | Default     | Description                          |
|-----------------|-------|--------|-------------|--------------------------------------|
| `--mode`        | `-m`  | `str`  | `markdown`  | Parse mode: `markdown`, `html`, `plain` |
| `--token`       |       | `str`  | env var     | Telegram bot token overrides `TELEGRAM_TOKEN` |
| `--channel-id`  |       | `str`  | env var     | Chat id overrides `TELEGRAM_CHANNEL_ID` |
| `--help`        |       |        |             | Show this message and exit           |

### Examples

```console
$ telegram-send "**Bold** *italic*"
$ telegram-send "<b>Bold</b>" -m html
$ telegram-send "just text" -m plain
$ telegram-send "hello" --token 123:abc --channel-id -1001234567890
```

## `listen_messages.py` / `telegram-listen`

Listen for incoming messages continuously.

```console
$ python scripts/listen_messages.py [OPTIONS]

# or after installation:
$ telegram-listen [OPTIONS]
```

| Option          | Short | Type         | Default  | Description                          |
|-----------------|-------|--------------|----------|--------------------------------------|
| `--timeout`     |       | `int`        | `30`     | Long-polling timeout in seconds      |
| `--interval`    |       | `float`      | `1.0`    | Delay between polls in seconds       |
| `--scripts`     | `-s`  | list of `str`| —        | External scripts to trigger          |
| `--token`       |       | `str`        | env var  | Override `TELEGRAM_TOKEN`            |
| `--channel-id`  |       | `str`        | env var  | Override `TELEGRAM_CHANNEL_ID`       |
| `--help`        |       |              |          | Show this message and exit           |

### Examples

```console
$ telegram-listen
$ telegram-listen --timeout 60 --interval 2
$ telegram-listen --scripts worker.py --scripts reporter.py
```

## Hatch shortcuts

The same commands are available through Hatch in the default environment:

```console
$ hatch run send "**Hello**"
$ hatch run listen --timeout 30 --interval 1
$ hatch run test
```

## Shell completion

Typer-based commands support shell completion. Try:

```console
$ telegram-send --install-completion
$ telegram-listen --install-completion
```
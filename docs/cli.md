# Command Line Interface

The CLI is implemented with **Typer** and exposed through three console
entry points:

| Entry point             | Description                                              |
|-------------------------|----------------------------------------------------------|
| `telegram-send`         | Send a single message.                                   |
| `telegram-listen`       | Listen for incoming messages.                            |
| `telegram-integration`  | Unified app with `send`, `listen` and `completion`.      |

The commands can also be invoked through the repository scripts or Hatch.

## Unified app: `telegram-integration`

```console
$ telegram-integration send "**Bold** *italic*"
$ telegram-integration listen --timeout 60 --interval 2
$ telegram-integration --help
```

The `send` and `listen` subcommands accept exactly the same options as the
standalone `telegram-send` / `telegram-listen` entry points below.

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

Every Typer app supports completion through the built-in flags:

```console
$ telegram-send --install-completion
$ telegram-listen --install-completion
$ telegram-integration --install-completion
```

The unified app also exposes a hidden `completion` command that prints the
completion script for `bash`, `zsh` or `fish`, which is convenient for
packaging and for writing it to a directory:

```console
$ telegram-integration completion bash > /etc/bash_completion.d/telegram-integration
$ telegram-integration completion zsh  > ~/.zsh/completions/_telegram-integration
$ telegram-integration completion fish > ~/.config/fish/completions/telegram-integration.fish

# Generate the script for a different program name:
$ telegram-integration completion bash --program telegram-send
```
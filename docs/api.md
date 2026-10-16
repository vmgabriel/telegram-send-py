# API Reference

::: telegram_integration.client.TelegramClient
    options:
        show_if_no_docstring: true

::: telegram_integration.sender.MessageSender
    options:
        show_if_no_docstring: true

::: telegram_integration.receiver.MessageReceiver
    options:
        show_if_no_docstring: true

::: telegram_integration.presentation.cli.send

::: telegram_integration.presentation.cli.listen

::: telegram_integration.presentation.completions.completion

## Application

::: telegram_integration.application.send_message.SendMessageUseCase

::: telegram_integration.application.send_message.SendMessageResult

::: telegram_integration.application.listen_messages.ListenMessagesUseCase

## Domain

::: telegram_integration.domain.entities.ListenerState

::: telegram_integration.domain.repositories.ListenerStateRepository

::: telegram_integration.domain.ports.TelegramGateway

## Infrastructure

::: telegram_integration.infrastructure.xdg_config.TelegramConfig
    options:
        show_if_no_docstring: true

::: telegram_integration.infrastructure.xdg_config.load_config

::: telegram_integration.infrastructure.xdg_config.write_config

::: telegram_integration.infrastructure.xdg_config.get_config_file

::: telegram_integration.infrastructure.xdg_config.get_data_dir

::: telegram_integration.infrastructure.sqlite_state.SqliteStateRepository
    options:
        show_if_no_docstring: true

::: telegram_integration.infrastructure.sqlite_state.SqliteStateError

::: telegram_integration.infrastructure.scripts.ScriptRunner
    options:
        show_if_no_docstring: true
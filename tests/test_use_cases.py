"""Tests for the application use cases.

The use cases are exercised with fully mocked ports, which proves they are
independent from Typer, the terminal, ``requests`` and ``sqlite3``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, call

import pytest

from telegram_integration.application import listen_messages, send_message
from telegram_integration.application.listen_messages import ListenMessagesUseCase
from telegram_integration.application.send_message import SendMessageUseCase
from telegram_integration.client import TelegramClient
from telegram_integration.domain import (
    InvalidMessageError,
    InvalidMessageModeError,
    MessageSendError,
    PollingError,
    TelegramGateway,
)
from telegram_integration.infrastructure import TelegramConfig


def make_config() -> TelegramConfig:
    """Build a configuration without touching the file system."""
    return TelegramConfig(token="test-token", chat_id="@test-channel")


class TestSendMessageUseCase:
    """The send use case maps modes and delegates to the injected gateway."""

    def _use_case(self, response: dict) -> tuple[SendMessageUseCase, Mock]:
        gateway = Mock()
        gateway.send_message.return_value = response
        return SendMessageUseCase(gateway, make_config()), gateway

    def test_sends_markdown_to_the_configured_chat(self) -> None:
        use_case, gateway = self._use_case({"ok": True, "result": {"message_id": 10}})

        result = use_case.execute("*hello*", "markdown")

        gateway.send_message.assert_called_once_with(
            text="*hello*", parse_mode="Markdown", chat_id="@test-channel"
        )
        assert result.message_id == 10
        assert result.chat_id == "@test-channel"
        assert result.mode == "markdown"

    def test_html_mode(self) -> None:
        use_case, gateway = self._use_case({"ok": True, "result": {}})

        result = use_case.execute("<b>hi</b>", "html")

        assert gateway.send_message.call_args.kwargs["parse_mode"] == "HTML"
        assert result.mode == "html"

    def test_plain_mode_uses_no_parse_mode(self) -> None:
        use_case, gateway = self._use_case({"ok": True, "result": {}})

        use_case.execute("hello", "plain")

        assert gateway.send_message.call_args.kwargs["parse_mode"] is None

    def test_mode_is_case_insensitive_and_trimmed(self) -> None:
        use_case, gateway = self._use_case({"ok": True, "result": {}})

        result = use_case.execute("hello", "  MARKDOWN  ")

        assert result.mode == "markdown"
        assert gateway.send_message.call_args.kwargs["parse_mode"] == "Markdown"

    def test_missing_result_yields_no_message_id(self) -> None:
        use_case, _ = self._use_case({"ok": True})

        assert use_case.execute("hello", "plain").message_id is None

    def test_invalid_mode_raises_domain_error(self) -> None:
        use_case, gateway = self._use_case({"ok": True, "result": {}})

        with pytest.raises(InvalidMessageModeError, match="Unsupported mode"):
            use_case.execute("hello", "telepathy")

        gateway.send_message.assert_not_called()

    def test_empty_text_raises_domain_error(self) -> None:
        use_case, gateway = self._use_case({"ok": True, "result": {}})

        with pytest.raises(InvalidMessageError):
            use_case.execute("   ", "markdown")

        gateway.send_message.assert_not_called()

    def test_api_error_raises_message_send_error(self) -> None:
        use_case, _ = self._use_case(
            {"ok": False, "description": "Bad Request: chat not found"}
        )

        with pytest.raises(MessageSendError, match="chat not found"):
            use_case.execute("hello", "markdown")


class TestListenMessagesUseCase:
    """The listen use case polls and persists the offset through its ports."""

    def _use_case(
        self,
        updates: list[dict],
        *,
        stored_offset: int | None = None,
        ok: bool = True,
    ) -> tuple[ListenMessagesUseCase, Mock, Mock]:
        gateway = Mock()
        gateway.get_updates.return_value = {"ok": ok, "result": updates}
        repository = Mock()
        repository.get_offset.return_value = stored_offset
        use_case = ListenMessagesUseCase(
            gateway, make_config(), repository, poll_interval=0.0
        )
        return use_case, gateway, repository

    def test_poll_once_forwards_the_stored_offset(self) -> None:
        use_case, gateway, _ = self._use_case([], stored_offset=42)

        use_case.poll_once()

        gateway.get_updates.assert_called_once_with(offset=42, timeout=30)

    def test_poll_once_returns_empty_list_when_no_updates(self) -> None:
        use_case, _, repository = self._use_case([])

        assert use_case.poll_once() == []
        repository.save_offset.assert_not_called()

    def test_poll_once_persists_offset_and_invokes_callback(self) -> None:
        updates = [{"update_id": 7}, {"update_id": 8}]
        use_case, _, repository = self._use_case(updates)
        seen: list[dict] = []

        result = use_case.poll_once(seen.append)

        assert result == updates
        assert seen == updates
        assert repository.save_offset.call_args_list == [call(8), call(9)]

    def test_poll_once_can_override_the_timeout(self) -> None:
        use_case, gateway, _ = self._use_case([])

        use_case.poll_once(timeout=5)

        assert gateway.get_updates.call_args.kwargs["timeout"] == 5

    def test_malformed_update_raises_polling_error(self) -> None:
        use_case, _, repository = self._use_case([{"text": "no update id"}])

        with pytest.raises(PollingError, match="update_id"):
            use_case.poll_once()

        repository.save_offset.assert_not_called()

    def test_api_error_raises_polling_error(self) -> None:
        use_case, _, _ = self._use_case([], ok=False)

        with pytest.raises(PollingError):
            use_case.poll_once()

    def test_execute_runs_a_bounded_number_of_cycles(self) -> None:
        updates = [{"update_id": 5}]
        use_case, gateway, repository = self._use_case(updates)
        repository.get_offset.return_value = 6

        offset = use_case.execute(max_iterations=2)

        assert gateway.get_updates.call_count == 2
        assert offset == 6

    def test_stop_breaks_the_polling_loop(self) -> None:
        use_case, gateway, _ = self._use_case([{"update_id": 1}])

        use_case.execute(lambda update: use_case.stop())

        assert gateway.get_updates.call_count == 1

    def test_offset_property_reads_the_repository(self) -> None:
        use_case, _, repository = self._use_case([], stored_offset=99)

        assert use_case.offset == 99
        repository.get_offset.assert_called()


class TestArchitecturalBoundaries:
    """The use cases stay free of framework and terminal concerns."""

    def test_telegram_client_satisfies_the_gateway_port(self) -> None:
        client = TelegramClient(token="token", channel_id="@channel")

        assert isinstance(client, TelegramGateway)

    @pytest.mark.parametrize("module", [send_message, listen_messages])
    def test_use_case_sources_avoid_typer_and_print(self, module) -> None:
        source = Path(module.__file__).read_text(encoding="utf-8")

        assert "import typer" not in source
        assert "print(" not in source

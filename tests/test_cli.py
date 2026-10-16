"""Tests for the Typer presentation layer."""

from __future__ import annotations

import tomllib
from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from telegram_integration.presentation.cli import app, listen_app, send_app

runner = CliRunner()


class TestSendCommand:
    """`telegram-send` wires infrastructure into SendMessageUseCase."""

    @patch("telegram_integration.client.requests.post")
    def test_send_markdown_default(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 9}}
        mock_post.return_value = mock_response

        result = runner.invoke(send_app, ["*Bold* message"])

        assert result.exit_code == 0
        assert "Message sent successfully" in result.output
        body = mock_post.call_args.kwargs["json"]
        assert body["parse_mode"] == "Markdown"
        assert body["text"] == "*Bold* message"
        assert body["chat_id"] == "test_channel_id"

    @patch("telegram_integration.client.requests.post")
    def test_send_plain_mode(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {}}
        mock_post.return_value = mock_response

        result = runner.invoke(send_app, ["hello", "-m", "plain"])

        assert result.exit_code == 0
        assert mock_post.call_args.kwargs["json"]["parse_mode"] is None

    @patch("telegram_integration.client.requests.post")
    def test_send_html_mode(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {}}
        mock_post.return_value = mock_response

        result = runner.invoke(send_app, ["<b>hi</b>", "-m", "html"])

        assert result.exit_code == 0
        assert mock_post.call_args.kwargs["json"]["parse_mode"] == "HTML"

    @patch("telegram_integration.client.requests.post")
    def test_send_invalid_mode_fails(self, mock_post: Mock) -> None:
        result = runner.invoke(send_app, ["hello", "-m", "telepathy"])

        assert result.exit_code == 1
        assert "Unsupported mode" in result.output
        mock_post.assert_not_called()

    @patch("telegram_integration.client.requests.post")
    def test_send_api_error_fails(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {
            "ok": False,
            "description": "Bad Request: chat not found",
        }
        mock_post.return_value = mock_response

        result = runner.invoke(send_app, ["hello"])

        assert result.exit_code == 1
        assert "chat not found" in result.output

    def test_send_without_credentials_reports_config_error(self, monkeypatch) -> None:
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)

        result = runner.invoke(send_app, ["hello"])

        assert result.exit_code == 1
        assert "credentials" in result.output.lower()

    def test_send_requires_message(self) -> None:
        result = runner.invoke(send_app, [])

        assert result.exit_code != 0
        assert "missing argument 'message'" in result.output.lower()


class TestListenCommand:
    """`telegram-listen` wires infrastructure into ListenMessagesUseCase."""

    @patch("telegram_integration.presentation.cli.ListenMessagesUseCase")
    def test_listen_builds_use_case_with_options(self, mock_use_case_cls: Mock) -> None:
        mock_use_case_cls.return_value = Mock()

        result = runner.invoke(listen_app, ["--timeout", "10", "--interval", "2.0"])

        assert result.exit_code == 0
        mock_use_case_cls.assert_called_once()
        kwargs = mock_use_case_cls.call_args.kwargs
        assert kwargs["timeout"] == 10
        assert kwargs["poll_interval"] == 2.0
        mock_use_case_cls.return_value.execute.assert_called_once()

    @patch("telegram_integration.presentation.cli.ListenMessagesUseCase")
    def test_listen_handles_keyboard_interrupt(self, mock_use_case_cls: Mock) -> None:
        use_case = Mock()
        use_case.execute.side_effect = KeyboardInterrupt
        mock_use_case_cls.return_value = use_case

        result = runner.invoke(listen_app, [])

        assert result.exit_code == 0
        assert "Stopped listening" in result.output

    @patch("telegram_integration.presentation.cli.ListenMessagesUseCase")
    def test_listen_echoes_received_updates(self, mock_use_case_cls: Mock) -> None:
        use_case = Mock()
        use_case.execute.side_effect = lambda callback: callback({"update_id": 3})
        mock_use_case_cls.return_value = use_case

        result = runner.invoke(listen_app, [])

        assert "Update received" in result.output

    @patch("telegram_integration.presentation.cli.ScriptRunner")
    @patch("telegram_integration.presentation.cli.ListenMessagesUseCase")
    def test_listen_triggers_scripts(
        self, mock_use_case_cls: Mock, mock_runner_cls: Mock
    ) -> None:
        runner_mock = Mock()
        mock_runner_cls.return_value = runner_mock
        use_case = Mock()
        use_case.execute.side_effect = lambda callback: callback({"update_id": 1})
        mock_use_case_cls.return_value = use_case

        result = runner.invoke(listen_app, ["--scripts", "worker.py"])

        assert result.exit_code == 0
        mock_runner_cls.assert_called_once_with(["worker.py"])
        runner_mock.run.assert_called_once_with({"update_id": 1})


class TestUnifiedApp:
    """`telegram-integration` exposes send and listen as subcommands."""

    def test_help_lists_the_main_commands(self) -> None:
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "send" in result.output
        assert "listen" in result.output

    def test_completion_command_is_hidden(self) -> None:
        completion_command = next(
            command
            for command in app.registered_commands
            if command.name == "completion"
        )

        assert completion_command.hidden is True

    @patch("telegram_integration.client.requests.post")
    def test_send_subcommand(self, mock_post: Mock) -> None:
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
        mock_post.return_value = mock_response

        result = runner.invoke(app, ["send", "hello"])

        assert result.exit_code == 0
        assert "Message sent successfully" in result.output


class TestCompletionCommand:
    """The hidden `completion` command generates shell scripts via Typer."""

    def test_bash_completion(self) -> None:
        result = runner.invoke(
            app, ["completion", "bash", "--program", "telegram-integration"]
        )

        assert result.exit_code == 0
        assert "_telegram_integration_completion" in result.output
        assert "complete -o default" in result.output

    def test_zsh_completion(self) -> None:
        result = runner.invoke(app, ["completion", "zsh", "--program", "telegram-send"])

        assert result.exit_code == 0
        assert "#compdef telegram-send" in result.output

    def test_fish_completion(self) -> None:
        result = runner.invoke(
            app, ["completion", "fish", "--program", "telegram-integration"]
        )

        assert result.exit_code == 0
        assert "complete --command telegram-integration" in result.output

    def test_default_program_name_is_used(self) -> None:
        result = runner.invoke(app, ["completion", "bash"])

        assert result.exit_code == 0
        assert result.output.strip()

    def test_unsupported_shell_fails(self) -> None:
        result = runner.invoke(app, ["completion", "powershell"])

        assert result.exit_code != 0
        assert "Unsupported shell" in result.output


class TestEntryPoints:
    """The console scripts are registered in pyproject.toml."""

    def test_entry_points_registered(self) -> None:
        root = Path(__file__).resolve().parent.parent
        data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        scripts = data["project"]["scripts"]

        assert (
            scripts["telegram-send"] == "telegram_integration.presentation.cli:send_app"
        )
        assert (
            scripts["telegram-listen"]
            == "telegram_integration.presentation.cli:listen_app"
        )
        assert (
            scripts["telegram-integration"]
            == "telegram_integration.presentation.cli:app"
        )

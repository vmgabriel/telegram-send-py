from unittest.mock import Mock, patch

from typer.testing import CliRunner

from telegram_integration.cli import listen_app, send_app

runner = CliRunner()


class TestSendCommand:
    @patch("telegram_integration.client.requests.post")
    def test_send_markdown_default(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 9}}
        mock_post.return_value = mock_response

        result = runner.invoke(send_app, ["*Bold* message"])

        assert result.exit_code == 0
        assert "Message sent successfully" in result.output
        body = mock_post.call_args.kwargs["json"]
        assert body["parse_mode"] == "Markdown"
        assert body["text"] == "*Bold* message"

    @patch("telegram_integration.client.requests.post")
    def test_send_plain_mode(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {}}
        mock_post.return_value = mock_response

        result = runner.invoke(send_app, ["hello", "-m", "plain"])

        assert result.exit_code == 0
        body = mock_post.call_args.kwargs["json"]
        assert body["parse_mode"] is None

    @patch("telegram_integration.client.requests.post")
    def test_send_html_mode(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {}}
        mock_post.return_value = mock_response

        result = runner.invoke(send_app, ["<b>hi</b>", "-m", "html"])

        assert result.exit_code == 0
        body = mock_post.call_args.kwargs["json"]
        assert body["parse_mode"] == "HTML"

    def test_send_requires_message(self):
        result = runner.invoke(send_app, [])
        assert result.exit_code != 0
        assert "missing argument 'message'" in result.output.lower()


class TestListenCommand:
    @patch("telegram_integration.cli.MessageReceiver")
    def test_listen_registers_callbacks(self, mock_receiver_cls):
        receiver = Mock()
        mock_receiver_cls.return_value = receiver

        result = runner.invoke(
            listen_app,
            ["--scripts", "worker_a.py", "--timeout", "10", "--interval", "2.0"],
        )

        assert result.exit_code == 0
        assert receiver.register_callback.call_count == 2
        receiver.listen.assert_called_once_with(timeout=10, poll_interval=2.0)

    @patch("telegram_integration.cli.MessageReceiver")
    def test_listen_without_scripts(self, mock_receiver_cls):
        receiver = Mock()
        mock_receiver_cls.return_value = receiver

        result = runner.invoke(listen_app, [])

        assert result.exit_code == 0
        assert receiver.register_callback.call_count == 1
        receiver.listen.assert_called_once()

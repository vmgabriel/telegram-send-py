from unittest.mock import Mock, patch

import pytest

from telegram_integration import MessageReceiver, MessageSender, TelegramClient
from telegram_integration.infrastructure import ConfigFileNotFoundError


class TestTelegramClient:
    def test_init_with_env_vars(self):
        client = TelegramClient()
        assert client.token == "test_token"
        assert client.channel_id == "test_channel_id"

    def test_init_with_params(self):
        client = TelegramClient(token="custom_token", channel_id="custom_channel")
        assert client.token == "custom_token"
        assert client.channel_id == "custom_channel"

    def test_init_missing_token(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
        with pytest.raises(ConfigFileNotFoundError, match="TELEGRAM_TOKEN"):
            TelegramClient()

    def test_init_missing_channel_id(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)
        with pytest.raises(ConfigFileNotFoundError, match="TELEGRAM_CHANNEL_ID"):
            TelegramClient()

    @patch("telegram_integration.client.requests.get")
    def test_get_updates(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": []}
        mock_get.return_value = mock_response

        client = TelegramClient()
        result = client.get_updates(offset=100, timeout=30)

        assert result["ok"] is True
        mock_get.assert_called_once()
        kwargs = mock_get.call_args.kwargs
        assert kwargs["params"]["offset"] == 100
        assert kwargs["params"]["timeout"] == 30


class TestMessageSender:
    @patch("telegram_integration.client.requests.post")
    def test_send_markdown(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
        mock_post.return_value = mock_response

        sender = MessageSender()
        result = sender.send_markdown("*Bold text*")

        assert result["ok"] is True
        body = mock_post.call_args.kwargs["json"]
        assert body["chat_id"] == "test_channel_id"
        assert body["text"] == "*Bold text*"
        assert body["parse_mode"] == "Markdown"

    @patch("telegram_integration.client.requests.post")
    def test_send_plain(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {}}
        mock_post.return_value = mock_response

        sender = MessageSender()
        result = sender.send_plain("Hello")

        assert result["ok"] is True
        body = mock_post.call_args.kwargs["json"]
        assert body["parse_mode"] is None

    @patch("telegram_integration.client.requests.post")
    def test_send_html(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {}}
        mock_post.return_value = mock_response

        sender = MessageSender()
        result = sender.send_html("<b>Hello</b>")

        assert result["ok"] is True
        body = mock_post.call_args.kwargs["json"]
        assert body["parse_mode"] == "HTML"


class TestMessageReceiver:
    def test_register_callback(self):
        receiver = MessageReceiver()
        callback = Mock()
        receiver.register_callback(callback)
        assert callback in receiver.callbacks

    def test_process_update(self):
        receiver = MessageReceiver()
        callback = Mock()
        receiver.register_callback(callback)

        update = {"update_id": 1, "message": {"text": "test"}}
        receiver.process_update(update)

        callback.assert_called_once_with(update)

    def test_multiple_callbacks(self):
        receiver = MessageReceiver()
        callback1 = Mock()
        callback2 = Mock()
        receiver.register_callback(callback1)
        receiver.register_callback(callback2)

        update = {"update_id": 2}
        receiver.process_update(update)

        callback1.assert_called_once_with(update)
        callback2.assert_called_once_with(update)

    @patch("telegram_integration.receiver.subprocess.Popen")
    def test_trigger_scripts(self, mock_popen):
        receiver = MessageReceiver()
        message = {"update_id": 1, "message": {"text": "trigger"}}

        receiver.trigger_scripts(message, ["script_a.py", "script_b.py"])

        assert mock_popen.call_count == 2

    @patch("telegram_integration.receiver.subprocess.Popen")
    def test_trigger_scripts_handles_error(self, mock_popen):
        mock_popen.side_effect = OSError("script not found")
        receiver = MessageReceiver()
        message = {"update_id": 1}

        receiver.trigger_scripts(message, ["missing_script.py"])

        mock_popen.assert_called_once()

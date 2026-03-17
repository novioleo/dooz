import pytest
from dooz_daemon.websocket_server import WsMessage


def test_ws_message_parse():
    msg = WsMessage(type="user_message", content="hello", session_id="123")
    assert msg.type == "user_message"
    assert msg.content == "hello"
    assert msg.session_id == "123"

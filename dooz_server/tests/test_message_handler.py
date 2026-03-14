# tests/test_message_handler.py
import pytest
from unittest.mock import Mock, AsyncMock
from dooz_server.message_handler import MessageHandler
from dooz_server.client_manager import ClientManager
from dooz_server.message_queue import MessageQueue


@pytest.fixture
def client_manager():
    return ClientManager()


@pytest.fixture
def message_queue():
    return MessageQueue()


@pytest.fixture
def message_handler(client_manager, message_queue):
    return MessageHandler(client_manager, message_queue)


def test_send_message_to_online_client(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    
    # Mock the websocket send
    mock_ws = Mock()
    mock_ws.send_json = AsyncMock()
    client_manager.add_connection(recipient_id, mock_ws)
    
    success, msg, msg_id = message_handler.send_message(sender_id, recipient_id, "Hello!")
    assert success is True
    mock_ws.send_json.assert_called_once()


def test_send_message_to_nonexistent(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    success, msg, msg_id = message_handler.send_message(sender_id, "nonexistent", "Hello!")
    assert success is False


def test_send_message_to_offline_client_queues(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    # Don't add connection - recipient is offline
    
    success, msg, msg_id = message_handler.send_message(sender_id, recipient_id, "Hello!")
    assert success is True
    assert msg_id is not None  # Message was queued
    assert "queued" in msg.lower()


def test_send_message_with_ttl_zero_no_queue(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    # Don't add connection - recipient is offline
    
    success, msg, msg_id = message_handler.send_message(
        sender_id, recipient_id, "Hello!", ttl_seconds=0
    )
    assert success is False
    assert "offline" in msg.lower()


def test_deliver_pending_messages(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    
    # Queue a message while recipient is offline
    success, msg, msg_id = message_handler.send_message(
        sender_id, recipient_id, "Hello!"
    )
    
    # Now connect the recipient
    mock_ws = Mock()
    mock_ws.send_json = AsyncMock()
    client_manager.add_connection(recipient_id, mock_ws)
    
    # Deliver pending messages
    delivered = message_handler.deliver_pending_messages(recipient_id)
    assert delivered == 1
    mock_ws.send_json.assert_called_once()


def test_get_pending_messages(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    
    # Queue a message
    message_handler.send_message(sender_id, recipient_id, "Hello!")
    
    # Get pending
    pending = message_handler.get_pending_messages(recipient_id)
    assert len(pending) == 1


def test_broadcast_message(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    client_manager.register_client("user1")
    client_manager.register_client("user2")
    
    # Connect users
    for client in client_manager.get_all_clients():
        if client.client_id != sender_id:
            mock_ws = Mock()
            mock_ws.send_json = AsyncMock()
            client_manager.add_connection(client.client_id, mock_ws)
    
    count = message_handler.broadcast_message(sender_id, "Hello all!")
    assert count == 2

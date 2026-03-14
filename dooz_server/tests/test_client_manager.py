# tests/test_client_manager.py
import pytest
from dooz_server.client_manager import ClientManager


@pytest.fixture
def client_manager():
    return ClientManager()


def test_register_client(client_manager):
    client_id = client_manager.register_client("user1", "WebSocket")
    assert client_id is not None
    assert len(client_manager.get_all_clients()) == 1


def test_unregister_client(client_manager):
    client_id = client_manager.register_client("user1", "WebSocket")
    client_manager.unregister_client(client_id)
    assert len(client_manager.get_all_clients()) == 0


def test_get_client_info(client_manager):
    client_id = client_manager.register_client(client_id="test-001", name="user1", connection_type="WebSocket")
    info = client_manager.get_client_info(client_id)
    assert info is not None
    assert info.name == "user1"


def test_list_all_clients(client_manager):
    client_manager.register_client("user1", "WebSocket")
    client_manager.register_client("user2", "WebSocket")
    clients = client_manager.get_all_clients()
    assert len(clients) == 2


def test_get_nonexistent_client(client_manager):
    info = client_manager.get_client_info("nonexistent")
    assert info is None


def test_add_connection(client_manager):
    client_id = client_manager.register_client("user1", "WebSocket")
    mock_ws = object()
    result = client_manager.add_connection(client_id, mock_ws)
    assert result is True
    assert client_manager.get_connection(client_id) is mock_ws


def test_is_connected(client_manager):
    client_id = client_manager.register_client("user1", "WebSocket")
    assert client_manager.is_connected(client_id) is False
    mock_ws = object()
    client_manager.add_connection(client_id, mock_ws)
    assert client_manager.is_connected(client_id) is True

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


def test_register_client_with_profile(client_manager):
    """Test registering a client with profile information."""
    from dooz_server.schemas import ClientProfile
    
    profile = ClientProfile(
        device_id="device-001",
        name="TestAgent",
        role="agent",
        skills=[("echo", "Echo back input"), ("ls", "List directory")],
        supports_input=True,
        supports_output=False
    )
    client_id = client_manager.register_client(
        client_id="agent-001",
        name="TestAgent",
        profile=profile,
        connection_type="WebSocket"
    )
    
    info = client_manager.get_client_info(client_id)
    assert info is not None
    assert info.profile is not None
    assert info.profile.device_id == "device-001"
    assert info.profile.name == "TestAgent"
    assert info.profile.role == "agent"
    assert info.profile.skills == [("echo", "Echo back input"), ("ls", "List directory")]
    assert info.profile.supports_input is True
    assert info.profile.supports_output is False


def test_register_client_without_profile(client_manager):
    """Test that profile is optional when registering."""
    client_id = client_manager.register_client(
        client_id="user-001",
        name="RegularUser",
        connection_type="WebSocket"
    )
    
    info = client_manager.get_client_info(client_id)
    assert info is not None
    assert info.profile is None

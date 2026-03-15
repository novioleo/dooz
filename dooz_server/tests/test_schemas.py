# tests/test_schemas.py
import pytest
from pydantic import ValidationError
from dooz_server.schemas import ClientInfo, MessageRequest, MessageResponse, ClientListResponse, ClientProfile


def test_client_profile_required_fields():
    """Test that name and role are required."""
    # Missing name should fail
    with pytest.raises(ValidationError):
        ClientProfile(role="agent")
    
    # Missing role should fail
    with pytest.raises(ValidationError):
        ClientProfile(name="TestClient")
    # Both present should pass
    profile = ClientProfile(name="TestClient", role="agent")
    assert profile.name == "TestClient"
    assert profile.role == "agent"


def test_client_profile_optional_fields():
    """Test optional fields have correct defaults."""
    profile = ClientProfile(name="TestClient", role="agent")
    assert profile.extra_info is None
    assert profile.skills == []
    assert profile.supports_input is False
    assert profile.supports_output is False


def test_client_profile_all_fields():
    """Test creating profile with all fields."""
    # skills is list[tuple[str, str]] - (ability_name, ability_description)
    profile = ClientProfile(
        name="TestClient",
        role="agent",
        extra_info="Custom info",
        skills=[("echo", "Echo back the input"), ("ls", "List directory contents")],
        supports_input=True,
        supports_output=True
    )
    assert profile.name == "TestClient"
    assert profile.role == "agent"
    assert profile.extra_info == "Custom info"
    assert profile.skills == [("echo", "Echo back the input"), ("ls", "List directory contents")]
    assert profile.supports_input is True
    assert profile.supports_output is True


def test_client_profile_extra_fields_ignored():
    """Test that extra fields are ignored (not strictly validated)."""
    # Extra fields should not raise validation error
    profile = ClientProfile(
        name="TestClient",
        role="agent",
        unknown_field="should be ignored"
    )
    assert profile.name == "TestClient"
    # The unknown_field should not be in the model
    assert not hasattr(profile, 'unknown_field')


def test_client_info_creation():
    client = ClientInfo(client_id="test-123", name="TestUser", connected_at="2024-01-01T00:00:00Z")
    assert client.client_id == "test-123"
    assert client.name == "TestUser"


def test_message_request_valid():
    req = MessageRequest(to_client_id="client-456", content="Hello!")
    assert req.to_client_id == "client-456"
    assert req.content == "Hello!"


def test_message_request_empty_content():
    with pytest.raises(ValidationError):
        MessageRequest(to_client_id="client-456", content="")


def test_message_request_with_ttl():
    req = MessageRequest(to_client_id="client-456", content="Hello!", ttl_seconds=600)
    assert req.ttl_seconds == 600


def test_message_request_default_ttl():
    req = MessageRequest(to_client_id="client-456", content="Hello!")
    assert req.ttl_seconds == 3600


def test_message_response_creation():
    resp = MessageResponse(success=True, message="Sent successfully")
    assert resp.success is True
    assert resp.message == "Sent successfully"


def test_message_response_with_message_id():
    resp = MessageResponse(success=True, message="Queued", message_id="msg-123")
    assert resp.message_id == "msg-123"


def test_client_list_response():
    clients = [
        ClientInfo(client_id="c1", name="User1", connected_at="2024-01-01T00:00:00Z"),
        ClientInfo(client_id="c2", name="User2", connected_at="2024-01-01T00:00:00Z"),
    ]
    response = ClientListResponse(clients=clients, total=2)
    assert len(response.clients) == 2
    assert response.total == 2


def test_client_info_with_profile():
    """Test that ClientInfo accepts profile field."""
    profile = ClientProfile(name="TestClient", role="agent", supports_input=True)
    client = ClientInfo(
        client_id="test-123",
        name="TestUser",
        connected_at="2024-01-01T00:00:00Z",
        profile=profile
    )
    assert client.client_id == "test-123"
    assert client.profile.name == "TestClient"
    assert client.profile.role == "agent"
    assert client.profile.supports_input is True


def test_client_info_profile_optional():
    """Test that profile is optional in ClientInfo."""
    client = ClientInfo(
        client_id="test-123",
        name="TestUser",
        connected_at="2024-01-01T00:00:00Z"
    )
    assert client.profile is None

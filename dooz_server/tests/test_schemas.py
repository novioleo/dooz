# tests/test_schemas.py
import pytest
from pydantic import ValidationError
from dooz_server.schemas import ClientInfo, MessageRequest, MessageResponse, ClientListResponse


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

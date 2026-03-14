# tests/test_router.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from dooz_server.router import router, get_client_manager, get_message_handler
from dooz_server.client_manager import ClientManager
from dooz_server.message_handler import MessageHandler
from dooz_server.message_queue import MessageQueue


@pytest.fixture
def client_manager():
    return ClientManager()


@pytest.fixture
def message_handler(client_manager):
    return MessageHandler(client_manager, MessageQueue())


@pytest.fixture
def test_app(client_manager, message_handler):
    app = FastAPI()
    app.include_router(router)
    # Override dependencies on the app
    app.dependency_overrides[get_client_manager] = lambda: client_manager
    app.dependency_overrides[get_message_handler] = lambda: message_handler
    return app


@pytest.fixture
def test_client(test_app):
    return TestClient(test_app)


def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_clients_empty(test_client):
    response = test_client.get("/clients")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["clients"] == []


def test_list_clients(test_client, client_manager):
    client_manager.register_client("user1")
    client_manager.register_client("user2")
    
    response = test_client.get("/clients")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["clients"]) == 2


def test_get_client(test_client, client_manager):
    client_id = client_manager.register_client("user1")
    
    response = test_client.get(f"/clients/{client_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "user1"


def test_get_nonexistent_client(test_client):
    response = test_client.get("/clients/nonexistent-id")
    assert response.status_code == 404

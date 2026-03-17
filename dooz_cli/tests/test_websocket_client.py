import pytest
from dooz_cli.websocket_client import CliClient


def test_cli_client_initialization():
    client = CliClient("ws://localhost:8765")
    assert client.uri == "ws://localhost:8765"

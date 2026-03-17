import pytest
from unittest.mock import Mock
from dooz_daemon.mqtt_client import MqttClient, MqttMessage

@pytest.mark.asyncio
async def test_mqtt_client_initialization():
    client = MqttClient("localhost", 1883, "test-client")
    assert client.broker == "localhost"
    assert client.port == 1883
    assert client.client_id == "test-client"

import pytest
from dooz_daemon.config import DaemonConfig, load_config


def test_default_config():
    config = DaemonConfig()
    assert config.host == "0.0.0.0"
    assert config.port == 8765
    assert config.mqtt.broker == "localhost"
    assert config.mqtt.port == 1883


def test_load_config_from_dict():
    config = DaemonConfig(
        host="127.0.0.1",
        port=9000,
        mqtt={"broker": "mqtt.local", "port": 1884}
    )
    assert config.host == "127.0.0.1"
    assert config.port == 9000
    assert config.mqtt.broker == "mqtt.local"

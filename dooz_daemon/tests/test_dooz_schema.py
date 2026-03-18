"""Tests for dooz schema."""

import pytest
from pydantic import ValidationError
from dooz_daemon.schemas.dooz import DoozDefinition, DoozMqttConfig


def test_dooz_definition_valid():
    """Test valid dooz definition."""
    dooz = DoozDefinition(
        dooz_id="dooz_1_1",
        name="智能家居",
        description="控制家中智能设备",
        role="dooz-group",
        agents=["light-agent", "speaker-agent"],
        nested_dooz=["dooz_2_1"],
        mqtt=DoozMqttConfig(topic_prefix="dooz/dooz_1_1"),
    )
    assert dooz.dooz_id == "dooz_1_1"
    assert dooz.role == "dooz-group"
    assert "light-agent" in dooz.agents
    assert "dooz_2_1" in dooz.nested_dooz


def test_dooz_id_format():
    """Test dooz_id format validation."""
    with pytest.raises(ValidationError):
        DoozDefinition(
            dooz_id="invalid",
            name="测试",
            mqtt=DoozMqttConfig(),
        )


def test_dooz_defaults():
    """Test default values."""
    dooz = DoozDefinition(
        dooz_id="dooz_1_1",
        name="测试",
        mqtt=DoozMqttConfig(),
    )
    assert dooz.role == "dooz"
    assert dooz.agents == []
    assert dooz.nested_dooz == []
    assert dooz.capabilities == []

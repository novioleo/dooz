"""Tests for agent schema."""

import pytest
from pydantic import ValidationError
from dooz_daemon.schemas.agent import AgentDefinition, AgentMqttConfig, Skill


def test_agent_definition_valid():
    """Test valid agent definition."""
    agent = AgentDefinition(
        agent_id="light-agent",
        name="灯光控制",
        description="控制家中灯光",
        role="sub-agent",
        capabilities=["light_on", "light_off"],
        mqtt=AgentMqttConfig(
            topic="light-control",
            subscribe=["tasks/light-agent"],
        ),
    )
    assert agent.agent_id == "light-agent"
    assert agent.role == "sub-agent"
    assert "light_on" in agent.capabilities


def test_agent_definition_defaults():
    """Test default values."""
    agent = AgentDefinition(
        agent_id="test-agent",
        name="测试",
        mqtt=AgentMqttConfig(topic="test"),
    )
    assert agent.role == "sub-agent"
    assert agent.capabilities == []
    assert agent.skills == []


def test_agent_mqtt_config():
    """Test MQTT config."""
    mqtt = AgentMqttConfig(
        topic="light",
        subscribe=["tasks/light"],
        publish=["results/light"],
    )
    assert mqtt.topic == "light"
    assert "tasks/light" in mqtt.subscribe

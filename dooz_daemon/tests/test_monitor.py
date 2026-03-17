"""Tests for Monitor Agent."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from dooz_daemon.agents.base import AgentConfig
from dooz_daemon.agents.monitor import MonitorAgent


@pytest.fixture
def config():
    return AgentConfig(
        agent_id="monitor",
        dooz_id="test-dooz",
        mqtt_broker="localhost",
        mqtt_port=1883,
    )


@pytest.fixture
def monitor_agent(config):
    return MonitorAgent(config)


def test_monitor_agent_initialization(monitor_agent, config):
    """Test MonitorAgent initialization."""
    assert monitor_agent.config.agent_id == "monitor"
    assert monitor_agent.config.dooz_id == "test-dooz"
    assert monitor_agent._agents == {}
    assert monitor_agent._offline_threshold == 30


def test_subscribe_topics(monitor_agent, config):
    """Test that subscribe_topics is correct."""
    topics = monitor_agent.subscribe_topics
    assert f"dooz/{config.dooz_id}/agents/+/heartbeat" in topics
    assert f"dooz/{config.dooz_id}/system/monitor" in topics


@pytest.mark.asyncio
async def test_handle_heartbeat(monitor_agent):
    """Test heartbeat handling."""
    # Create mock message
    msg = MagicMock()
    msg.type = "heartbeat"
    msg.payload = {
        "agent_id": "worker-1",
        "name": "Worker One",
        "capabilities": ["coding", "testing"],
    }
    
    await monitor_agent.handle_message(msg)
    
    assert "worker-1" in monitor_agent._agents
    assert monitor_agent._agents["worker-1"]["name"] == "Worker One"
    assert monitor_agent._agents["worker-1"]["capabilities"] == ["coding", "testing"]
    assert monitor_agent._agents["worker-1"]["status"] == "online"


@pytest.mark.asyncio
async def test_handle_query_agents(monitor_agent):
    """Test query_agents handling."""
    # Add some agents
    monitor_agent._agents["agent-1"] = {
        "last_seen": time.time(),
        "status": "online",
        "capabilities": ["coding"],
        "name": "Agent One",
    }
    monitor_agent._agents["agent-2"] = {
        "last_seen": time.time() - 60,  # Offline (超过30秒阈值)
        "status": "online",
        "capabilities": ["testing"],
        "name": "Agent Two",
    }
    
    # Create mock message
    msg = MagicMock()
    msg.type = "query_agents"
    msg.payload = {
        "request_id": "req-123",
        "from_dooz": "test-dooz",
    }
    
    # Mock publish to capture response
    monitor_agent.publish = AsyncMock()
    
    await monitor_agent.handle_message(msg)
    
    # Verify publish was called with agent_list
    monitor_agent.publish.assert_called_once()
    call_args = monitor_agent.publish.call_args
    topic = call_args[0][0]
    response_msg = call_args[0][1]
    
    assert "response" in topic
    assert response_msg.type == "agent_list"
    assert response_msg.payload["agents"][0]["agent_id"] == "agent-1"


@pytest.mark.asyncio
async def test_offline_threshold(monitor_agent):
    """Test that offline agents are filtered out."""
    # Add an agent that's still online
    monitor_agent._agents["online-agent"] = {
        "last_seen": time.time(),
        "status": "online",
        "capabilities": [],
        "name": "Online Agent",
    }
    
    # Add an agent that's offline
    monitor_agent._agents["offline-agent"] = {
        "last_seen": time.time() - 60,  # 60 seconds ago
        "status": "online",
        "capabilities": [],
        "name": "Offline Agent",
    }
    
    # Create query message
    msg = MagicMock()
    msg.type = "query_agents"
    msg.payload = {
        "request_id": "req-456",
        "from_dooz": "test-dooz",
    }
    
    monitor_agent.publish = AsyncMock()
    
    await monitor_agent.handle_message(msg)
    
    # Only online agent should be in response
    call_args = monitor_agent.publish.call_args
    response_msg = call_args[0][1]
    agents = response_msg.payload["agents"]
    
    assert len(agents) == 1
    assert agents[0]["agent_id"] == "online-agent"

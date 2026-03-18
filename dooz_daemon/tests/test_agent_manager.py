"""Tests for agent manager."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from dooz_daemon.agent_manager import AgentProcess, AgentProcessManager


def test_agent_process_creation():
    """Test creating an AgentProcess."""
    process = AgentProcess(
        agent_id="light-agent",
        name="灯光控制",
        dooz_id="dooz_1_1",
        mqtt_topic="dooz/dooz_1_1/agents/light-control",
    )
    assert process.agent_id == "light-agent"
    assert process.dooz_id == "dooz_1_1"


def test_agent_process_manager_init():
    """Test initializing AgentProcessManager."""
    manager = AgentProcessManager(
        dooz_id="dooz_1_1",
        definitions_dir=Path("/tmp/defs"),
    )
    assert manager.dooz_id == "dooz_1_1"
    assert len(manager.processes) == 0


def test_spawn_agent():
    """Test spawning an agent."""
    manager = AgentProcessManager(
        dooz_id="dooz_1_1",
        definitions_dir=Path("/tmp/defs"),
    )
    
    process = manager.spawn_agent(
        agent_id="light-agent",
        name="灯光",
        mqtt_topic="light",
    )
    
    assert process is not None
    assert process.agent_id == "light-agent"
    assert process.mqtt_topic == "dooz/dooz_1_1/agents/light"


def test_spawn_duplicate_agent():
    """Test spawning duplicate agent returns existing."""
    manager = AgentProcessManager(
        dooz_id="dooz_1_1",
        definitions_dir=Path("/tmp/defs"),
    )
    
    # Spawn twice
    process1 = manager.spawn_agent(agent_id="light-agent", name="灯光", mqtt_topic="light")
    process2 = manager.spawn_agent(agent_id="light-agent", name="灯光", mqtt_topic="light")
    
    # Should return same process
    assert process1 == process2


@pytest.mark.asyncio
async def test_stop_agent():
    """Test stopping an agent."""
    manager = AgentProcessManager(
        dooz_id="dooz_1_1",
        definitions_dir=Path("/tmp/defs"),
    )
    
    # Spawn agent
    manager.spawn_agent(agent_id="light-agent", name="灯光", mqtt_topic="light")
    assert len(manager.processes) == 1
    
    # Stop
    result = await manager.stop_agent("light-agent")
    assert result is True
    assert len(manager.processes) == 0


def test_get_all_agents():
    """Test getting all agents."""
    manager = AgentProcessManager(
        dooz_id="dooz_1_1",
        definitions_dir=Path("/tmp/defs"),
    )
    
    manager.spawn_agent(agent_id="light-agent", name="灯光", mqtt_topic="light")
    manager.spawn_agent(agent_id="speaker-agent", name="音箱", mqtt_topic="speaker")
    
    agents = manager.get_all_agents()
    assert len(agents) == 2

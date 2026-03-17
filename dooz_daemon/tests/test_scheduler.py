"""Tests for Scheduler Agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from dooz_daemon.agents.base import AgentConfig
from dooz_daemon.agents.scheduler import SchedulerAgent


@pytest.fixture
def config():
    return AgentConfig(
        agent_id="scheduler",
        dooz_id="test-dooz",
        mqtt_broker="localhost",
        mqtt_port=1883,
    )


@pytest.fixture
def scheduler_agent(config):
    return SchedulerAgent(config)


def test_scheduler_agent_initialization(scheduler_agent, config):
    """Test SchedulerAgent initialization."""
    assert scheduler_agent.config.agent_id == "scheduler"
    assert scheduler_agent.config.dooz_id == "test-dooz"
    assert scheduler_agent._pending_tasks == {}


def test_subscribe_topics(scheduler_agent, config):
    """Test that subscribe_topics is correct."""
    topics = scheduler_agent.subscribe_topics
    assert f"dooz/{config.dooz_id}/system/scheduler" in topics


@pytest.mark.asyncio
async def test_handle_task_submit_single(scheduler_agent):
    """Test task submission with a single sub-task."""
    # Create mock message
    msg = MagicMock()
    msg.type = "task_submit"
    msg.payload = {
        "task_id": "task-123",
        "goal": "Implement feature X",
        "sub_tasks": [
            {
                "agent_id": "worker-1",
                "sub_task_id": "sub-1",
                "goal": "Implement feature X",
                "parameters": {"priority": "high"},
            }
        ],
    }
    
    # Mock publish
    scheduler_agent.publish = AsyncMock()
    
    await scheduler_agent.handle_message(msg)
    
    # Verify publish was called twice: once for task dispatch, once for response
    assert scheduler_agent.publish.call_count == 2
    
    # First call should be the task to the agent
    first_call = scheduler_agent.publish.call_args_list[0]
    topic = first_call[0][0]
    task_msg = first_call[0][1]
    
    assert "tasks/worker-1" in topic
    assert task_msg.type == "task"
    assert task_msg.payload["task_id"] == "task-123"
    assert task_msg.payload["goal"] == "Implement feature X"
    
    # Second call should be the response to orchestrator
    second_call = scheduler_agent.publish.call_args_list[1]
    response_topic = second_call[0][0]
    response_msg = second_call[0][1]
    
    assert "orchestrator" in response_topic
    assert response_msg.type == "task_result"
    assert response_msg.payload["status"] == "dispatched"
    assert response_msg.payload["sub_tasks"] == 1


@pytest.mark.asyncio
async def test_handle_task_submit_multiple(scheduler_agent):
    """Test task submission with multiple sub-tasks."""
    msg = MagicMock()
    msg.type = "task_submit"
    msg.payload = {
        "task_id": "task-456",
        "goal": "Build system",
        "sub_tasks": [
            {"agent_id": "worker-1", "goal": "Part 1"},
            {"agent_id": "worker-2", "goal": "Part 2"},
            {"agent_id": "worker-3", "goal": "Part 3"},
        ],
    }
    
    scheduler_agent.publish = AsyncMock()
    
    await scheduler_agent.handle_message(msg)
    
    # Should have 4 publishes: 3 tasks + 1 response
    assert scheduler_agent.publish.call_count == 4
    
    # First three should be task dispatches
    for i in range(3):
        call = scheduler_agent.publish.call_args_list[i]
        topic = call[0][0]
        assert "tasks/worker-" in topic


@pytest.mark.asyncio
async def test_handle_task_submit_generates_task_id(scheduler_agent):
    """Test that task_id is generated if not provided."""
    msg = MagicMock()
    msg.type = "task_submit"
    msg.payload = {
        "goal": "Some task",
        "sub_tasks": [
            {"agent_id": "worker-1"},
        ],
    }
    
    scheduler_agent.publish = AsyncMock()
    
    await scheduler_agent.handle_message(msg)
    
    # Get the task message from first publish
    first_call = scheduler_agent.publish.call_args_list[0]
    task_msg = first_call[0][1]
    
    # task_id should be generated (not empty)
    assert task_msg.payload["task_id"] is not None
    assert len(task_msg.payload["task_id"]) > 0

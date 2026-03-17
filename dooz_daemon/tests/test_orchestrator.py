"""Tests for Orchestrator Agent."""

import logging
import pytest
from unittest.mock import AsyncMock

from dooz_daemon.agents.base import AgentConfig, AgentMessage
from dooz_daemon.agents.orchestrator import OrchestratorAgent


@pytest.fixture
def config():
    return AgentConfig(
        agent_id="orchestrator",
        dooz_id="test-dooz",
        mqtt_broker="localhost",
        mqtt_port=1883,
    )


@pytest.fixture
def orchestrator_agent(config):
    return OrchestratorAgent(config)


def test_orchestrator_agent_initialization(orchestrator_agent, config):
    """Test OrchestratorAgent initialization."""
    assert orchestrator_agent.config.agent_id == "orchestrator"
    assert orchestrator_agent.config.dooz_id == "test-dooz"


def test_subscribe_topics(orchestrator_agent, config):
    """Test that subscribe_topics is correct."""
    topics = orchestrator_agent.subscribe_topics
    assert f"dooz/{config.dooz_id}/system/orchestrator" in topics


@pytest.mark.asyncio
async def test_handle_user_message(orchestrator_agent):
    """Test user message handling."""
    # Create proper AgentMessage
    msg = AgentMessage(
        type="user_message",
        agent_id="test-agent",
        dooz_id="test-dooz",
        payload={
            "session_id": "session-123",
            "content": "Hello, dooz!",
        },
    )
    
    # Mock publish to avoid actual MQTT calls
    orchestrator_agent.publish = AsyncMock()
    
    await orchestrator_agent.handle_message(msg)
    
    # Verify publish was called with response
    orchestrator_agent.publish.assert_called_once()
    call_args = orchestrator_agent.publish.call_args
    response_msg = call_args[0][1]
    
    assert response_msg.type == "response"
    assert response_msg.payload["session_id"] == "session-123"
    assert "Hello, dooz!" in response_msg.payload["content"]


@pytest.mark.asyncio
async def test_handle_task_result(orchestrator_agent):
    """Test task result handling."""
    # Create proper AgentMessage
    msg = AgentMessage(
        type="task_result",
        agent_id="scheduler",
        dooz_id="test-dooz",
        payload={
            "task_id": "task-789",
            "status": "completed",
        },
    )
    
    # Mock publish 
    orchestrator_agent.publish = AsyncMock()
    
    # Handle message - task_result doesn't publish in current implementation
    await orchestrator_agent.handle_message(msg)
    
    # Verify the method handled the message (no publish for task_result currently)
    # This test verifies no exception is raised


@pytest.mark.asyncio
async def test_handle_unknown_message_type(orchestrator_agent):
    """Test handling of unknown message types."""
    msg = AgentMessage(
        type="unknown_type",
        agent_id="test-agent",
        dooz_id="test-dooz",
        payload={},
    )
    
    # Should not raise an exception
    await orchestrator_agent.handle_message(msg)


@pytest.mark.asyncio
async def test_user_message_echo_response(orchestrator_agent):
    """Test that user message generates an echo response."""
    msg = AgentMessage(
        type="user_message",
        agent_id="test-agent",
        dooz_id="test-dooz",
        payload={
            "session_id": "session-456",
            "content": "Test message",
        },
    )
    
    # Mock publish to capture the response
    orchestrator_agent.publish = AsyncMock()
    
    await orchestrator_agent.handle_message(msg)
    
    # Verify publish was called (response would be sent)
    orchestrator_agent.publish.assert_called_once()
    
    call_args = orchestrator_agent.publish.call_args
    response_msg = call_args[0][1]
    
    assert response_msg.type == "response"
    assert response_msg.payload["session_id"] == "session-456"
    assert "Test message" in response_msg.payload["content"]

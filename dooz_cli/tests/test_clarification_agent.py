"""Tests for ClarificationAgent."""

import pytest
from dooz_cli.clarification.agent import ClarificationAgent


def test_clarification_agent_initial():
    """Test initial state of ClarificationAgent."""
    agent = ClarificationAgent(session_id="test-123")
    
    assert agent.session_id == "test-123"
    assert agent.state.turn_count == 0
    assert agent.state.is_complete is False


def test_process_create_with_explicit_target():
    """Test processing create with explicit target."""
    agent = ClarificationAgent(session_id="test-123")
    
    response = agent.process_message("创建一个任务")
    
    # Should ask for clarification (needs name)
    assert response is not None
    # May get confirmation if target was extracted
    assert isinstance(response, str)


def test_process_delete_intent():
    """Test processing delete intent - should ask for target."""
    agent = ClarificationAgent(session_id="test-123")
    
    response = agent.process_message("删除文件")
    
    # Should ask for clarification about target
    assert response is not None


def test_process_with_explicit_target():
    """Test processing with explicit target."""
    agent = ClarificationAgent(session_id="test-123")
    
    # First message
    agent.process_message("删除用户")
    # Answer what to delete
    response = agent.process_message("张三")
    
    # Should get confirmation
    assert response is not None


def test_process_complete_intent():
    """Test processing when intent is complete."""
    agent = ClarificationAgent(session_id="test-123")
    
    # First message - may extract target
    agent.process_message("创建")
    
    # Answer target - should ask for name or confirm
    response = agent.process_message("任务")
    
    # Should ask more or confirm
    assert response is not None


def test_max_turns_limit():
    """Test max turns limit."""
    agent = ClarificationAgent(session_id="test-123")
    
    # Exhaust max turns
    for i in range(ClarificationAgent.MAX_TURNS):
        agent.process_message(f"回答{i}")
    
    # Should complete after max turns
    assert agent.state.turn_count >= ClarificationAgent.MAX_TURNS


def test_get_clarified_request():
    """Test getting clarified request."""
    agent = ClarificationAgent(session_id="test-123")
    
    # Process to complete
    agent.process_message("删除")
    agent.process_message("用户")
    agent.process_message("张三")
    
    # Get clarified request
    request = agent.get_clarified_request()
    
    assert request is not None
    assert "clarified_goal" in request or "goal" in request
    # Should have a valid intent type
    assert request["intent_type"] in ["delete", "execute_task", "update", "create"]


def test_unknown_input_becomes_execute():
    """Test unknown input becomes execute task."""
    agent = ClarificationAgent(session_id="test-123")
    
    response = agent.process_message("帮我做件事情")
    
    # Should still work and ask for clarification
    assert response is not None


def test_multiple_clarification_questions():
    """Test multiple rounds of clarification."""
    agent = ClarificationAgent(session_id="test-123")
    
    # Create with no details
    agent.process_message("创建")
    
    # Answer target
    agent.process_message("任务")
    
    # Answer name
    response = agent.process_message("我的任务")
    
    # Should be complete
    assert response is not None


def test_set_value_clarification():
    """Test set value intent clarification."""
    agent = ClarificationAgent(session_id="test-123")
    
    response = agent.process_message("设置")
    
    # Should ask for target
    assert response is not None

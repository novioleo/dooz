"""Tests for clarification state models."""

import pytest
from dooz_cli.clarification.state import (
    ClarificationState,
    ConversationTurn,
    Intent,
    IntentType,
)


def test_clarification_state_initial():
    """Test initial clarification state."""
    state = ClarificationState(session_id="test-123")
    assert state.session_id == "test-123"
    assert state.turn_count == 0
    assert state.intent is None
    assert state.is_complete is False


def test_clarification_state_add_turn():
    """Test adding conversation turns."""
    state = ClarificationState(session_id="test-123")
    
    state.add_turn("user", "创建一个任务")
    assert state.turn_count == 1
    assert state.last_user_input == "创建一个任务"
    
    state.add_turn("agent", "请问您想创建什么任务？")
    assert state.turn_count == 1  # Only user turns count


def test_intent_creation():
    """Test creating an intent."""
    intent = Intent(
        type=IntentType.CREATE,
        confidence=0.9,
        entities={"target": "task", "name": "my-task"},
    )
    assert intent.type == IntentType.CREATE
    assert intent.confidence == 0.9
    assert intent.entities["target"] == "task"


def test_intent_types():
    """Test all intent types."""
    assert IntentType.GET_INFO.value == "get_info"
    assert IntentType.CREATE.value == "create"
    assert IntentType.DELETE.value == "delete"
    assert IntentType.EXECUTE_TASK.value == "execute_task"


def test_intent_with_missing_fields():
    """Test intent with missing fields."""
    intent = Intent(
        type=IntentType.CREATE,
        confidence=0.9,
        entities={},
        missing_fields=["target", "name"],
    )
    assert len(intent.missing_fields) == 2
    assert intent.missing_fields[0] == "target"

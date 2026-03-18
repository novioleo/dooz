"""Tests for clarification questions."""

import pytest
from dooz_cli.clarification.questions import QuestionGenerator, IntentType


def test_ask_target_for_create():
    """Test asking target for create intent."""
    generator = QuestionGenerator()
    
    question = generator.generate_question(
        IntentType.CREATE,
        missing_field="target",
    )
    
    assert "创建" in question or "什么" in question


def test_ask_name_for_create():
    """Test asking name for create intent."""
    generator = QuestionGenerator()
    
    question = generator.generate_question(
        IntentType.CREATE,
        missing_field="name",
    )
    
    assert "名称" in question or "什么" in question


def test_ask_target_for_delete():
    """Test asking target for delete intent."""
    generator = QuestionGenerator()
    
    question = generator.generate_question(
        IntentType.DELETE,
        missing_field="target",
    )
    
    assert "删除" in question or "什么" in question


def test_ask_value_for_set():
    """Test asking value for set_value intent."""
    generator = QuestionGenerator()
    
    question = generator.generate_question(
        IntentType.SET_VALUE,
        missing_field="value",
    )
    
    assert "值" in question or "什么" in question


def test_ask_recipient_for_send_message():
    """Test asking recipient for send_message intent."""
    generator = QuestionGenerator()
    
    question = generator.generate_question(
        IntentType.SEND_MESSAGE,
        missing_field="recipient",
    )
    
    assert "给" in question or "谁" in question


def test_no_question_when_complete():
    """Test no question when missing_field is None."""
    generator = QuestionGenerator()
    
    question = generator.generate_question(
        IntentType.CREATE,
        missing_field=None,
    )
    
    assert question is None


def test_generate_confirmation_create():
    """Test confirmation for create."""
    generator = QuestionGenerator()
    
    confirmation = generator.generate_confirmation(
        IntentType.CREATE,
        {"target": "task", "name": "测试任务"},
    )
    
    assert "创建" in confirmation
    assert "测试任务" in confirmation


def test_generate_confirmation_delete():
    """Test confirmation for delete."""
    generator = QuestionGenerator()
    
    confirmation = generator.generate_confirmation(
        IntentType.DELETE,
        {"target": "用户", "name": "张三"},
    )
    
    assert "删除" in confirmation or "删除" in confirmation


def test_generate_confirmation_enable():
    """Test confirmation for enable."""
    generator = QuestionGenerator()
    
    confirmation = generator.generate_confirmation(
        IntentType.ENABLE,
        {"target": "服务"},
    )
    
    assert "启用" in confirmation or "开启" in confirmation


def test_generate_confirmation_with_scope_all():
    """Test confirmation with scope=all."""
    generator = QuestionGenerator()
    
    confirmation = generator.generate_confirmation(
        IntentType.DELETE,
        {"target": "用户", "scope": "all"},
    )
    
    assert "全部" in confirmation

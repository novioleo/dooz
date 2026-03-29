"""Tests for MessageList widget."""

import pytest
from textual.widgets import Static

from dooz_cli.tui.models import Message, MessageType


def test_message_list_initialization():
    """Test MessageList initializes empty."""
    from dooz_cli.tui.widgets.message_list import MessageList
    
    ml = MessageList()
    assert len(ml.messages) == 0


def test_message_list_add_user_message():
    """Test adding a user message."""
    from dooz_cli.tui.widgets.message_list import MessageList
    
    ml = MessageList()
    msg = Message(content="Hello", author="user", message_type=MessageType.USER)
    ml.add_message(msg)
    assert len(ml.messages) == 1
    assert ml.messages[0].content == "Hello"


def test_message_list_add_daemon_message():
    """Test adding a daemon message."""
    from dooz_cli.tui.widgets.message_list import MessageList
    
    ml = MessageList()
    msg = Message(content="Response", author="dooz", message_type=MessageType.DAEMON)
    ml.add_message(msg)
    assert len(ml.messages) == 1
    assert ml.messages[0].author == "dooz"


def test_message_list_clear():
    """Test clearing messages."""
    from dooz_cli.tui.widgets.message_list import MessageList
    
    ml = MessageList()
    msg = Message(content="Test", author="user")
    ml.add_message(msg)
    ml.clear()
    assert len(ml.messages) == 0


def test_message_list_is_static():
    """Test MessageList inherits from Static."""
    from dooz_cli.tui.widgets.message_list import MessageList
    
    ml = MessageList()
    assert isinstance(ml, Static)

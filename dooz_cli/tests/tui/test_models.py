"""Tests for TUI message models."""

from dooz_cli.tui.models import Message, MessageType


def test_message_creation():
    """Test creating a basic message."""
    msg = Message(content="Hello", author="user")
    assert msg.content == "Hello"
    assert msg.author == "user"
    assert msg.message_type == MessageType.USER


def test_message_from_daemon():
    """Test creating a message from daemon response."""
    msg = Message(content="Response text", author="dooz", message_type=MessageType.DAEMON)
    assert msg.author == "dooz"
    assert msg.message_type == MessageType.DAEMON


def test_message_timestamp():
    """Test that timestamp is set automatically."""
    import time
    before = time.time()
    msg = Message(content="Test", author="user")
    after = time.time()
    assert before <= msg.timestamp <= after


def test_message_str():
    """Test string representation."""
    msg = Message(content="Hi", author="user", message_type=MessageType.USER)
    assert "Hi" in str(msg)
    assert "user" in str(msg)

"""Tests for ChatBubble widget."""

from dooz_cli.tui.models import Message, MessageType


def test_chat_bubble_user_message():
    """Test ChatBubble renders user message correctly."""
    from textual.widgets import Static
    from dooz_cli.tui.widgets.chat_bubble import ChatBubble
    
    msg = Message(content="Hello", author="user", message_type=MessageType.USER)
    bubble = ChatBubble(msg)
    assert bubble.message == msg


def test_chat_bubble_daemon_message():
    """Test ChatBubble renders daemon message correctly."""
    from dooz_cli.tui.widgets.chat_bubble import ChatBubble
    
    msg = Message(content="Hi there!", author="dooz", message_type=MessageType.DAEMON)
    bubble = ChatBubble(msg)
    assert bubble.message.author == "dooz"


def test_chat_bubble_is_static():
    """Test ChatBubble inherits from Static."""
    from textual.widgets import Static
    from dooz_cli.tui.widgets.chat_bubble import ChatBubble
    
    msg = Message(content="Test", author="user")
    bubble = ChatBubble(msg)
    assert isinstance(bubble, Static)

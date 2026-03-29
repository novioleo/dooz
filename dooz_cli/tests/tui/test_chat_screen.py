"""Tests for ChatScreen."""

from dooz_cli.tui.models import Message, MessageType
from dooz_cli.tui.screens.chat_screen import ChatScreen, MessageSubmitted


def test_chat_screen_initialization():
    """Test ChatScreen initializes correctly."""
    screen = ChatScreen()
    assert screen._input_area is not None
    assert screen._message_list is not None


def test_chat_screen_has_message_list_and_input():
    """Test ChatScreen has required widgets."""
    screen = ChatScreen()
    assert hasattr(screen, '_input_area')
    assert hasattr(screen, '_message_list')
    assert hasattr(screen, 'add_daemon_message')
    assert hasattr(screen, 'add_error_message')
    assert hasattr(screen, 'add_system_message')


def test_message_submitted_class():
    """Test MessageSubmitted event class exists."""
    assert issubclass(MessageSubmitted, Message)

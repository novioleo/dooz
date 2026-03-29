"""Tests for DoozTUI application."""

from dooz_cli.tui.app import DoozTUI


def test_tui_initialization():
    """Test TUI initializes correctly."""
    app = DoozTUI()
    assert app is not None


def test_tui_has_chat_screen():
    """Test TUI has chat screen."""
    app = DoozTUI()
    # The app should have ChatScreen as default screen

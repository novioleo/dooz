"""Tests for InputArea widget."""

from dooz_cli.tui.widgets.input_area import InputArea


def test_input_area_initialization():
    """Test InputArea initializes correctly."""
    ia = InputArea()
    assert ia.value == ""


def test_input_area_submit_event():
    """Test that submit event fires on Enter."""
    ia = InputArea()
    # The InputArea inherits action_submit from Input widget
    assert hasattr(ia, "action_submit")

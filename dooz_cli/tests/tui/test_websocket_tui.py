"""Tests for WebSocket TUI integration."""

import asyncio

from dooz_cli.tui.websocket_tui import WebSocketTUI


def test_websocket_tui_initialization():
    """Test WebSocketTUI initializes correctly."""
    tui = WebSocketTUI()
    assert tui is not None


def test_websocket_tui_has_websocket_client():
    """Test WebSocketTUI has client attribute."""
    tui = WebSocketTUI()
    assert hasattr(tui, 'client')

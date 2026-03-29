"""Dooz TUI Application."""

import asyncio
from typing import Optional

from textual.app import App, ComposeResult
from textual.driver import Driver
from textual.geometry import Size

from dooz_cli.tui.models import Message, MessageType
from dooz_cli.tui.screens.chat_screen import ChatScreen, MessageSubmitted


class DoozTUI(App):
    """Main TUI application for dooz CLI."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        background: $primary;
        color: $text;
    }
    
    Footer {
        background: $primary-darken-1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chat_screen: Optional[ChatScreen] = None
    
    def on_mount(self) -> None:
        """Handle app mount."""
        self._chat_screen = self.screen  # type: ignore
    
    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield ChatScreen()
    
    def get_chat_screen(self) -> ChatScreen:
        """Get the chat screen instance."""
        if self._chat_screen is None:
            self._chat_screen = self.screen  # type: ignore
        return self._chat_screen
    
    async def handle_message_submitted(self, event: MessageSubmitted) -> None:
        """Handle message submitted event from chat screen."""
        # Override in subclass or set callback to handle message sending
        pass

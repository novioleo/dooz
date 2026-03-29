"""Main chat screen for the TUI."""

from textual.app import ComposeResult
from textual.widgets import Input
from textual.screen import Screen
from textual.widgets import Header, Footer

from dooz_cli.tui.models import Message, MessageType
from dooz_cli.tui.widgets import ChatBubble
from dooz_cli.tui.widgets.input_area import InputArea
from dooz_cli.tui.widgets.message_list import MessageList


class ChatScreen(Screen):
    """Main chat interface screen."""
    
    CSS = """
    ChatScreen {
        layout: vertical;
    }
    
    #message-area {
        height: 1fr;
        background: $surface;
    }
    
    InputArea {
        dock: bottom;
        width: 100%;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._message_list = MessageList(id="message-area")
        self._input_area = InputArea(placeholder="Type a message...")
    
    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header()
        yield self._message_list
        yield self._input_area
        yield Footer()
    
    def on_input_area_submit(self, event: Input.Submitted) -> None:
        """Handle message submission."""
        content = self._input_area.value.strip()
        if content:
            # Add user message
            user_msg = Message(content=content, author="user", message_type=MessageType.USER)
            self._message_list.add_message(user_msg)
            self._input_area.value = ""
            
            # Emit event for external handling (e.g., send to daemon)
            self.post_message(MessageSubmitted(user_msg))
    
    def add_daemon_message(self, content: str) -> None:
        """Add a message from the daemon."""
        daemon_msg = Message(content=content, author="dooz", message_type=MessageType.DAEMON)
        self._message_list.add_message(daemon_msg)
    
    def add_error_message(self, content: str) -> None:
        """Add an error message."""
        error_msg = Message(content=content, author="system", message_type=MessageType.ERROR)
        self._message_list.add_message(error_msg)
    
    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        sys_msg = Message(content=content, author="system", message_type=MessageType.SYSTEM)
        self._message_list.add_message(sys_msg)


class MessageSubmitted(Message):
    """Event message for when user submits a message."""
    pass

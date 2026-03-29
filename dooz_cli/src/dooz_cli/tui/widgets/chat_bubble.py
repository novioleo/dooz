"""Chat bubble widget for TUI."""

from textual.widgets import Static

from dooz_cli.tui.models import Message, MessageType


class ChatBubble(Static):
    """A chat bubble widget displaying a message."""
    
    def __init__(self, message: Message, **kwargs):
        super().__init__(**kwargs)
        self.message = message
    
    def on_mount(self) -> None:
        """Set up the bubble appearance on mount."""
        self._update_style()
        self._update_content()
    
    def _update_style(self) -> None:
        """Update the bubble style based on message type."""
        if self.message.message_type == MessageType.USER:
            self.styles.background = "#00008b"
            self.styles.color = "white"
            self.styles.align = ("right", "top")
            self.styles.padding = (1, 2)
            self.styles.width = "70%"
            self.styles.margin = (1, 1, 1, 20)
        elif self.message.message_type == MessageType.DAEMON:
            self.styles.background = "#006400"
            self.styles.color = "white"
            self.styles.align = ("left", "top")
            self.styles.padding = (1, 2)
            self.styles.width = "70%"
            self.styles.margin = (1, 20, 1, 1)
        elif self.message.message_type == MessageType.ERROR:
            self.styles.background = "#8b0000"
            self.styles.color = "white"
            self.styles.align = ("left", "top")
            self.styles.padding = (1, 2)
            self.styles.width = "70%"
            self.styles.margin = (1, 20, 1, 1)
        else:
            self.styles.background = "#404040"
            self.styles.color = "white"
            self.styles.align = ("center", "top")
            self.styles.padding = (1, 2)
            self.styles.width = "70%"
            self.styles.margin = (1, 20, 1, 1)
    
    def _update_content(self) -> None:
        """Update the displayed content."""
        prefix = f"[{self.message.author}]: " if self.message.author != "system" else ""
        self.update(f"{prefix}{self.message.content}")

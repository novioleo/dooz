"""Input area widget for the TUI chat interface."""

from textual.widgets import Input


class InputArea(Input):
    """Input widget for typing chat messages."""
    
    def __init__(self, placeholder: str = "Type a message...", **kwargs):
        super().__init__(placeholder=placeholder, **kwargs)
    
    def on_mount(self) -> None:
        """Set up the input area."""
        self.styles.height = 3
        self.styles.margin = 1

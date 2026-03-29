"""Input area widget for the TUI chat interface."""

from textual.widgets import Input


class InputArea(Input):
    """Input widget for typing chat messages."""
    
    def __init__(self, placeholder: str = "Type a message or /new, /exit...", **kwargs):
        super().__init__(placeholder=placeholder, **kwargs)
    
    def on_mount(self) -> None:
        """Set up the input area."""
        self.styles.height = 3
        self.styles.margin = 1
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        content = self.value.strip()
        if not content:
            return
        
        # Check for commands
        if content == "/exit":
            self.post_message(ExitCommand())
            self.value = ""
            return
        
        if content == "/new":
            self.post_message(NewConversationCommand())
            self.value = ""
            return
        
        # Regular message - emit for parent to handle
        self.post_message(InputSubmitted(self, content))
        self.value = ""


class ExitCommand:
    """Command to exit the application."""
    pass


class NewConversationCommand:
    """Command to create a new conversation."""
    pass


class InputSubmitted:
    """Event when user submits a message."""
    def __init__(self, input_widget: InputArea, content: str):
        self.input = input_widget
        self.content = content

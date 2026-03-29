"""Message list widget for displaying chat history."""

from typing import List

from textual.widgets import Static

from dooz_cli.tui.models import Message
from dooz_cli.tui.widgets.chat_bubble import ChatBubble


class MessageList(Static):
    """Widget to display a list of messages as chat bubbles."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages: List[Message] = []
        self._bubbleWidgets: List[ChatBubble] = []
    
    def add_message(self, message: Message) -> None:
        """Add a message to the list."""
        self.messages.append(message)
        bubble = ChatBubble(message)
        self._bubbleWidgets.append(bubble)
        if self.is_attached:
            self.mount(bubble)
            self.scroll_end()
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        for widget in self._bubbleWidgets:
            if widget.is_attached:
                widget.remove()
        self._bubbleWidgets.clear()
    
    def on_mount(self) -> None:
        """Set up the message list container."""
        self.styles.layout = "vertical"

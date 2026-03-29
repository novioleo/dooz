"""Conversation list widget for TUI sidebar."""

from typing import List

from textual.widgets import Static

from dooz_cli.tui.models import Conversation


class ConversationItem(Static):
    """A single conversation item in the list."""
    
    def __init__(self, conversation: Conversation, **kwargs):
        super().__init__(**kwargs)
        self.conversation = conversation
    
    def on_mount(self) -> None:
        """Set up the item appearance."""
        self.styles.padding = (1, 1)
        self.styles.width = "100%"
        self.styles.height = "auto"
        self._update_content()
    
    def _update_content(self) -> None:
        """Update displayed content."""
        time_str = self.conversation.updated_time_str
        title = self.conversation.title[:20] + "..." if len(self.conversation.title) > 20 else self.conversation.title
        self.update(f"{title}\n{time_str}")


class ConversationList(Static):
    """Widget to display list of conversations."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conversations: List[Conversation] = []
        self._items: List[ConversationItem] = []
        self.selected_id: str | None = None
    
    def add_conversation(self, conversation: Conversation) -> None:
        """Add a conversation to the list."""
        self.conversations.append(conversation)
        item = ConversationItem(conversation)
        self._items.append(item)
        if self.is_attached:
            self.mount(item)
    
    def select_conversation(self, conversation_id: str) -> None:
        """Select a conversation by ID."""
        self.selected_id = conversation_id
        # Update visual selection
        for item, conv in zip(self._items, self.conversations):
            if conv.id == conversation_id:
                item.styles.background = "#404040"
            else:
                item.styles.background = "transparent"
    
    def clear(self) -> None:
        """Clear all conversations."""
        self.conversations.clear()
        for item in self._items:
            if item.is_attached:
                item.remove()
        self._items.clear()
        self.selected_id = None
    
    def on_mount(self) -> None:
        """Set up the list container."""
        self.styles.layout = "vertical"
        self.styles.padding = 0
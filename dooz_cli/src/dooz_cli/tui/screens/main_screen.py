"""Main screen for TUI with 20/80 split layout."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Header

from dooz_cli.tui.models import Conversation, Message, MessageType
from dooz_cli.tui.widgets import ChatBubble, ConversationList, InputArea, MessageList
from dooz_cli.tui.widgets.input_area import ExitCommand, InputSubmitted, NewConversationCommand


class MainScreen(Screen):
    """Main screen with sidebar and chat layout.
    
    Layout:
    - Left (20%): Conversation list with border
    - Right (80%): Vertical split
      - Top (80%): Chat history with border
      - Bottom (20%): Input area with border
    """
    
    CSS = """
    MainScreen {
        layout: horizontal;
    }
    
    #sidebar {
        width: 20%;
        height: 100%;
        border: solid green;
        dock: left;
    }
    
    #right-panel {
        width: 80%;
        height: 100%;
        layout: vertical;
        border: solid green;
    }
    
    #chat-area {
        height: 1fr;
        border: solid blue;
        background: $surface;
    }
    
    #input-area {
        height: 20%;
        border: solid yellow;
        background: $surface;
    }
    
    Header {
        background: $primary;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._conversation_list = ConversationList(id="sidebar")
        self._message_list = MessageList(id="chat-area")
        self._input_area = InputArea(placeholder="Type a message or /new, /exit...")
        self._current_conversation_id: str | None = None
    
    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        yield Header()
        yield Container(
            self._message_list,
            self._input_area,
            id="right-panel"
        )
        yield self._conversation_list
    
    def on_mount(self) -> None:
        """Handle screen mount."""
        self._create_new_conversation()
    
    def _create_new_conversation(self) -> None:
        """Create a new conversation."""
        import uuid
        conversation = Conversation(
            id=str(uuid.uuid4())[:8],
            title="New Chat"
        )
        self._conversation_list.add_conversation(conversation)
        self._conversation_list.select_conversation(conversation.id)
        self._current_conversation_id = conversation.id
    
    def on_input_area_submitted(self, event: InputSubmitted) -> None:
        """Handle message submission from input area."""
        content = event.content
        
        # Add user message
        user_msg = Message(content=content, author="user", message_type=MessageType.USER)
        self._message_list.add_message(user_msg)
        
        # Emit event for external handling
        self.post_message(ChatMessageSubmitted(user_msg))
    
    def on_exit_command(self, event: ExitCommand) -> None:
        """Handle exit command."""
        self.post_message(AppExitRequested())
    
    def on_new_conversation_command(self, event: NewConversationCommand) -> None:
        """Handle new conversation command."""
        self._message_list.clear()
        self._create_new_conversation()
        self.post_message(ConversationChanged(self._current_conversation_id))
    
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


class ChatMessageSubmitted(Message):
    """Event when user sends a chat message."""
    pass


class AppExitRequested:
    """Event when app should exit."""
    pass


class ConversationChanged:
    """Event when conversation changes."""
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id

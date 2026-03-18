"""Clarification agent state management."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IntentType(str, Enum):
    """Generic intent types - applicable to various domains."""
    
    # Information retrieval
    GET_INFO = "get_info"
    LIST_ITEMS = "list_items"
    GET_STATUS = "get_status"
    
    # CRUD operations
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    
    # Task execution
    EXECUTE_TASK = "execute_task"
    STOP_TASK = "stop_task"
    
    # Control
    ENABLE = "enable"
    DISABLE = "disable"
    SET_VALUE = "set_value"
    
    # Communication
    SEND_MESSAGE = "send_message"
    READ_MESSAGE = "read_message"
    
    # File operations
    DOWNLOAD = "download"
    UPLOAD = "upload"
    
    # Help
    HELP = "help"
    
    # Fallback
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Detected user intent."""
    type: IntentType
    confidence: float
    entities: dict[str, str] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)


@dataclass
class ConversationTurn:
    """A single conversation turn."""
    speaker: str  # "user" or "agent"
    text: str
    timestamp: float


class ClarificationState:
    """Manages clarification conversation state."""
    
    MAX_TURNS = 3
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns: list[ConversationTurn] = []
        self.intent: Optional[Intent] = None
        self.is_complete = False
        self.needs_clarification = False
    
    @property
    def turn_count(self) -> int:
        return len([t for t in self.turns if t.speaker == "user"])
    
    @property
    def last_user_input(self) -> Optional[str]:
        for turn in reversed(self.turns):
            if turn.speaker == "user":
                return turn.text
        return None
    
    def add_turn(self, speaker: str, text: str):
        """Add a conversation turn."""
        import time
        turn = ConversationTurn(speaker=speaker, text=text, timestamp=time.time())
        self.turns.append(turn)
    
    def set_intent(self, intent: Intent):
        """Set the detected intent."""
        self.intent = intent
        if intent.missing_fields:
            self.needs_clarification = True
        else:
            self.is_complete = True
    
    def complete(self):
        """Mark conversation as complete."""
        self.is_complete = True
        self.needs_clarification = False

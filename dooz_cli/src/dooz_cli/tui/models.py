"""Message models for TUI chat interface."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MessageType(Enum):
    """Message type enumeration."""
    
    USER = "user"
    DAEMON = "daemon"
    SYSTEM = "system"
    ERROR = "error"


@dataclass
class Message:
    """Chat message model."""
    
    content: str
    author: str
    message_type: MessageType = MessageType.USER
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    id: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation."""
        return f"[{self.author}] {self.content}"

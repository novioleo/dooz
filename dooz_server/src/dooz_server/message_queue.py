# dooz_server/src/dooz_server/message_queue.py
import uuid
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class StoredMessage:
    """Represents a stored message with metadata."""
    message_id: str
    from_client_id: str
    to_client_id: str
    content: str
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_read: bool = False


class MessageQueue:
    """Queue for storing undelivered messages with TTL support."""
    
    def __init__(self, default_ttl_seconds: int = 3600):  # Default 1 hour
        self.default_ttl_seconds = default_ttl_seconds
        self._messages: Dict[str, StoredMessage] = {}
        self._client_messages: Dict[str, List[str]] = {}  # client_id -> [message_ids]
    
    def store_message(
        self, 
        from_client_id: str, 
        to_client_id: str, 
        content: str,
        ttl_seconds: Optional[int] = None
    ) -> str:
        """Store a message for later delivery."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        
        message_id = str(uuid.uuid4())
        message = StoredMessage(
            message_id=message_id,
            from_client_id=from_client_id,
            to_client_id=to_client_id,
            content=content,
            expires_at=time.time() + ttl if ttl > 0 else None
        )
        
        self._messages[message_id] = message
        
        if to_client_id not in self._client_messages:
            self._client_messages[to_client_id] = []
        self._client_messages[to_client_id].append(message_id)
        
        return message_id
    
    def get_pending_messages(self, client_id: str) -> List[StoredMessage]:
        """Get all unread, unexpired messages for a client."""
        if client_id not in self._client_messages:
            return []
        
        current_time = time.time()
        pending = []
        
        for msg_id in self._client_messages[client_id]:
            msg = self._messages.get(msg_id)
            if msg and not msg.is_read:
                # Check expiration
                if msg.expires_at and msg.expires_at < current_time:
                    # Message expired - remove it
                    self._remove_message(msg_id, client_id)
                    continue
                pending.append(msg)
        
        return pending
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        if message_id in self._messages:
            self._messages[message_id].is_read = True
            return True
        return False
    
    def get_message(self, message_id: str) -> Optional[StoredMessage]:
        """Get a specific message by ID."""
        return self._messages.get(message_id)
    
    def _remove_message(self, message_id: str, client_id: str) -> None:
        """Remove a message from storage."""
        if message_id in self._messages:
            del self._messages[message_id]
        if client_id in self._client_messages and message_id in self._client_messages[client_id]:
            self._client_messages[client_id].remove(message_id)
    
    def cleanup_expired(self) -> int:
        """Remove all expired messages. Returns count of removed messages."""
        current_time = time.time()
        expired_ids = [
            msg_id for msg_id, msg in self._messages.items()
            if msg.expires_at and msg.expires_at < current_time
        ]
        
        for msg_id in expired_ids:
            msg = self._messages[msg_id]
            self._remove_message(msg_id, msg.to_client_id)
        
        return len(expired_ids)
    
    def get_expired_messages(self) -> List[StoredMessage]:
        """Get list of expired messages (for notifying sender)."""
        current_time = time.time()
        return [
            msg for msg in self._messages.values()
            if msg.expires_at and msg.expires_at < current_time and not msg.is_read
        ]

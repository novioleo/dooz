"""Conversation history management."""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger("dooz_server.agent.conversation")


class ConversationManager:
    """Manages conversation history for each user."""
    
    def __init__(self, max_history: int = 10):
        """Initialize conversation manager."""
        self.max_history = max_history
        self._conversations: dict[str, list[dict]] = defaultdict(list)
    
    def add_message(self, user_id: str, role: str, content: str):
        """Add a message to user's conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self._conversations[user_id].append(message)
        
        # Trim if exceeds max
        if len(self._conversations[user_id]) > self.max_history:
            self._conversations[user_id] = self._conversations[user_id][-self.max_history:]
        
        logger.debug(f"Added {role} message to {user_id}, total: {len(self._conversations[user_id])}")
    
    def get_history(self, user_id: str) -> list[dict]:
        """Get conversation history for a user."""
        return self._conversations.get(user_id, [])
    
    def get_history_as_text(self, user_id: str) -> str:
        """Get conversation history formatted as text for LLM context."""
        history = self.get_history(user_id)
        if not history:
            return "No previous conversation."
        
        lines = ["Conversation history:"]
        for msg in history:
            role = msg["role"].capitalize()
            lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(lines)
    
    def clear_history(self, user_id: str):
        """Clear conversation history for a user."""
        if user_id in self._conversations:
            del self._conversations[user_id]
            logger.debug(f"Cleared conversation history for {user_id}")
    
    def get_history_count(self, user_id: str) -> int:
        """Get number of messages in conversation."""
        return len(self._conversations.get(user_id, []))

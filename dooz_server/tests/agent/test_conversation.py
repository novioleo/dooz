import pytest
from datetime import datetime


class TestConversationManager:
    """Tests for ConversationManager."""
    
    def test_add_message(self):
        """Test adding a message to conversation."""
        from dooz_server.agent.conversation import ConversationManager
        
        manager = ConversationManager(max_history=10)
        manager.add_message("user-1", "user", "Hello")
        manager.add_message("user-1", "assistant", "Hi there")
        
        history = manager.get_history("user-1")
        assert len(history) == 2
        assert history[0]["role"] == "user"
    
    def test_max_history_limit(self):
        """Test older messages are removed when limit reached."""
        from dooz_server.agent.conversation import ConversationManager
        
        manager = ConversationManager(max_history=2)
        manager.add_message("user-1", "user", "Message 1")
        manager.add_message("user-1", "user", "Message 2")
        manager.add_message("user-1", "user", "Message 3")
        
        history = manager.get_history("user-1")
        assert len(history) == 2
        assert "Message 2" in str(history)
    
    def test_separate_conversations(self):
        """Test different users have separate histories."""
        from dooz_server.agent.conversation import ConversationManager
        
        manager = ConversationManager(max_history=10)
        manager.add_message("user-1", "user", "Hello")
        manager.add_message("user-2", "user", "Hi")
        
        assert len(manager.get_history("user-1")) == 1
        assert len(manager.get_history("user-2")) == 1
    
    def test_clear_conversation(self):
        """Test clearing conversation history."""
        from dooz_server.agent.conversation import ConversationManager
        
        manager = ConversationManager(max_history=10)
        manager.add_message("user-1", "user", "Hello")
        manager.clear_history("user-1")
        
        assert len(manager.get_history("user-1")) == 0

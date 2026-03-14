# tests/test_message_queue.py
import pytest
import asyncio
import time
from dooz_server.message_queue import MessageQueue, StoredMessage


def test_store_message():
    queue = MessageQueue()
    msg_id = queue.store_message("from-1", "to-2", "Hello!")
    assert msg_id is not None


def test_get_pending_messages():
    queue = MessageQueue()
    queue.store_message("from-1", "to-2", "Hello!")
    messages = queue.get_pending_messages("to-2")
    assert len(messages) == 1
    assert messages[0].content == "Hello!"


def test_mark_as_read():
    queue = MessageQueue()
    msg_id = queue.store_message("from-1", "to-2", "Hello!")
    queue.mark_as_read(msg_id)
    messages = queue.get_pending_messages("to-2")
    assert len(messages) == 0


def test_message_expiration():
    """Test that expired messages are cleaned up."""
    queue = MessageQueue(default_ttl_seconds=1)
    queue.store_message("from-1", "to-2", "Hello!")
    
    # Wait for expiration
    time.sleep(1.5)
    
    # Trigger cleanup
    queue.cleanup_expired()
    
    messages = queue.get_pending_messages("to-2")
    assert len(messages) == 0


def test_get_expired_messages():
    """Test that expired messages are returned for notification."""
    queue = MessageQueue(default_ttl_seconds=1)
    queue.store_message("from-1", "to-2", "Hello!")
    
    time.sleep(1.5)
    
    expired = queue.get_expired_messages()
    assert len(expired) == 1
    assert expired[0].content == "Hello!"


def test_no_messages_for_client():
    queue = MessageQueue()
    messages = queue.get_pending_messages("nonexistent")
    assert len(messages) == 0


def test_get_message():
    queue = MessageQueue()
    msg_id = queue.store_message("from-1", "to-2", "Hello!")
    msg = queue.get_message(msg_id)
    assert msg is not None
    assert msg.content == "Hello!"


def test_custom_ttl():
    """Test message with custom TTL."""
    queue = MessageQueue(default_ttl_seconds=3600)
    msg_id = queue.store_message("from-1", "to-2", "Hello!", ttl_seconds=1)
    
    time.sleep(1.5)
    
    messages = queue.get_pending_messages("to-2")
    assert len(messages) == 0


def test_ttl_zero_no_expiry():
    """Test that TTL=0 means no expiration."""
    queue = MessageQueue(default_ttl_seconds=1)
    queue.store_message("from-1", "to-2", "Hello!", ttl_seconds=0)
    
    time.sleep(1.5)
    
    messages = queue.get_pending_messages("to-2")
    assert len(messages) == 1

import pytest
from unittest.mock import Mock, MagicMock
from core.transport import TransportService


def test_transport_service_init():
    """Test TransportService initialization"""
    participant = Mock()
    device_id = "device-001"
    
    service = TransportService(participant, device_id)
    
    assert service.participant == participant
    assert service.device_id == device_id
    assert service.publishers == {}
    assert service.subscribers == {}
    assert service._callbacks == {}


def test_create_publisher():
    """Test creating a publisher"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    service.create_publisher("test/topic")
    
    assert "test/topic" in service.publishers
    assert service.publishers["test/topic"] is True


def test_create_subscriber():
    """Test creating a subscriber with callback"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    callback = Mock()
    service.create_subscriber("test/topic", callback)
    
    assert "test/topic" in service.subscribers
    assert callback in service.subscribers["test/topic"]
    assert callback in service._callbacks["test/topic"]


def test_create_subscriber_multiple_callbacks():
    """Test adding multiple callbacks to the same topic"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    callback1 = Mock()
    callback2 = Mock()
    
    service.create_subscriber("test/topic", callback1)
    service.create_subscriber("test/topic", callback2)
    
    assert len(service.subscribers["test/topic"]) == 2
    assert callback1 in service.subscribers["test/topic"]
    assert callback2 in service.subscribers["test/topic"]
    assert len(service._callbacks["test/topic"]) == 2


def test_publish_message():
    """Test publishing a message"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    service.create_publisher("test/topic")
    service.publish("test/topic", {"data": "test"})


def test_on_message_received_triggers_callback():
    """Test that receiving a message triggers the callback"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    callback = Mock()
    service.create_subscriber("test/topic", callback)
    
    message = {"data": "test message"}
    service.on_message_received("test/topic", message)
    
    callback.assert_called_once_with(message)


def test_on_message_received_multiple_callbacks():
    """Test that multiple callbacks are all triggered"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    callback1 = Mock()
    callback2 = Mock()
    
    service.create_subscriber("test/topic", callback1)
    service.create_subscriber("test/topic", callback2)
    
    message = {"data": "test"}
    service.on_message_received("test/topic", message)
    
    callback1.assert_called_once_with(message)
    callback2.assert_called_once_with(message)


def test_on_message_received_no_callbacks():
    """Test that no error occurs when no callback is registered"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    # Should not raise any exception
    service.on_message_received("nonexistent/topic", {"data": "test"})


def test_on_message_received_callback_error():
    """Test that callback errors are caught and logged"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    callback = Mock(side_effect=Exception("Callback error"))
    service.create_subscriber("test/topic", callback)
    
    # Should not raise exception - errors should be caught
    service.on_message_received("test/topic", {"data": "test"})
    
    callback.assert_called_once()


def test_get_subscribed_topics():
    """Test getting list of subscribed topics"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    service.create_subscriber("topic1", Mock())
    service.create_subscriber("topic2", Mock())
    service.create_subscriber("topic3", Mock())
    
    topics = service.get_subscribed_topics()
    
    assert "topic1" in topics
    assert "topic2" in topics
    assert "topic3" in topics
    assert len(topics) == 3


def test_get_subscribed_topics_empty():
    """Test getting subscribed topics when nothing is subscribed"""
    participant = Mock()
    service = TransportService(participant, "device-001")
    
    topics = service.get_subscribed_topics()
    
    assert topics == []

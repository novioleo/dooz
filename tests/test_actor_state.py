import pytest
from core.actor_state import ActorStateManager
from core.types import ActorState


def test_actor_state_init():
    """Test ActorStateManager initialization"""
    manager = ActorStateManager("device-001")
    
    assert manager.device_id == "device-001"
    assert isinstance(manager.state, ActorState)
    assert manager.state.device_id == "device-001"
    assert manager.state.history == []
    assert manager.state.current is None
    assert manager.state.next_ops == []


def test_update_on_receive():
    """Test updating state when receiving an operation"""
    manager = ActorStateManager("device-001")
    
    manager.update_on_receive("turn_on")
    
    assert manager.state.current == "turn_on"
    assert manager.state.history == []


def test_update_on_complete():
    """Test updating state when operation completes"""
    manager = ActorStateManager("device-001")
    
    manager.update_on_receive("turn_on")
    manager.update_on_complete(success=True)
    
    assert manager.state.current is None
    assert "turn_on" in manager.state.history
    assert manager.state.history == ["turn_on"]


def test_multiple_operations():
    """Test multiple operations in sequence"""
    manager = ActorStateManager("device-001")
    
    # First operation
    manager.update_on_receive("turn_on")
    manager.update_on_complete(success=True)
    
    # Second operation
    manager.update_on_receive("move_forward")
    manager.update_on_complete(success=True)
    
    # Third operation - failed
    manager.update_on_receive("turn_off")
    manager.update_on_complete(success=False)
    
    # Verify history contains all completed operations (regardless of success)
    assert manager.state.history == ["turn_on", "move_forward", "turn_off"]
    assert manager.state.current is None
    
    # Test get_history returns a copy
    history = manager.get_history()
    assert history == ["turn_on", "move_forward", "turn_off"]
    assert history is not manager.state.history  # Should be a copy
    
    # Test get_current
    assert manager.get_current() is None
    
    # Test set_next_ops
    manager.set_next_ops(["turn_on", "turn_off", "move"])
    assert manager.state.next_ops == ["turn_on", "turn_off", "move"]
    
    # Test get_state
    state = manager.get_state()
    assert state.device_id == "device-001"
    assert state.history == ["turn_on", "move_forward", "turn_off"]

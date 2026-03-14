import pytest
from core.types import (
    DeviceAnnounce, DeviceInfo, BrainStatus, TaskRequest,
    TaskResponse, TaskDispatch, TaskNotify, ActorState
)

def test_device_announce_creation():
    info = DeviceInfo(
        device_id="test_001",
        name="Test Device",
        role="test",
        wisdom=50,
        output=True,
        skills=["skill1", "skill2"]
    )
    announce = DeviceAnnounce(device=info)
    assert announce.device.device_id == "test_001"
    assert announce.device.wisdom == 50

def test_brain_status_no_brain():
    status = BrainStatus(brain_id=None, reason="no_candidate")
    assert status.brain_id is None
    assert status.reason == "no_candidate"

def test_actor_state_operations():
    state = ActorState(device_id="test_001")
    assert state.current is None
    assert state.history == []
    
    state.update_on_receive("test_op")
    assert state.current == "test_op"
    
    state.update_on_complete(True)
    assert state.current is None
    assert "test_op" in state.history

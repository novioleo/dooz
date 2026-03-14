import pytest
import time
from unittest.mock import Mock, MagicMock
from core.types import DeviceInfo, DeviceAnnounce, DeviceHeartbeat, DeviceOffline
from core.discovery import DiscoveryService


def create_test_device(device_id: str = "test_001", wisdom: int = 50) -> DeviceInfo:
    """Helper to create test device"""
    return DeviceInfo(
        device_id=device_id,
        name=f"Test Device {device_id}",
        role="worker",
        wisdom=wisdom,
        output=True,
        skills=["skill1"]
    )


class TestDiscoveryServiceInit:
    """Test DiscoveryService initialization"""
    
    def test_init_sets_device_info(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        assert service.device_info == device
        assert service.participant == participant
        
    def test_init_defaults(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        assert service.online_devices == {}
        assert service.last_heartbeat == {}
        assert service._running is False
        
    def test_heartbeat_constants(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        assert service.HEARTBEAT_INTERVAL == 3
        assert service.HEARTBEAT_TIMEOUT == 10


class TestDiscoveryServiceStartStop:
    """Test DiscoveryService start/stop methods"""
    
    def test_start_sets_running_true(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        service.start()
        
        assert service._running is True
        
    def test_stop_sets_running_false(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        service.start()
        
        service.stop()
        
        assert service._running is False


class TestDiscoveryServiceAnnounce:
    """Test device announcement methods"""
    
    def test_announce_presence_adds_self_to_online(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        service.start()
        
        # When device announces presence, it should add itself to online_devices
        # (handled by on_device_announce when receiving own announce, 
        # or directly for self)
        assert device.device_id in service.online_devices
        
    def test_announce_offline_removes_from_online(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        # Simulate self being in online_devices
        service.online_devices[device.device_id] = device
        service.last_heartbeat[device.device_id] = time.time()
        
        service.stop()
        
        assert device.device_id not in service.online_devices


class TestDiscoveryServiceHeartbeat:
    """Test heartbeat methods"""
    
    def test_send_heartbeat_updates_last_heartbeat(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        service.send_heartbeat()
        
        assert device.device_id in service.last_heartbeat
        
    def test_on_heartbeat_from_other_updates_time(self):
        device = create_test_device()
        other_device = create_test_device("other_001", 30)
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        heartbeat = DeviceHeartbeat(device_id=other_device.device_id)
        service.on_heartbeat(heartbeat)
        
        assert other_device.device_id in service.last_heartbeat
        
    def test_on_heartbeat_ignores_self(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        heartbeat = DeviceHeartbeat(device_id=device.device_id)
        service.on_heartbeat(heartbeat)
        
        # Should not add self to last_heartbeat from on_heartbeat
        # (the service's own send_heartbeat handles that)
        assert device.device_id not in service.last_heartbeat


class TestDiscoveryServiceDeviceAnnounce:
    """Test device announce message handling"""
    
    def test_on_device_announce_adds_device(self):
        device = create_test_device()
        other_device = create_test_device("other_001", 30)
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        announce = DeviceAnnounce(device=other_device)
        service.on_device_announce(announce)
        
        assert other_device.device_id in service.online_devices
        
    def test_on_device_announce_ignores_self(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        announce = DeviceAnnounce(device=device)
        service.on_device_announce(announce)
        
        # Should not add self to online_devices
        assert device.device_id not in service.online_devices
        
    def test_on_device_announce_sets_heartbeat_time(self):
        device = create_test_device()
        other_device = create_test_device("other_001", 30)
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        announce = DeviceAnnounce(device=other_device)
        service.on_device_announce(announce)
        
        assert other_device.device_id in service.last_heartbeat


class TestDiscoveryServiceDeviceOffline:
    """Test device offline message handling"""
    
    def test_on_device_offline_removes_device(self):
        device = create_test_device()
        other_device = create_test_device("other_001", 30)
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        # Add other device to online
        service.online_devices[other_device.device_id] = other_device
        service.last_heartbeat[other_device.device_id] = time.time()
        
        offline = DeviceOffline(device_id=other_device.device_id)
        service.on_device_offline(offline)
        
        assert other_device.device_id not in service.online_devices
        assert other_device.device_id not in service.last_heartbeat


class TestDiscoveryServiceTimeouts:
    """Test timeout checking"""
    
    def test_check_timeouts_removes_stale_devices(self):
        device = create_test_device()
        other_device = create_test_device("other_001", 30)
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        # Add other device with old heartbeat
        service.online_devices[other_device.device_id] = other_device
        service.last_heartbeat[other_device.device_id] = time.time() - 20  # 20 seconds ago
        
        service.check_timeouts()
        
        assert other_device.device_id not in service.online_devices
        assert other_device.device_id not in service.last_heartbeat
        
    def test_check_timeouts_keeps_fresh_devices(self):
        device = create_test_device()
        other_device = create_test_device("other_001", 30)
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        # Add other device with recent heartbeat
        service.online_devices[other_device.device_id] = other_device
        service.last_heartbeat[other_device.device_id] = time.time()  # just now
        
        service.check_timeouts()
        
        assert other_device.device_id in service.online_devices
        
    def test_check_timeouts_handles_empty(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        # Should not raise exception
        service.check_timeouts()


class TestDiscoveryServiceQueries:
    """Test query methods"""
    
    def test_get_online_devices_returns_copy(self):
        device = create_test_device()
        other_device = create_test_device("other_001", 30)
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        service.online_devices[other_device.device_id] = other_device
        
        result = service.get_online_devices()
        
        assert result is not service.online_devices  # Should be a different object
        assert other_device.device_id in result
        
    def test_is_device_online_true(self):
        device = create_test_device()
        other_device = create_test_device("other_001", 30)
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        service.online_devices[other_device.device_id] = other_device
        
        assert service.is_device_online(other_device.device_id) is True
        
    def test_is_device_online_false(self):
        device = create_test_device()
        participant = Mock()
        service = DiscoveryService(device, participant)
        
        assert service.is_device_online("nonexistent") is False

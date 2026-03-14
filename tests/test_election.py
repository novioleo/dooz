import pytest
from core.types import DeviceInfo, BrainStatus
from core.election import ElectionService


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


class TestElectionServiceInit:
    """Test ElectionService initialization"""
    
    def test_init_sets_threshold(self):
        service = ElectionService(wisdom_threshold=30)
        assert service.wisdom_threshold == 30
        
    def test_init_default_threshold(self):
        service = ElectionService()
        assert service.wisdom_threshold == 50
        
    def test_init_no_brain_selected(self):
        service = ElectionService()
        assert service.current_brain_id is None


class TestElectionNoCandidates:
    """Test election when no candidates meet threshold"""
    
    def test_election_no_candidates(self):
        """No brain when all wisdom < threshold"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=30),
            "device_002": create_test_device("device_002", wisdom=40),
            "device_003": create_test_device("device_003", wisdom=49),
        }
        
        result = service.elect_brain(devices)
        
        assert result is None
        assert service.current_brain_id is None
        
    def test_election_empty_devices(self):
        """No brain when no devices"""
        service = ElectionService(wisdom_threshold=50)
        
        result = service.elect_brain({})
        
        assert result is None
        assert service.current_brain_id is None


class TestElectionSingleCandidate:
    """Test election with single candidate"""
    
    def test_election_single_candidate(self):
        """Single candidate becomes brain"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=30),
            "device_002": create_test_device("device_002", wisdom=60),
        }
        
        result = service.elect_brain(devices)
        
        assert result == "device_002"
        assert service.current_brain_id == "device_002"


class TestElectionHighestWisdom:
    """Test election with multiple candidates"""
    
    def test_election_highest_wisdom(self):
        """Highest wisdom wins"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=50),
            "device_002": create_test_device("device_002", wisdom=80),
            "device_003": create_test_device("device_003", wisdom=70),
        }
        
        result = service.elect_brain(devices)
        
        assert result == "device_002"
        assert service.current_brain_id == "device_002"
        
    def test_election_keeps_same_brain_when_highest(self):
        """Same brain is kept when still highest"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=50),
            "device_002": create_test_device("device_002", wisdom=80),
        }
        
        # First election
        result1 = service.elect_brain(devices)
        assert result1 == "device_002"
        
        # Second election with same devices
        result2 = service.elect_brain(devices)
        assert result2 == "device_002"
        assert service.current_brain_id == "device_002"


class TestElectionBelowThreshold:
    """Test election excluding devices below threshold"""
    
    def test_election_below_threshold(self):
        """Wisdom below threshold excluded"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=49),
            "device_002": create_test_device("device_002", wisdom=50),
            "device_003": create_test_device("device_003", wisdom=51),
        }
        
        result = service.elect_brain(devices)
        
        # Only device_002 and device_003 are candidates
        # device_003 has highest wisdom (51)
        assert result == "device_003"
        
    def test_election_exact_threshold_included(self):
        """Device with exact threshold is included"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=50),
        }
        
        result = service.elect_brain(devices)
        
        assert result == "device_001"


class TestElectionBrainStatus:
    """Test brain status queries"""
    
    def test_get_brain_status_no_brain(self):
        """Returns no_candidate when no brain"""
        service = ElectionService(wisdom_threshold=50)
        
        status = service.get_brain_status()
        
        assert status.brain_id is None
        assert status.wisdom_threshold == 50
        assert status.reason == "no_candidate"
        
    def test_get_brain_status_with_brain(self):
        """Returns brain info when brain elected"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=60),
        }
        service.elect_brain(devices)
        
        status = service.get_brain_status()
        
        assert status.brain_id == "device_001"
        assert status.wisdom_threshold == 50
        assert status.reason == "highest_wisdom"


class TestElectionIsBrain:
    """Test is_brain check"""
    
    def test_is_brain_true(self):
        """Returns true for brain device"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=60),
        }
        service.elect_brain(devices)
        
        assert service.is_brain("device_001") is True
        
    def test_is_brain_false(self):
        """Returns false for non-brain device"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=60),
        }
        service.elect_brain(devices)
        
        assert service.is_brain("device_002") is False
        
    def test_is_brain_false_no_brain(self):
        """Returns false when no brain elected"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=30),
        }
        service.elect_brain(devices)
        
        assert service.is_brain("device_001") is False


class TestElectionReset:
    """Test election reset"""
    
    def test_reset_clears_brain(self):
        """Reset clears current brain"""
        service = ElectionService(wisdom_threshold=50)
        
        devices = {
            "device_001": create_test_device("device_001", wisdom=60),
        }
        service.elect_brain(devices)
        assert service.current_brain_id == "device_001"
        
        service.reset()
        
        assert service.current_brain_id is None
        
    def test_reset_allows_re_election(self):
        """Reset allows new election"""
        service = ElectionService(wisdom_threshold=50)
        
        devices1 = {
            "device_001": create_test_device("device_001", wisdom=60),
        }
        service.elect_brain(devices1)
        
        service.reset()
        
        devices2 = {
            "device_002": create_test_device("device_002", wisdom=70),
        }
        result = service.elect_brain(devices2)
        
        assert result == "device_002"

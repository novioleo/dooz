"""Tests for Client base class"""
import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock, patch

from core.types import DeviceInfo
from core.discovery import DiscoveryService
from core.election import ElectionService
from core.transport import TransportService
from core.actor_state import ActorStateManager


class TestClient:
    """Test suite for Client base class"""
    
    @pytest.fixture
    def device_info(self):
        """Create a test device info"""
        return DeviceInfo(
            device_id="test-device-001",
            name="Test Device",
            role="worker",
            wisdom=75,
            output=True,
            skills=["skill1", "skill2"]
        )
    
    @pytest.fixture
    def config_yaml(self):
        """Create a temporary YAML config file"""
        yaml_content = """
device:
  id: "yaml-device-001"
  name: "YAML Device"
  role: "brain"
  wisdom: 80
  output: true
  skills:
    - name: "skill1"
    - name: "skill2"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    @pytest.fixture
    def mock_participant(self):
        """Mock FastDDS participant"""
        return Mock()
    
    def test_client_initialization(self, device_info, mock_participant):
        """Test Client initializes with correct attributes"""
        from client.base import Client
        
        client = Client(device_info)
        
        assert client.config == device_info
        assert client.device_id == device_info.device_id
        assert client.wisdom == device_info.wisdom
        assert client.output == device_info.output
        assert client.skills == device_info.skills
        assert client._is_running == False
        
    def test_client_services_initialized(self, device_info, mock_participant):
        """Test Client initializes all services"""
        from client.base import Client
        
        client = Client(device_info)
        
        assert client.discovery is not None
        assert isinstance(client.discovery, DiscoveryService)
        assert client.election is not None
        assert isinstance(client.election, ElectionService)
        assert client.transport is not None
        assert isinstance(client.transport, TransportService)
        assert client.actor_state is not None
        assert isinstance(client.actor_state, ActorStateManager)
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_client_from_yaml(self, mock_actor_state, mock_transport, mock_discovery, config_yaml):
        """Test Client can be created from YAML config"""
        from client.base import Client
        
        client = Client.from_yaml(config_yaml)
        
        assert client.device_id == "yaml-device-001"
        assert client.wisdom == 80
        assert client.output == True
        assert "skill1" in client.skills
        assert "skill2" in client.skills
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_start_sets_running_flag(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test start() sets _is_running to True"""
        from client.base import Client
        
        client = Client(device_info)
        client.start()
        
        assert client._is_running == True
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_stop_clears_running_flag(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test stop() sets _is_running to False"""
        from client.base import Client
        
        client = Client(device_info)
        client._is_running = True
        client.stop()
        
        assert client._is_running == False
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_start_calls_discovery_start(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test start() calls discovery.start()"""
        from client.base import Client
        
        client = Client(device_info)
        client.start()
        
        mock_discovery_instance = client.discovery
        mock_discovery_instance.start.assert_called_once()
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_start_creates_subscriptions(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test start() sets up subscriptions for expected topics"""
        from client.base import Client
        
        client = Client(device_info)
        client.start()
        
        # Verify transport.create_subscriber was called for expected topics
        expected_topics = [
            "dooz/device/announce",
            "dooz/device/heartbeat",
            "dooz/device/offline",
            "dooz/brain/status",
            "dooz/task/dispatch",
            "dooz/task/notify",
        ]
        
        # Check that create_subscriber was called for each topic
        call_args_list = client.transport.create_subscriber.call_args_list
        called_topics = [call[0][0] for call in call_args_list]
        
        for topic in expected_topics:
            assert topic in called_topics, f"Topic {topic} not subscribed"
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_stop_calls_discovery_stop(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test stop() calls discovery.stop()"""
        from client.base import Client
        
        client = Client(device_info)
        client.stop()
        
        mock_discovery_instance = client.discovery
        mock_discovery_instance.stop.assert_called_once()
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_send_task_request_publishes_message(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test send_task_request publishes to task/request topic"""
        from client.base import Client
        
        client = Client(device_info)
        client.send_task_request("test task")
        
        client.transport.publish.assert_called()
        call_args = client.transport.publish.call_args
        assert call_args[0][0] == 'dooz/task/request'
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_send_task_request_includes_request_id(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test send_task_request includes request_id in message"""
        from client.base import Client
        
        client = Client(device_info)
        client.send_task_request("test task")
        
        call_args = client.transport.publish.call_args
        message = call_args[0][1]
        
        assert 'request_id' in message
        assert message['msg_type'] == 'task/request'
        assert message['text'] == "test task"
        assert message['requester_id'] == client.device_id
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_get_status_returns_correct_structure(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test get_status returns expected keys"""
        from client.base import Client
        
        client = Client(device_info)
        status = client.get_status()
        
        assert 'device_id' in status
        assert 'wisdom' in status
        assert 'output' in status
        assert 'skills' in status
        assert 'is_brain' in status
        assert 'actor_state' in status
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_get_status_returns_device_info(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test get_status returns correct device info"""
        from client.base import Client
        
        client = Client(device_info)
        status = client.get_status()
        
        assert status['device_id'] == device_info.device_id
        assert status['wisdom'] == device_info.wisdom
        assert status['output'] == device_info.output
        assert status['skills'] == device_info.skills
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_execute_skill_returns_success(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test _execute_skill returns success dict"""
        from client.base import Client
        
        client = Client(device_info)
        result = client._execute_skill("test_skill", {"param": "value"})
        
        assert 'success' in result
        assert result['success'] == True
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_on_task_dispatch_only_handles_own_tasks(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test _on_task_dispatch ignores tasks not for this device"""
        from client.base import Client
        
        client = Client(device_info)
        
        # Message for different device
        message = {
            'msg_type': 'task/dispatch',
            'executor_id': 'other-device',
            'skill_name': 'test_skill',
            'parameters': {}
        }
        
        client._on_task_dispatch(message)
        
        # Should not publish response for other devices
        client.transport.publish.assert_not_called()
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_on_task_dispatch_handles_own_task(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test _on_task_dispatch executes task for this device"""
        from client.base import Client
        
        client = Client(device_info)
        
        message = {
            'msg_type': 'task/dispatch',
            'executor_id': device_info.device_id,
            'request_id': 'req-123',
            'skill_name': 'test_skill',
            'parameters': {'key': 'value'}
        }
        
        client._on_task_dispatch(message)
        
        # Should publish response
        client.transport.publish.assert_called()
        call_args = client.transport.publish.call_args
        assert call_args[0][0] == 'dooz/task/response'
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_on_task_notify_logs_when_output_enabled(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test _on_task_notify logs when output is True"""
        from client.base import Client
        
        client = Client(device_info)
        
        message = {
            'msg_type': 'task/notify',
            'message': 'Test notification'
        }
        
        with patch('client.base.logger') as mock_logger:
            client._on_task_notify(message)
            mock_logger.info.assert_called()
    
    @patch('client.base.DiscoveryService')
    @patch('client.base.TransportService')
    @patch('client.base.ActorStateManager')
    def test_on_task_notify_ignores_when_output_disabled(self, mock_actor_state, mock_transport, mock_discovery, device_info):
        """Test _on_task_notify ignores when output is False"""
        from client.base import Client
        
        device_info.output = False
        client = Client(device_info)
        
        message = {
            'msg_type': 'task/notify',
            'message': 'Test notification'
        }
        
        with patch('client.base.logger') as mock_logger:
            client._on_task_notify(message)
            # Should not log when output is disabled
            mock_logger.info.assert_not_called()

import logging
import yaml
from typing import Optional
from pathlib import Path

from core.types import DeviceInfo, TaskRequest, TaskDispatch, TaskResponse
from core.discovery import DiscoveryService
from core.election import ElectionService
from core.transport import TransportService
from core.actor_state import ActorStateManager
from client.brain_plugin import BrainPlugin

logger = logging.getLogger(__name__)


class Client:
    """设备客户端基类 - 支持可选的大脑插件"""
    
    def __init__(self, config: DeviceInfo):
        self.config = config
        self.device_id = config.device_id
        self.wisdom = config.wisdom
        self.output = config.output
        self.skills = config.skills
        self.brain_enabled = config.brain_enabled
        
        # 服务
        self.participant = None  # FastDDS participant
        self.discovery = DiscoveryService(config, self.participant)
        self.election = ElectionService(wisdom_threshold=50)
        self.transport = TransportService(self.participant, self.device_id)
        self.actor_state = ActorStateManager(self.device_id)
        
        # 大脑插件 (可选)
        self.brain: Optional[BrainPlugin] = None
        if self.brain_enabled:
            self.brain = BrainPlugin(self)
            logger.info(f"Brain plugin enabled for {self.device_id}")
        
        self._is_running = False
        
    @classmethod
    def from_yaml(cls, config_path: str) -> 'Client':
        """从 YAML 配置文件创建 Client"""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        device_data = config_data['device']
        config = DeviceInfo(
            device_id=device_data['id'],
            name=device_data['name'],
            role=device_data['role'],
            wisdom=device_data['wisdom'],
            output=device_data['output'],
            brain_enabled=device_data.get('brain_enabled', False),
            skills=[s['name'] for s in device_data.get('skills', [])]
        )
        return cls(config)
        
    def start(self):
        """启动客户端"""
        logger.info(f"Starting client: {self.device_id}")
        self._is_running = True
        
        # 初始化 FastDDS
        self._init_dds()
        
        # 启动服务
        self.discovery.start()
        self._setup_subscriptions()
        
        # 启动大脑插件
        if self.brain:
            self.brain.start()
        
        logger.info(f"Client {self.device_id} started")
        
    def stop(self):
        """停止客户端"""
        logger.info(f"Stopping client: {self.device_id}")
        self._is_running = False
        
        # 停止大脑插件
        if self.brain:
            self.brain.stop()
            
        self.discovery.stop()
        
    def _init_dds(self):
        """初始化 FastDDS"""
        # TODO: 初始化 FastDDS participant
        logger.info("FastDDS participant initialized (placeholder)")
        
    def _setup_subscriptions(self):
        """设置消息订阅"""
        topics = [
            "dooz/device/announce",
            "dooz/device/heartbeat",
            "dooz/device/offline",
            "dooz/brain/status",
            "dooz/task/request",
            "dooz/task/dispatch",
            "dooz/task/response",
            "dooz/task/notify",
        ]
        for topic in topics:
            self.transport.create_subscriber(topic, self._handle_message)
            
    def _handle_message(self, message: dict):
        """处理收到的消息"""
        msg_type = message.get('msg_type', '')
        
        if msg_type == 'device/announce':
            self.discovery.on_device_announce(message)
            self._update_brain_election()
            
        elif msg_type == 'device/offline':
            self.discovery.on_device_offline(message)
            self._update_brain_election()
            
        elif msg_type == 'brain/status':
            self._on_brain_status(message)
            
        elif msg_type == 'task/request':
            # 如果启用了大脑且自己是大脑，处理请求
            if self.brain and self.election.is_brain(self.device_id):
                self.brain.on_task_request(message)
            
        elif msg_type == 'task/dispatch':
            self._on_task_dispatch(message)
            
        elif msg_type == 'task/response':
            # 如果是大脑，接收执行结果
            if self.brain and self.election.is_brain(self.device_id):
                self.brain.on_task_response(message)
            
        elif msg_type == 'task/notify':
            self._on_task_notify(message)
            
    def _update_brain_election(self):
        """更新大脑选举"""
        online_devices = self.discovery.get_online_devices()
        # 加入自己
        online_devices[self.device_id] = self.config
        
        new_brain_id = self.election.elect_brain(online_devices)
        brain_status = self.election.get_brain_status()
        self._broadcast_brain_status(brain_status)
        
    def _broadcast_brain_status(self, status):
        """广播大脑状态"""
        import time
        msg = {
            'msg_type': 'brain/status',
            'brain_id': status.brain_id,
            'wisdom_threshold': status.wisdom_threshold,
            'reason': status.reason,
            'timestamp': time.time()
        }
        self.transport.publish('dooz/brain/status', msg)
        
    def send_task_request(self, text: str):
        """发送任务请求"""
        import uuid, time
        request = {
            'msg_type': 'task/request',
            'request_id': str(uuid.uuid4()),
            'text': text,
            'requester_id': self.device_id,
            'timestamp': time.time()
        }
        self.transport.publish('dooz/task/request', request)
        self.actor_state.update_on_receive(f"request:{text}")
        
    def _on_brain_status(self, message: dict):
        """处理大脑状态更新"""
        brain_id = message.get('brain_id')
        reason = message.get('reason', '')
        logger.info(f"Brain status: {brain_id} ({reason})")
        
        # 如果自己不是大脑，且有大脑变更，需要更新本地选举状态
        if not self.election.is_brain(self.device_id):
            # 触发重新选举
            self._update_brain_election()
        
    def _on_task_dispatch(self, message: dict):
        """处理任务分发"""
        if message.get('executor_id') != self.device_id:
            return
            
        skill_name = message.get('skill_name')
        params = message.get('parameters', {})
        
        logger.info(f"Received task: {skill_name} with params {params}")
        
        # 更新 actor state
        self.actor_state.update_on_receive(skill_name)
        
        # 执行 skill
        result = self._execute_skill(skill_name, params)
        
        # 发送响应
        import time
        response = {
            'msg_type': 'task/response',
            'request_id': message.get('request_id'),
            'success': result['success'],
            'result': result.get('message', ''),
            'executor_id': self.device_id,
            'timestamp': time.time()
        }
        self.transport.publish('dooz/task/response', response)
        
        # 更新 actor state
        self.actor_state.update_on_complete(result['success'])
        
    def _on_task_notify(self, message: dict):
        """处理任务通知"""
        if not self.output:
            return
            
        logger.info(f"NOTIFICATION: {message.get('message')}")
        self.actor_state.update_on_receive("notify")
        self.actor_state.update_on_complete(True)
        
    def _execute_skill(self, skill_name: str, params: dict) -> dict:
        """执行 skill (由子类重写)"""
        logger.info(f"Executing skill: {skill_name}")
        return {'success': True, 'message': f'Skill {skill_name} executed'}
        
    def get_status(self) -> dict:
        """获取客户端状态"""
        return {
            'device_id': self.device_id,
            'wisdom': self.wisdom,
            'output': self.output,
            'brain_enabled': self.brain_enabled,
            'skills': self.skills,
            'is_brain': self.election.is_brain(self.device_id),
            'actor_state': {
                'history': self.actor_state.get_history(),
                'current': self.actor_state.get_current()
            }
        }

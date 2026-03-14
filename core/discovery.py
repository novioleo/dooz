import logging
import time
import threading
from typing import Dict, Optional, Callable
from core.types import DeviceInfo, DeviceAnnounce, DeviceHeartbeat, DeviceOffline

logger = logging.getLogger(__name__)


class DiscoveryService:
    """设备发现服务 - 管理设备注册，心跳、在线状态"""
    
    HEARTBEAT_INTERVAL = 3  # 秒
    HEARTBEAT_TIMEOUT = 10   # 秒
    
    def __init__(self, device_info: DeviceInfo, participant, transport=None):
        self.device_info = device_info
        self.participant = participant
        self.transport = transport
        self.online_devices: Dict[str, DeviceInfo] = {}
        self.last_heartbeat: Dict[str, float] = {}
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def set_transport(self, transport):
        """设置传输服务"""
        self.transport = transport
        
    def start(self):
        """启动发现服务"""
        self._running = True
        self._stop_event.clear()
        
        # 注册消息回调
        if self.transport:
            # 添加自己到在线列表
            self.online_devices[self.device_info.device_id] = self.device_info
            self.last_heartbeat[self.device_info.device_id] = time.time()
            
        # 广播上线
        self._announce_presence()
        
        # 启动心跳线程
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        
        logger.info(f"DiscoveryService started for {self.device_info.device_id}")
        
    def stop(self):
        """停止发现服务"""
        self._running = False
        self._stop_event.set()
        
        # 停止心跳线程
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2)
            
        # 广播离线
        self._announce_offline()
        
        # 清理
        self.online_devices.clear()
        self.last_heartbeat.clear()
        
        logger.info(f"DiscoveryService stopped for {self.device_info.device_id}")
        
    def _heartbeat_loop(self):
        """心跳循环"""
        while not self._stop_event.is_set():
            try:
                # 发送心跳
                self.send_heartbeat()
                
                # 检查超时
                self.check_timeouts()
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                
            # 等待下一个心跳间隔
            self._stop_event.wait(self.HEARTBEAT_INTERVAL)
            
    def _announce_presence(self):
        """广播设备上线"""
        msg = DeviceAnnounce(device=self.device_info)
        msg_dict = {
            'msg_type': msg.msg_type,
            'device': {
                'device_id': self.device_info.device_id,
                'name': self.device_info.name,
                'role': self.device_info.role,
                'wisdom': self.device_info.wisdom,
                'output': self.device_info.output,
                'brain_enabled': self.device_info.brain_enabled,
                'skills': self.device_info.skills,
            },
            'timestamp': msg.timestamp
        }
        
        # 通过 Transport 发布
        if self.transport:
            self.transport.publish('dooz/device/announce', msg_dict)
            
        logger.info(f"Announced presence: {self.device_info.device_id}")
        
    def _announce_offline(self):
        """广播设备离线"""
        msg = DeviceOffline(device_id=self.device_info.device_id)
        msg_dict = {
            'msg_type': msg.msg_type,
            'device_id': self.device_info.device_id,
            'timestamp': msg.timestamp
        }
        
        # 通过 Transport 发布
        if self.transport:
            self.transport.publish('dooz/device/offline', msg_dict)
            
        logger.info(f"Announced offline: {self.device_info.device_id}")
        
    def send_heartbeat(self):
        """发送心跳"""
        msg = DeviceHeartbeat(device_id=self.device_info.device_id)
        msg_dict = {
            'msg_type': msg.msg_type,
            'device_id': self.device_info.device_id,
            'timestamp': msg.timestamp
        }
        
        # 通过 Transport 发布
        if self.transport:
            self.transport.publish('dooz/device/heartbeat', msg_dict)
            
        # 更新自己的心跳时间
        self.last_heartbeat[self.device_info.device_id] = time.time()
        
    def on_device_announce(self, data):
        """处理设备上线消息"""
        # 支持 dict 和 typed object
        if hasattr(data, 'get'):
            # It's a dict
            if 'device' not in data:
                return
            device_data = data['device']
        else:
            # It's a typed object (backwards compatibility)
            device = data.device
            device_data = {
                'device_id': device.device_id,
                'name': device.name,
                'role': device.role,
                'wisdom': device.wisdom,
                'output': device.output,
                'brain_enabled': getattr(device, 'brain_enabled', False),
                'skills': device.skills
            }
            
        device_id = device_data.get('device_id')
        
        if device_id == self.device_info.device_id:
            return  # 忽略自己的消息
            
        device = DeviceInfo(
            device_id=device_id,
            name=device_data.get('name', ''),
            role=device_data.get('role', ''),
            wisdom=device_data.get('wisdom', 0),
            output=device_data.get('output', False),
            brain_enabled=device_data.get('brain_enabled', False),
            skills=device_data.get('skills', [])
        )
        
        self.online_devices[device_id] = device
        self.last_heartbeat[device_id] = time.time()
        logger.info(f"Device online: {device_id} (wisdom={device.wisdom})")
        
    def on_device_offline(self, data):
        """处理设备离线消息"""
        # 支持 dict 和 typed object
        if hasattr(data, 'get'):
            device_id = data.get('device_id', '')
        else:
            device_id = data.device_id
        
        if device_id in self.online_devices:
            del self.online_devices[device_id]
        if device_id in self.last_heartbeat:
            del self.last_heartbeat[device_id]
        logger.info(f"Device offline: {device_id}")
        
    def on_heartbeat(self, data):
        """处理心跳消息"""
        # 支持 dict 和 typed object
        if hasattr(data, 'get'):
            device_id = data.get('device_id', '')
        else:
            device_id = data.device_id
        
        if device_id != self.device_info.device_id:
            self.last_heartbeat[device_id] = time.time()
            
    def check_timeouts(self):
        """检查超时设备"""
        current_time = time.time()
        timed_out = []
        
        for device_id, last_time in list(self.last_heartbeat.items()):
            # 跳过自己
            if device_id == self.device_info.device_id:
                continue
            if current_time - last_time > self.HEARTBEAT_TIMEOUT:
                timed_out.append(device_id)
                
        for device_id in timed_out:
            if device_id in self.online_devices:
                del self.online_devices[device_id]
            if device_id in self.last_heartbeat:
                del self.last_heartbeat[device_id]
                logger.info(f"Device timed out: {device_id}")
                
    def get_online_devices(self) -> Dict[str, DeviceInfo]:
        """获取在线设备列表"""
        # 确保自己也在列表中
        if self.device_info.device_id not in self.online_devices:
            self.online_devices[self.device_info.device_id] = self.device_info
        return self.online_devices.copy()
        
    def is_device_online(self, device_id: str) -> bool:
        """检查设备是否在线"""
        return device_id in self.online_devices

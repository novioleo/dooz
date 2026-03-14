import logging
import time
from typing import Dict, Optional
from core.types import DeviceInfo, DeviceAnnounce, DeviceHeartbeat, DeviceOffline

logger = logging.getLogger(__name__)


class DiscoveryService:
    """设备发现服务 - 管理设备注册、心跳、在线状态"""
    
    HEARTBEAT_INTERVAL = 3  # 秒
    HEARTBEAT_TIMEOUT = 10   # 秒
    
    def __init__(self, device_info: DeviceInfo, participant):
        self.device_info = device_info
        self.participant = participant
        self.online_devices: Dict[str, DeviceInfo] = {}
        self.last_heartbeat: Dict[str, float] = {}
        self._running = False
        
    def start(self):
        """启动发现服务"""
        self._running = True
        self._announce_presence()
        logger.info(f"DiscoveryService started for {self.device_info.device_id}")
        
    def stop(self):
        """停止发现服务"""
        self._running = False
        self._announce_offline()
        logger.info(f"DiscoveryService stopped for {self.device_info.device_id}")
        
    def _announce_presence(self):
        """广播设备上线"""
        msg = DeviceAnnounce(device=self.device_info)
        # TODO: Publish via FastDDS
        # Add self to online devices when announcing presence
        self.online_devices[self.device_info.device_id] = self.device_info
        logger.info(f"Announced presence: {self.device_info.device_id}")
        
    def _announce_offline(self):
        """广播设备离线"""
        msg = DeviceOffline(device_id=self.device_info.device_id)
        # TODO: Publish via FastDDS
        # Remove self from online devices
        if self.device_info.device_id in self.online_devices:
            del self.online_devices[self.device_info.device_id]
        if self.device_info.device_id in self.last_heartbeat:
            del self.last_heartbeat[self.device_info.device_id]
        logger.info(f"Announced offline: {self.device_info.device_id}")
        
    def send_heartbeat(self):
        """发送心跳"""
        msg = DeviceHeartbeat(device_id=self.device_info.device_id)
        # TODO: Publish via FastDDS
        self.last_heartbeat[self.device_info.device_id] = time.time()
        
    def on_device_announce(self, announce: DeviceAnnounce):
        """处理设备上线消息"""
        device = announce.device
        if device.device_id == self.device_info.device_id:
            return  # 忽略自己的消息
            
        self.online_devices[device.device_id] = device
        self.last_heartbeat[device.device_id] = time.time()
        logger.info(f"Device online: {device.device_id} (wisdom={device.wisdom})")
        
    def on_device_offline(self, offline: DeviceOffline):
        """处理设备离线消息"""
        device_id = offline.device_id
        if device_id in self.online_devices:
            del self.online_devices[device_id]
        if device_id in self.last_heartbeat:
            del self.last_heartbeat[device_id]
        logger.info(f"Device offline: {device_id}")
        
    def on_heartbeat(self, heartbeat: DeviceHeartbeat):
        """处理心跳消息"""
        device_id = heartbeat.device_id
        if device_id != self.device_info.device_id:
            self.last_heartbeat[device_id] = time.time()
            
    def check_timeouts(self):
        """检查超时设备"""
        current_time = time.time()
        timed_out = []
        for device_id, last_time in list(self.last_heartbeat.items()):
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
        return self.online_devices.copy()
        
    def is_device_online(self, device_id: str) -> bool:
        """检查设备是否在线"""
        return device_id in self.online_devices

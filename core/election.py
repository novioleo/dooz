import logging
from typing import Dict, Optional
from core.types import DeviceInfo, BrainStatus

logger = logging.getLogger(__name__)


class ElectionService:
    """大脑选举服务 - 基于 wisdom 值选举脑节点"""
    
    def __init__(self, wisdom_threshold: int = 50):
        self.wisdom_threshold = wisdom_threshold
        self.current_brain_id: Optional[str] = None
        
    def elect_brain(self, devices: Dict[str, DeviceInfo]) -> Optional[str]:
        """
        选举大脑
        规则：wisdom >= threshold 的设备中，wisdom 最高的成为大脑
        """
        candidates = {
            device_id: device 
            for device_id, device in devices.items()
            if device.wisdom >= self.wisdom_threshold
        }
        
        if not candidates:
            logger.info("No brain candidate available (all wisdom < threshold)")
            self.current_brain_id = None
            return None
            
        # 选择 wisdom 最高的设备
        brain_id = max(candidates.keys(), key=lambda k: candidates[k].wisdom)
        
        if brain_id != self.current_brain_id:
            logger.info(f"Brain elected: {brain_id} (wisdom={candidates[brain_id].wisdom})")
            self.current_brain_id = brain_id
            
        return brain_id
    
    def get_brain_status(self) -> BrainStatus:
        """获取当前大脑状态"""
        if self.current_brain_id is None:
            return BrainStatus(
                brain_id=None,
                wisdom_threshold=self.wisdom_threshold,
                reason="no_candidate"
            )
        return BrainStatus(
            brain_id=self.current_brain_id,
            wisdom_threshold=self.wisdom_threshold,
            reason="highest_wisdom"
        )
    
    def is_brain(self, device_id: str) -> bool:
        """检查是否为大脑"""
        return device_id == self.current_brain_id
    
    def reset(self):
        """重置选举状态"""
        self.current_brain_id = None

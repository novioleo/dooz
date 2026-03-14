import logging
from core.types import ActorState

logger = logging.getLogger(__name__)


class ActorStateManager:
    """Actor 状态管理器 - 管理设备的操作历史、当前操作、下一步操作"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.state = ActorState(device_id=device_id)
        
    def update_on_receive(self, operation: str):
        """接收任务时更新状态"""
        self.state.update_on_receive(operation)
        logger.info(f"{self.device_id}: received operation '{operation}'")
        
    def update_on_complete(self, success: bool):
        """任务完成时更新状态"""
        self.state.update_on_complete(success)
        logger.info(f"{self.device_id}: completed operation, history={self.state.history}")
        
    def set_next_ops(self, operations: list):
        """设置下一步可执行的操作"""
        self.state.next_ops = operations
        
    def get_state(self) -> ActorState:
        """获取当前状态"""
        return self.state
        
    def get_history(self) -> list:
        """获取操作历史"""
        return self.state.history.copy()
        
    def get_current(self) -> str:
        """获取当前操作"""
        return self.state.current

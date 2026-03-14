"""
消息传输服务 - 基于 FastDDS 的 Pub/Sub
MVP 阶段使用内存队列模拟，FastDDS 集成在运行时完成
"""
import logging
import json
from typing import Dict, Callable, Any
from dataclasses import asdict

logger = logging.getLogger(__name__)


class TransportService:
    """消息传输服务 - 负责消息的发布和订阅"""
    
    def __init__(self, participant, device_id: str):
        self.participant = participant
        self.device_id = device_id
        self.publishers: Dict[str, Any] = {}
        self.subscribers: Dict[str, list] = {}
        self._callbacks: Dict[str, list] = {}
        
    def create_publisher(self, topic_name: str):
        """创建发布者"""
        # TODO: 集成 FastDDS publisher
        self.publishers[topic_name] = None
        logger.info(f"Publisher created for topic: {topic_name}")
        
    def create_subscriber(self, topic_name: str, callback: Callable):
        """创建订阅者"""
        if topic_name not in self.subscribers:
            self.subscribers[topic_name] = []
            # TODO: 集成 FastDDS subscriber
        self.subscribers[topic_name].append(callback)
        
        if topic_name not in self._callbacks:
            self._callbacks[topic_name] = []
        self._callbacks[topic_name].append(callback)
        logger.info(f"Subscriber created for topic: {topic_name}")
        
    def publish(self, topic_name: str, message: Any):
        """发布消息"""
        # TODO: 通过 FastDDS 发布
        logger.debug(f"Publishing to {topic_name}: {message}")
        
    def on_message_received(self, topic_name: str, message: Any):
        """收到消息时触发回调"""
        if topic_name in self._callbacks:
            for callback in self._callbacks[topic_name]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error in callback for {topic_name}: {e}")
                    
    def get_subscribed_topics(self) -> list:
        """获取已订阅的话题列表"""
        return list(self.subscribers.keys())

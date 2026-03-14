"""
消息传输服务 - 基于内存的 Pub/Sub
MVP 阶段使用内存消息总线，可替换为 FastDDS
"""
import logging
import threading
from typing import Dict, Callable, Any, List
from dataclasses import asdict

logger = logging.getLogger(__name__)


class InMemoryBus:
    """内存消息总线 - 跨设备消息传递 (MVP用，生产可替换为FastDDS)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscribers: Dict[str, List[Callable]] = {}
                    cls._instance._lock = threading.Lock()
        return cls._instance
    
    def subscribe(self, topic: str, callback: Callable):
        """订阅话题"""
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            if callback not in self._subscribers[topic]:
                self._subscribers[topic].append(callback)
                logger.debug(f"Subscribed to {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """取消订阅"""
        with self._lock:
            if topic in self._subscribers:
                if callback in self._subscribers[topic]:
                    self._subscribers[topic].remove(callback)
    
    def publish(self, topic: str, message: Any, sender_id: str = None):
        """发布消息到话题"""
        with self._lock:
            subscribers = self._subscribers.get(topic, []).copy()
        
        for callback in subscribers:
            try:
                # 添加 sender_id 到消息中
                if isinstance(message, dict):
                    message['sender_id'] = sender_id
                callback(message)
            except Exception as e:
                logger.error(f"Error in subscriber callback for {topic}: {e}")
    
    def clear(self):
        """清除所有订阅 (用于测试)"""
        with self._lock:
            self._subscribers.clear()


class TransportService:
    """消息传输服务 - 负责消息的发布和订阅"""
    
    def __init__(self, participant, device_id: str):
        self.participant = participant
        self.device_id = device_id
        self.publishers: Dict[str, Any] = {}
        self.subscribers: Dict[str, list] = {}
        self._callbacks: Dict[str, list] = {}
        
        # 内存消息总线 (MVP)
        self._bus = InMemoryBus()
        
    def create_publisher(self, topic_name: str):
        """创建发布者"""
        self.publishers[topic_name] = True
        logger.info(f"Publisher created for topic: {topic_name}")
        
    def create_subscriber(self, topic_name: str, callback: Callable):
        """创建订阅者"""
        if topic_name not in self.subscribers:
            self.subscribers[topic_name] = []
        
        self.subscribers[topic_name].append(callback)
        
        if topic_name not in self._callbacks:
            self._callbacks[topic_name] = []
        self._callbacks[topic_name].append(callback)
        
        # 注册到内存总线
        self._bus.subscribe(topic_name, callback)
        
        logger.info(f"Subscriber created for topic: {topic_name}")
        
    def publish(self, topic_name: str, message: Any):
        """发布消息"""
        if topic_name not in self.publishers:
            logger.warning(f"No publisher for topic: {topic_name}")
            return
            
        # 确保消息是字典
        if not isinstance(message, dict):
            logger.warning(f"Message is not a dict: {type(message)}")
            return
            
        # 通过内存总线发布
        self._bus.publish(topic_name, message, self.device_id)
        
        logger.debug(f"Published to {topic_name}: {message.get('msg_type', 'unknown')}")
        
    def on_message_received(self, topic_name: str, message: Any):
        """收到消息时触发回调 (供测试使用)"""
        if topic_name in self._callbacks:
            for callback in self._callbacks[topic_name]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error in callback for {topic_name}: {e}")
                    
    def get_subscribed_topics(self) -> list:
        """获取已订阅的话题列表"""
        return list(self.subscribers.keys())
    
    def clear_bus(self):
        """清除消息总线 (用于测试)"""
        self._bus.clear()

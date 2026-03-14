"""内存消息总线 (MVP)."""

import threading
from typing import Dict, List, Callable


class MessageBus:
    """简单的内存 Pub/Sub 总线."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
    
    def subscribe(self, topic: str, callback: Callable):
        with self._lock:
            self._subscribers.setdefault(topic, []).append(callback)
    
    def publish(self, topic: str, message: dict):
        with self._lock:
            subs = self._subscribers.get(topic, []).copy()
        for cb in subs:
            try:
                cb(message)
            except Exception:
                pass
    
    def unsubscribe(self, topic: str, callback: Callable):
        with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic] = [c for c in self._subscribers[topic] if c != callback]


# 全局总线
bus = MessageBus()

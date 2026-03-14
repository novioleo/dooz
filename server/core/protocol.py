"""消息协议常量."""

from enum import Enum


class MsgType(Enum):
    DEVICE_ANNOUNCE = "device/announce"
    DEVICE_HEARTBEAT = "device/heartbeat"
    DEVICE_OFFLINE = "device/offline"
    TASK_REQUEST = "task/request"
    TASK_DISPATCH = "task/dispatch"
    TASK_RESPONSE = "task/response"
    TASK_NOTIFY = "task/notify"


class TopicPrefix:
    BASE = "dooz"
    
    @staticmethod
    def for_tenant(tenant_id: str) -> str:
        return f"{TopicPrefix.BASE}/{tenant_id}"
    
    @staticmethod
    def device_announce(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/device/announce"
    
    @staticmethod
    def device_heartbeat(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/device/heartbeat"
    
    @staticmethod
    def device_offline(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/device/offline"
    
    @staticmethod
    def task_request(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/task/request"
    
    @staticmethod
    def task_dispatch(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/task/dispatch"
    
    @staticmethod
    def task_response(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/task/response"
    
    @staticmethod
    def task_notify(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/task/notify"

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import time


class MsgType(Enum):
    DEVICE_ANNOUNCE = "device/announce"
    DEVICE_HEARTBEAT = "device/heartbeat"
    DEVICE_OFFLINE = "device/offline"
    BRAIN_ELECTION = "brain/election"
    BRAIN_STATUS = "brain/status"
    TASK_REQUEST = "task/request"
    TASK_DISPATCH = "task/dispatch"
    TASK_RESPONSE = "task/response"
    TASK_NOTIFY = "task/notify"
    ACTOR_UPDATE = "actor/update"


@dataclass
class DeviceInfo:
    device_id: str
    name: str
    role: str
    wisdom: int
    output: bool
    brain_enabled: bool = False  # 是否启用大脑功能
    skills: List[str] = field(default_factory=list)


@dataclass
class DeviceAnnounce:
    msg_type: str = MsgType.DEVICE_ANNOUNCE.value
    device: Optional[DeviceInfo] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class DeviceHeartbeat:
    msg_type: str = MsgType.DEVICE_HEARTBEAT.value
    device_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class DeviceOffline:
    msg_type: str = MsgType.DEVICE_OFFLINE.value
    device_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class BrainStatus:
    msg_type: str = MsgType.BRAIN_STATUS.value
    brain_id: Optional[str] = None
    wisdom_threshold: int = 50
    reason: str = "no_candidate"  # "highest_wisdom" or "no_candidate"
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskRequest:
    msg_type: str = MsgType.TASK_REQUEST.value
    request_id: str = ""
    text: str = ""
    requester_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskDispatch:
    msg_type: str = MsgType.TASK_DISPATCH.value
    request_id: str = ""
    skill_name: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    executor_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskResponse:
    msg_type: str = MsgType.TASK_RESPONSE.value
    request_id: str = ""
    success: bool = False
    result: str = ""
    executor_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskNotify:
    msg_type: str = MsgType.TASK_NOTIFY.value
    request_id: str = ""
    message: str = ""
    source_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class ActorState:
    device_id: str = ""
    history: List[str] = field(default_factory=list)
    current: Optional[str] = None
    next_ops: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def update_on_receive(self, operation: str):
        self.current = operation
        
    def update_on_complete(self, success: bool):
        if self.current:
            self.history.append(self.current)
            self.current = None

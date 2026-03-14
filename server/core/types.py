"""消息类型."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import time
import uuid


@dataclass
class DeviceInfo:
    device_id: str
    name: str
    wisdom: int
    output: bool
    llm_enabled: bool = False
    skills: List[str] = field(default_factory=list)


@dataclass
class TaskRequest:
    msg_type: str = "task/request"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    requester_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskDispatch:
    msg_type: str = "task/dispatch"
    request_id: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    executor_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskResponse:
    msg_type: str = "task/response"
    request_id: str = ""
    task_id: str = ""
    success: bool = False
    result: str = ""
    executor_id: str = ""
    timestamp: float = field(default_factory=time.time)

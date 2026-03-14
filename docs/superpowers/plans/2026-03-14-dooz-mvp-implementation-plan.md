# dooz MVP Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个最小可行的去中心化设备协作系统，演示多设备自发现、脑选举、任务分发、多设备协作执行与结果通知能力。

**Architecture:** 基于 FastDDS 的去中心化 Pub/Sub 架构，通过 Tailscale VPN 组网。每个设备是独立的 Python 进程，通过 FastDDS 话题通信。大脑节点运行 LLM 代理，负责理解用户意图并调度多设备协作。

**Tech Stack:** Python 3.10+, FastDDS (fastdds Python binding), PyYAML, OpenAI API

---

## 文件结构规划

```
dooz/
├── core/                          # 核心模块
│   ├── __init__.py
│   ├── types.py                   # 消息类型定义
│   ├── discovery.py               # 设备发现服务
│   ├── election.py                # 大脑选举服务
│   ├── transport.py               # 消息传输服务
│   └── actor_state.py             # Actor 状态机
├── client/                        # 客户端
│   ├── __init__.py
│   ├── base.py                    # Client 基类
│   ├── brain.py                   # Brain 扩展
│   ├── skill_executor.py          # Skill 执行器
│   └── main.py                    # 入口
├── brain/                         # 大脑能力
│   ├── __init__.py
│   ├── llm_client.py              # LLM 调用
│   └── tools/                     # 工具
│       ├── __init__.py
│       ├── search_movie.py
│       ├── play_video.py
│       ├── set_light.py
│       └── speak.py
├── config/                        # 配置文件
│   ├── computer.yaml
│   ├── phone.yaml
│   ├── speaker.yaml
│   ├── tv.yaml
│   └── light.yaml
├── skills/                        # Skill 定义
│   ├── __init__.py
│   ├── screen_display.py
│   ├── send_notification.py
│   ├── play_audio.py
│   ├── display_video.py
│   ├── toggle_light.py
│   └── set_brightness.py
├── scripts/
│   ├── run_mvp.sh                 # 一键启动
│   └── vpn/
│       └── start_vpn.sh
├── tests/
│   └── (单元测试)
├── requirements.txt
└── README.md
```

---

## Chunk 1: 项目基础设置

**目标:** 创建项目结构、安装依赖、验证 FastDDS 环境

### Task 1: 创建项目目录和依赖文件

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastdds>=2.14.0
pyyaml>=6.0
openai>=1.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

- [ ] **Step 2: 创建 pyproject.toml**

```toml
[project]
name = "dooz"
version = "0.1.0"
description = "AI-Friendly Hardware Module & System"
requires-python = ">=3.10"
dependencies = [
    "fastdds>=2.14.0",
    "pyyaml>=6.0",
    "openai>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 3: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 4: 验证 FastDDS 安装**

```bash
python -c "import fastdds; print(fastdds.__version__)"
```

Expected: 输出版本号，无报错

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pyproject.toml
git commit -m "feat: add project dependencies"
```

---

### Task 2: 创建核心目录结构

**Files:**
- Create: `core/__init__.py`
- Create: `client/__init__.py`
- Create: `brain/__init__.py`
- Create: `brain/tools/__init__.py`
- Create: `config/`
- Create: `skills/__init__.py`
- Create: `scripts/vpn/`
- Create: `tests/`

- [ ] **Step 1: 创建所有目录和 __init__.py**

```bash
mkdir -p core client brain/tools config skills scripts/vpn tests
touch core/__init__.py client/__init__.py brain/__init__.py brain/tools/__init__.py skills/__init__.py
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "feat: create project directory structure"
```

---

## Chunk 2: 核心类型定义

**目标:** 定义所有消息类型和数据结构

### Task 3: 定义消息类型

**Files:**
- Create: `core/types.py`
- Test: `tests/test_types.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_types.py
import pytest
from core.types import (
    DeviceAnnounce, DeviceInfo, BrainStatus, TaskRequest,
    TaskResponse, TaskDispatch, TaskNotify, ActorState
)

def test_device_announce_creation():
    info = DeviceInfo(
        device_id="test_001",
        name="Test Device",
        role="test",
        wisdom=50,
        output=True,
        skills=["skill1", "skill2"]
    )
    announce = DeviceAnnounce(device=info)
    assert announce.device.device_id == "test_001"
    assert announce.device.wisdom == 50

def test_brain_status_no_brain():
    status = BrainStatus(brain_id=None, reason="no_candidate")
    assert status.brain_id is None
    assert status.reason == "no_candidate"

def test_actor_state_operations():
    state = ActorState(device_id="test_001")
    assert state.current is None
    assert state.history == []
    
    state.update_on_receive("test_op")
    assert state.current == "test_op"
    
    state.update_on_complete(True)
    assert state.current is None
    assert "test_op" in state.history
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /Users/taoluo/projects/gcode/dooz
pytest tests/test_types.py -v
```

Expected: FAIL (ModuleNotFoundError: core.types)

- [ ] **Step 3: 实现 core/types.py**

```python
# core/types.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /Users/taoluo/projects/gcode/dooz
pytest tests/test_types.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/types.py tests/test_types.py
git commit -m "feat: add core message types"
```

---

## Chunk 3: 设备发现服务

**目标:** 实现基于 FastDDS 的设备发现功能

### Task 4: 实现 DiscoveryService

**Files:**
- Create: `core/discovery.py`
- Test: `tests/test_discovery.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_discovery.py
import pytest
from unittest.mock import Mock, MagicMock
from core.discovery import DiscoveryService
from core.types import DeviceInfo

@pytest.fixture
def mock_participant():
    participant = MagicMock()
    return participant

def test_discovery_service_init():
    device_info = DeviceInfo(
        device_id="test_001",
        name="Test",
        role="test",
        wisdom=50,
        output=True,
        skills=["skill1"]
    )
    # Will fail because DiscoveryService doesn't exist yet
    discovery = DiscoveryService(device_info, mock_participant)
    assert discovery.device_info.device_id == "test_001"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_discovery.py -v
```

Expected: FAIL (ModuleNotFoundError: core.discovery)

- [ ] **Step 3: 实现 discovery.py**

```python
# core/discovery.py
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
        logger.info(f"Announced presence: {self.device_info.device_id}")
        
    def _announce_offline(self):
        """广播设备离线"""
        msg = DeviceOffline(device_id=self.device_info.device_id)
        # TODO: Publish via FastDDS
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
        for device_id, last_time in self.list(self.last_heartbeat):
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_discovery.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/discovery.py tests/test_discovery.py
git commit -m "feat: add discovery service"
```

---

## Chunk 4: 大脑选举服务

**目标:** 实现基于 wisdom 值的脑选举逻辑

### Task 5: 实现 ElectionService

**Files:**
- Create: `core/election.py`
- Test: `tests/test_election.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_election.py
import pytest
from core.election import ElectionService
from core.types import DeviceInfo, BrainStatus

WISDOM_THRESHOLD = 50

def test_election_no_candidates():
    """测试无可用候选者"""
    devices = {}
    service = ElectionService(WISDOM_THRESHOLD)
    brain_id = service.elect_brain(devices)
    assert brain_id is None

def test_election_single_candidate():
    """测试单一候选者"""
    devices = {
        "device_001": DeviceInfo("device_001", "Test", "test", 90, True, [])
    }
    service = ElectionService(WISDOM_THRESHOLD)
    brain_id = service.elect_brain(devices)
    assert brain_id == "device_001"

def test_election_highest_wisdom():
    """测试最高 wisdom 获胜"""
    devices = {
        "device_001": DeviceInfo("device_001", "Test1", "test", 70, True, []),
        "device_002": DeviceInfo("device_002", "Test2", "test", 90, True, []),
        "device_003": DeviceInfo("device_003", "Test3", "test", 50, True, []),
    }
    service = ElectionService(WISDOM_THRESHOLD)
    brain_id = service.elect_brain(devices)
    assert brain_id == "device_002"  # wisdom=90

def test_election_below_threshold():
    """测试 wisdom 低于门槛"""
    devices = {
        "device_001": DeviceInfo("device_001", "Test", "test", 30, True, []),
    }
    service = ElectionService(WISDOM_THRESHOLD)
    brain_id = service.elect_brain(devices)
    assert brain_id is None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_election.py -v
```

Expected: FAIL (ModuleNotFoundError: core.election)

- [ ] **Step 3: 实现 election.py**

```python
# core/election.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_election.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/election.py tests/test_election.py
git commit -m "feat: add election service"
```

---

## Chunk 5: Actor State 管理

**目标:** 实现 Actor 状态机

### Task 6: 实现 ActorStateManager

**Files:**
- Create: `core/actor_state.py`
- Test: `tests/test_actor_state.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_actor_state.py
import pytest
from core.actor_state import ActorStateManager
from core.types import ActorState

def test_actor_state_init():
    manager = ActorStateManager("device_001")
    state = manager.get_state()
    assert state.device_id == "device_001"
    assert state.current is None
    assert state.history == []

def test_update_on_receive():
    manager = ActorStateManager("device_001")
    manager.update_on_receive("play_video")
    state = manager.get_state()
    assert state.current == "play_video"

def test_update_on_complete():
    manager = ActorStateManager("device_001")
    manager.update_on_receive("play_video")
    manager.update_on_complete(True)
    state = manager.get_state()
    assert state.current is None
    assert "play_video" in state.history

def test_multiple_operations():
    manager = ActorStateManager("device_001")
    manager.update_on_receive("op1")
    manager.update_on_complete(True)
    manager.update_on_receive("op2")
    manager.update_on_complete(True)
    state = manager.get_state()
    assert state.history == ["op1", "op2"]
    assert state.current is None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_actor_state.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: 实现 actor_state.py**

```python
# core/actor_state.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_actor_state.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/actor_state.py tests/test_actor_state.py
git commit -m "feat: add actor state manager"
```

---

## Chunk 6: 消息传输服务

**目标:** 实现基于 FastDDS 的消息发布/订阅

### Task 7: 实现 TransportService

**Files:**
- Create: `core/transport.py`
- Test: `tests/test_transport.py`

- [ ] **Step 1: 编写测试 (简化版)**

```python
# tests/test_transport.py
import pytest
from unittest.mock import MagicMock
from core.transport import TransportService

def test_transport_init():
    """测试传输服务初始化"""
    participant = MagicMock()
    transport = TransportService(participant, "device_001")
    assert transport.device_id == "device_001"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_transport.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 transport.py (MVP 简化版)**

```python
# core/transport.py
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_transport.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/transport.py tests/test_transport.py
git commit -m "feat: add transport service"
```

---

## Chunk 7: Client 基类

**目标:** 实现 Client 基类，整合所有服务

### Task 8: 实现 Client 基类

**Files:**
- Create: `client/base.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_client.py
import pytest
from unittest.mock import MagicMock
from client.base import Client
from core.types import DeviceInfo

@pytest.fixture
def client_config():
    return DeviceInfo(
        device_id="test_001",
        name="Test Device",
        role="test",
        wisdom=50,
        output=True,
        skills=["skill1"]
    )

def test_client_init(client_config):
    client = Client(client_config)
    assert client.device_id == "test_001"
    assert client.wisdom == 50
    assert client.output is True
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_client.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 client/base.py**

```python
# client/base.py
import logging
import yaml
from typing import Optional
from pathlib import Path

from core.types import DeviceInfo, TaskRequest, TaskDispatch, TaskResponse
from core.discovery import DiscoveryService
from core.election import ElectionService
from core.transport import TransportService
from core.actor_state import ActorStateManager

logger = logging.getLogger(__name__)


class Client:
    """设备客户端基类"""
    
    def __init__(self, config: DeviceInfo):
        self.config = config
        self.device_id = config.device_id
        self.wisdom = config.wisdom
        self.output = config.output
        self.skills = config.skills
        
        # 服务
        self.participant = None  # FastDDS participant
        self.discovery = DiscoveryService(config, self.participant)
        self.election = ElectionService(wisdom_threshold=50)
        self.transport = TransportService(self.participant, self.device_id)
        self.actor_state = ActorStateManager(self.device_id)
        
        self._is_running = False
        
    @classmethod
    def from_yaml(cls, config_path: str) -> 'Client':
        """从 YAML 配置文件创建 Client"""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        device_data = config_data['device']
        config = DeviceInfo(
            device_id=device_data['id'],
            name=device_data['name'],
            role=device_data['role'],
            wisdom=device_data['wisdom'],
            output=device_data['output'],
            skills=[s['name'] for s in device_data.get('skills', [])]
        )
        return cls(config)
        
    def start(self):
        """启动客户端"""
        logger.info(f"Starting client: {self.device_id}")
        self._is_running = True
        
        # 初始化 FastDDS
        self._init_dds()
        
        # 启动服务
        self.discovery.start()
        self._setup_subscriptions()
        
        logger.info(f"Client {self.device_id} started")
        
    def stop(self):
        """停止客户端"""
        logger.info(f"Stopping client: {self.device_id}")
        self._is_running = False
        self.discovery.stop()
        
    def _init_dds(self):
        """初始化 FastDDS"""
        # TODO: 初始化 FastDDS participant
        logger.info("FastDDS participant initialized (placeholder)")
        
    def _setup_subscriptions(self):
        """设置消息订阅"""
        topics = [
            "dooz/device/announce",
            "dooz/device/heartbeat",
            "dooz/device/offline",
            "dooz/brain/status",
            "dooz/task/dispatch",
            "dooz/task/notify",
        ]
        for topic in topics:
            self.transport.create_subscriber(topic, self._handle_message)
            
    def _handle_message(self, message: dict):
        """处理收到的消息"""
        msg_type = message.get('msg_type', '')
        
        if msg_type == 'device/announce':
            self.discovery.on_device_announce(message)
            self._update_brain_election()
            
        elif msg_type == 'device/offline':
            self.discovery.on_device_offline(message)
            self._update_brain_election()
            
        elif msg_type == 'brain/status':
            self._on_brain_status(message)
            
        elif msg_type == 'task/dispatch':
            self._on_task_dispatch(message)
            
        elif msg_type == 'task/notify':
            self._on_task_notify(message)
            
    def _update_brain_election(self):
        """更新大脑选举"""
        online_devices = self.discovery.get_online_devices()
        # 加入自己
        online_devices[self.device_id] = self.config
        
        new_brain_id = self.election.elect_brain(online_devices)
        brain_status = self.election.get_brain_status()
        self._broadcast_brain_status(brain_status)
        
    def _broadcast_brain_status(self, status):
        """广播大脑状态"""
        import time
        msg = {
            'msg_type': 'brain/status',
            'brain_id': status.brain_id,
            'wisdom_threshold': status.wisdom_threshold,
            'reason': status.reason,
            'timestamp': time.time()
        }
        self.transport.publish('dooz/brain/status', msg)
        
    def send_task_request(self, text: str):
        """发送任务请求"""
        import uuid, time
        request = {
            'msg_type': 'task/request',
            'request_id': str(uuid.uuid4()),
            'text': text,
            'requester_id': self.device_id,
            'timestamp': time.time()
        }
        self.transport.publish('dooz/task/request', request)
        self.actor_state.update_on_receive(f"request:{text}")
        
    def _on_brain_status(self, message: dict):
        """处理大脑状态更新"""
        logger.info(f"Brain status: {message.get('brain_id')} ({message.get('reason')})")
        
    def _on_task_dispatch(self, message: dict):
        """处理任务分发"""
        if message.get('executor_id') != self.device_id:
            return
            
        skill_name = message.get('skill_name')
        params = message.get('parameters', {})
        
        logger.info(f"Received task: {skill_name} with params {params}")
        
        # 更新 actor state
        self.actor_state.update_on_receive(skill_name)
        
        # 执行 skill
        result = self._execute_skill(skill_name, params)
        
        # 发送响应
        response = {
            'msg_type': 'task/response',
            'request_id': message.get('request_id'),
            'success': result['success'],
            'result': result.get('message', ''),
            'executor_id': self.device_id,
            'timestamp': time.time()
        }
        self.transport.publish('dooz/task/response', response)
        
        # 更新 actor state
        self.actor_state.update_on_complete(result['success'])
        
    def _on_task_notify(self, message: dict):
        """处理任务通知"""
        if not self.output:
            return
            
        logger.info(f"NOTIFICATION: {message.get('message')}")
        self.actor_state.update_on_receive("notify")
        self.actor_state.update_on_complete(True)
        
    def _execute_skill(self, skill_name: str, params: dict) -> dict:
        """执行 skill (由子类重写)"""
        logger.info(f"Executing skill: {skill_name}")
        return {'success': True, 'message': f'Skill {skill_name} executed'}
        
    def get_status(self) -> dict:
        """获取客户端状态"""
        return {
            'device_id': self.device_id,
            'wisdom': self.wisdom,
            'output': self.output,
            'skills': self.skills,
            'is_brain': self.election.is_brain(self.device_id),
            'actor_state': {
                'history': self.actor_state.get_history(),
                'current': self.actor_state.get_current()
            }
        }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/test_client.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add client/base.py tests/test_client.py
git commit -m "feat: add client base class"
```

---

## Chunk 8: Skill 定义

**目标:** 定义每个设备的 skill

### Task 9: 实现 Skills

**Files:**
- Create: `skills/__init__.py`
- Create: `skills/screen_display.py`
- Create: `skills/send_notification.py`
- Create: `skills/play_audio.py`
- Create: `skills/display_video.py`
- Create: `skills/toggle_light.py`
- Create: `skills/set_brightness.py`

- [ ] **Step 1: 创建 skills/__init__.py**

```python
# skills/__init__.py
"""Skill 定义模块"""

from .screen_display import ScreenDisplaySkill
from .send_notification import SendNotificationSkill
from .play_audio import PlayAudioSkill
from .display_video import DisplayVideoSkill
from .toggle_light import ToggleLightSkill
from .set_brightness import SetBrightnessSkill

SKILL_REGISTRY = {
    'screen_display': ScreenDisplaySkill(),
    'send_notification': SendNotificationSkill(),
    'play_audio': PlayAudioSkill(),
    'display_video': DisplayVideoSkill(),
    'toggle_light': ToggleLightSkill(),
    'set_brightness': SetBrightnessSkill(),
}

def get_skill(skill_name: str):
    """获取 skill 实例"""
    return SKILL_REGISTRY.get(skill_name)
```

- [ ] **Step 2: 创建各个 skill 文件**

```python
# skills/screen_display.py
import logging

logger = logging.getLogger(__name__)

class ScreenDisplaySkill:
    name = "screen_display"
    
    def execute(self, **params) -> dict:
        message = params.get('message', '')
        logger.info(f"[ScreenDisplay] Displaying: {message}")
        return {'success': True, 'message': f'Screen: {message}'}
```

```python
# skills/send_notification.py
import logging

logger = logging.getLogger(__name__)

class SendNotificationSkill:
    name = "send_notification"
    
    def execute(self, **params) -> dict:
        message = params.get('message', '')
        logger.info(f"[Notification] Sending: {message}")
        return {'success': True, 'message': f'Notified: {message}'}
```

```python
# skills/play_audio.py
import logging

logger = logging.getLogger(__name__)

class PlayAudioSkill:
    name = "play_audio"
    
    def execute(self, **params) -> dict:
        message = params.get('message', '')
        audio_type = params.get('type', 'speech')
        
        if audio_type == 'speech':
            logger.info(f"[PlayAudio] Speaking: {message}")
        else:
            logger.info(f"[PlayAudio] Playing: {message}")
            
        return {'success': True, 'message': f'Audio: {message}'}
```

```python
# skills/display_video.py
import logging

logger = logging.getLogger(__name__)

class DisplayVideoSkill:
    name = "display_video"
    
    def execute(self, **params) -> dict:
        url = params.get('url', '')
        title = params.get('title', 'Video')
        logger.info(f"[DisplayVideo] Playing: {title} from {url}")
        return {'success': True, 'message': f'Playing: {title}'}
```

```python
# skills/toggle_light.py
import logging

logger = logging.getLogger(__name__)

class ToggleLightSkill:
    name = "toggle_light"
    
    def execute(self, **params) -> dict:
        state = params.get('state', 'toggle')
        logger.info(f"[ToggleLight] Light turned {state}")
        return {'success': True, 'message': f'Light: {state}'}
```

```python
# skills/set_brightness.py
import logging

logger = logging.getLogger(__name__)

class SetBrightnessSkill:
    name = "set_brightness"
    
    def execute(self, **params) -> dict:
        level = int(params.get('level', 100))
        logger.info(f"[SetBrightness] Brightness set to {level}%")
        return {'success': True, 'message': f'Brightness: {level}%'}
```

- [ ] **Step 3: Commit**

```bash
git add skills/
git commit -m "feat: add skill implementations"
```

---

## Chunk 9: 配置文件

**目标:** 创建 5 个设备的配置文件

### Task 10: 创建配置文件

**Files:**
- Create: `config/computer.yaml`
- Create: `config/phone.yaml`
- Create: `config/speaker.yaml`
- Create: `config/tv.yaml`
- Create: `config/light.yaml`

- [ ] **Step 1: 创建 computer.yaml**

```yaml
# config/computer.yaml
device:
  id: "computer_001"
  name: "Computer"
  role: "computer"
  wisdom: 90
  output: true
  skills:
    - name: "screen_display"
    - name: "execute_command"
```

- [ ] **Step 2: 创建 phone.yaml**

```yaml
# config/phone.yaml
device:
  id: "phone_001"
  name: "Phone"
  role: "phone"
  wisdom: 70
  output: true
  skills:
    - name: "send_notification"
    - name: "vibrate"
```

- [ ] **Step 3: 创建 speaker.yaml**

```yaml
# config/speaker.yaml
device:
  id: "speaker_001"
  name: "Speaker"
  role: "speaker"
  wisdom: 50
  output: true
  skills:
    - name: "play_audio"
    - name: "set_volume"
```

- [ ] **Step 4: 创建 tv.yaml**

```yaml
# config/tv.yaml
device:
  id: "tv_001"
  name: "TV"
  role: "tv"
  wisdom: 60
  output: true
  skills:
    - name: "display_video"
    - name: "display_image"
```

- [ ] **Step 5: 创建 light.yaml**

```yaml
# config/light.yaml
device:
  id: "light_001"
  name: "Light"
  role: "light"
  wisdom: 30
  output: false
  skills:
    - name: "toggle_light"
    - name: "set_brightness"
```

- [ ] **Step 6: Commit**

```bash
git add config/
git commit -m "feat: add device configuration files"
```

---

## Chunk 10: Brain 扩展

**目标:** 实现 Brain 客户端，包含 LLM 和工具注册

### Task 11: 实现 Brain 功能

**Files:**
- Create: `brain/llm_client.py`
- Create: `brain/tool_registry.py`
- Create: `client/brain.py`
- Test: `tests/test_brain.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_brain.py
import pytest
from unittest.mock import MagicMock, patch
from brain.tool_registry import ToolRegistry
from brain.tools.search_movie import SearchMovieTool

def test_tool_registry_register():
    registry = ToolRegistry()
    tool = SearchMovieTool()
    registry.register("search_movie", tool)
    assert "search_movie" in registry.list_tools()

def test_tool_registry_execute():
    registry = ToolRegistry()
    tool = SearchMovieTool()
    registry.register("search_movie", tool)
    result = registry.execute("search_movie", actor="Jackie Chan")
    assert result is not None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/test_brain.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 tool_registry.py**

```python
# brain/tool_registry.py
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册表 - 管理大脑可用的工具"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        
    def register(self, name: str, tool: Callable):
        """注册工具"""
        self._tools[name] = tool
        logger.info(f"Tool registered: {name}")
        
    def execute(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        if tool_name not in self._tools:
            logger.error(f"Tool not found: {tool_name}")
            return {'success': False, 'error': f'Tool {tool_name} not found'}
            
        try:
            result = self._tools[tool_name](**kwargs)
            logger.info(f"Tool executed: {tool_name} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {'success': False, 'error': str(e)}
            
    def list_tools(self) -> list:
        """列出所有工具"""
        return list(self._tools.keys())
```

- [ ] **Step 4: 实现内置工具**

```python
# brain/tools/__init__.py
from .search_movie import search_movie_tool
from .play_video import play_video_tool
from .set_light import set_light_tool
from .speak import speak_tool
```

```python
# brain/tools/search_movie.py
import logging

logger = logging.getLogger(__name__)

def search_movie_tool(actor: str = None, genre: str = None) -> dict:
    """搜索电影工具 (MVP: 模拟返回)"""
    logger.info(f"[Tool] Searching movie: actor={actor}, genre={genre}")
    
    # MVP: 模拟返回结果
    if actor and "成龙" in actor:
        result = {
            'success': True,
            'title': '功夫瑜伽',
            'url': 'https://example.com/movie/kung_fu_yoga.mp4',
            'actor': '成龙'
        }
    elif actor:
        result = {
            'success': True,
            'title': f'{actor}电影',
            'url': f'https://example.com/movie/{actor}.mp4'
        }
    else:
        result = {'success': True, 'title': '默认电影', 'url': 'https://example.com/movie/default.mp4'}
        
    return result
```

```python
# brain/tools/play_video.py
import logging

logger = logging.getLogger(__name__)

def play_video_tool(url: str, title: str = None) -> dict:
    """播放视频工具"""
    logger.info(f"[Tool] Playing video: {title} from {url}")
    return {'success': True, 'message': f'Playing: {title or url}'}
```

```python
# brain/tools/set_light.py
import logging

logger = logging.getLogger(__name__)

def set_light_tool(level: int = 100, state: str = None) -> dict:
    """设置灯光工具"""
    if state:
        logger.info(f"[Tool] Light state: {state}")
        return {'success': True, 'message': f'Light: {state}'}
    logger.info(f"[Tool] Light brightness: {level}%")
    return {'success': True, 'message': f'Brightness: {level}%'}
```

```python
# brain/tools/speak.py
import logging

logger = logging.getLogger(__name__)

def speak_tool(message: str) -> dict:
    """语音通知工具"""
    logger.info(f"[Tool] Speaking: {message}")
    return {'success': True, 'message': f'Speaking: {message}'}
```

- [ ] **Step 5: 实现 LLM 客户端 (简化版)**

```python
# brain/llm_client.py
"""
LLM 客户端 (MVP: 简化版)
生产环境应使用真实 OpenAI API
"""
import logging
import json

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端 - 理解用户意图并生成执行计划"""
    
    SYSTEM_PROMPT = """你是一个智能家居助手的大脑。你需要：
1. 理解用户的自然语言请求
2. 从可用工具中选择合适的工具来完成任务
3. 生成执行计划

可用工具：
- search_movie: 搜索电影 (参数: actor, genre)
- play_video: 在电视播放视频 (参数: url, title)
- set_light: 设置灯光 (参数: level, state)
- speak_text: 语音通知 (参数: message)

场景1: "放一部成龙的喜剧片"
计划: [search_movie(actor="成龙", genre="喜剧"), play_video, set_light(level=30), speak_text]

场景2: "我要吃晚饭了"
计划: [set_light(level=30), play_audio(type="background_music"), set_light(level=50)]

用户请求: {user_input}

请输出 JSON 格式的执行计划："""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        
    def understand(self, user_input: str) -> dict:
        """理解用户输入"""
        logger.info(f"[LLM] Understanding: {user_input}")
        
        # MVP: 简化实现，基于规则匹配
        if "电影" in user_input or "喜剧片" in user_input:
            if "成龙" in user_input:
                return {
                    'intent': 'play_movie',
                    'params': {'actor': '成龙', 'genre': '喜剧'}
                }
            return {'intent': 'play_movie', 'params': {}}
            
        if "晚饭" in user_input or "吃饭" in user_input or "晚餐" in user_input:
            return {'intent': 'dinner_mode', 'params': {}}
            
        return {'intent': 'unknown', 'params': {}}
        
    def plan(self, intent: dict, available_tools: list) -> list:
        """生成执行计划"""
        logger.info(f"[LLM] Planning for intent: {intent}")
        
        if intent['intent'] == 'play_movie':
            # 1. 先搜索电影
            movie = self._call_tool('search_movie', **intent['params'])
            
            # 2. 然后播放、调光、通知
            plan = [
                {'tool': 'play_video', 'params': {'url': movie.get('url'), 'title': movie.get('title')}},
                {'tool': 'set_light', 'params': {'level': 30}},
                {'tool': 'speak_text', 'params': {'message': f'《{movie.get("title", "电影")}》已经为您准备好'}}
            ]
            
        elif intent['intent'] == 'dinner_mode':
            plan = [
                {'tool': 'set_light', 'params': {'level': 30}},
                {'tool': 'play_audio', 'params': {'type': 'background_music', 'message': '轻柔背景音乐'}},
                {'tool': 'set_light_tv', 'params': {'level': 50}}
            ]
            
        else:
            plan = []
            
        return plan
        
    def _call_tool(self, tool_name: str, **kwargs) -> dict:
        """调用工具"""
        # MVP: 简化实现
        if tool_name == 'search_movie':
            actor = kwargs.get('actor', '')
            if "成龙" in actor:
                return {'title': '功夫瑜伽', 'url': 'https://example.com/kung_fu_yoga.mp4'}
            return {'title': '电影', 'url': 'https://example.com/movie.mp4'}
        return {}
```

- [ ] **Step 6: 实现 Brain Client**

```python
# client/brain.py
import logging
from client.base import Client
from brain.llm_client import LLMClient
from brain.tool_registry import ToolRegistry
from brain.tools import search_movie_tool, play_video_tool, set_light_tool, speak_tool

logger = logging.getLogger(__name__)


class BrainClient(Client):
    """大脑客户端 - 具备 LLM 理解和任务规划能力"""
    
    def __init__(self, config, llm_api_key: str = None):
        super().__init__(config)
        self.llm = LLMClient(api_key=llm_api_key)
        self.tool_registry = ToolRegistry()
        self._register_tools()
        
    def _register_tools(self):
        """注册可用工具"""
        self.tool_registry.register('search_movie', search_movie_tool)
        self.tool_registry.register('play_video', play_video_tool)
        self.tool_registry.register('set_light', set_light_tool)
        self.tool_registry.register('speak_text', speak_tool)
        
    def on_task_request(self, message: dict):
        """处理任务请求 (大脑专属)"""
        if not self.election.is_brain(self.device_id):
            logger.warning("Not brain, ignoring task request")
            return
            
        user_input = message.get('text', '')
        request_id = message.get('request_id', '')
        requester_id = message.get('requester_id', '')
        
        logger.info(f"[Brain] Processing request: {user_input}")
        
        # 1. 理解意图
        intent = self.llm.understand(user_input)
        
        # 2. 生成计划
        plan = self.llm.plan(intent, self.tool_registry.list_tools())
        
        # 3. 执行计划
        results = []
        for step in plan:
            tool_name = step.get('tool')
            params = step.get('params', {})
            
            result = self.tool_registry.execute(tool_name, **params)
            results.append({'tool': tool_name, 'result': result})
            
            # 调度到对应设备执行
            self._dispatch_to_device(tool_name, params, request_id)
            
        # 4. 通知用户
        self._notify_user(results, request_id)
        
    def _dispatch_to_device(self, tool_name: str, params: dict, request_id: str):
        """调度任务到对应设备"""
        # 根据 skill 名称找到执行者
        executor_id = self._find_executor(tool_name)
        
        if executor_id:
            import time
            dispatch_msg = {
                'msg_type': 'task/dispatch',
                'request_id': request_id,
                'skill_name': self._tool_to_skill(tool_name),
                'parameters': params,
                'executor_id': executor_id,
                'timestamp': time.time()
            }
            self.transport.publish('dooz/task/dispatch', dispatch_msg)
            logger.info(f"[Brain] Dispatched {tool_name} to {executor_id}")
            
    def _find_executor(self, tool_name: str) -> str:
        """找到能执行工具的设备"""
        skill_name = self._tool_to_skill(tool_name)
        
        # 获取在线设备
        devices = self.discovery.get_online_devices()
        devices[self.device_id] = self.config
        
        # 查找有对应 skill 的设备
        for device_id, device in devices.items():
            if skill_name in device.skills:
                return device_id
                
        return None
        
    def _tool_to_skill(self, tool_name: str) -> str:
        """工具名转 skill 名"""
        mapping = {
            'play_video': 'display_video',
            'set_light': 'set_brightness',
            'speak_text': 'play_audio',
            'play_audio': 'play_audio',
        }
        return mapping.get(tool_name, tool_name)
        
    def _notify_user(self, results: list, request_id: str):
        """通知用户结果"""
        import time
        
        # 找到有 output 能力的设备
        devices = self.discovery.get_online_devices()
        devices[self.device_id] = self.config
        
        output_devices = [d for d in devices.values() if d.output]
        
        if not output_devices:
            logger.warning("No output device available")
            return
            
        # 选择一个 output 设备 (简化: 选第一个)
        notify_device = output_devices[0].device_id
        
        # 构建通知消息
        notify_msg = {
            'msg_type': 'task/notify',
            'request_id': request_id,
            'message': '任务已完成',
            'source_id': self.device_id,
            'timestamp': time.time()
        }
        
        self.transport.publish('dooz/task/notify', notify_msg)
        logger.info(f"[Brain] Notified user via {notify_device}")
```

- [ ] **Step 7: 运行测试**

```bash
pytest tests/test_brain.py -v
```

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add brain/ client/brain.py tests/test_brain.py
git commit -m "feat: add brain client with LLM and tools"
```

---

## Chunk 11: 主入口和运行脚本

**目标:** 创建主入口和运行脚本

### Task 12: 创建主入口

**Files:**
- Create: `client/main.py`
- Create: `scripts/run_mvp.sh`
- Create: `scripts/vpn/start_vpn.sh`

- [ ] **Step 1: 创建 client/main.py**

```python
# client/main.py
"""Client 主入口"""
import argparse
import logging
import sys
import time

from client.base import Client
from client.brain import BrainClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='dooz Client')
    parser.add_argument('--config', required=True, help='Path to config YAML')
    parser.add_argument('--brain', action='store_true', help='Run as brain (with LLM)')
    parser.add_argument('--llm-key', help='OpenAI API key (if brain mode)')
    args = parser.parse_args()
    
    logger.info(f"Loading config from: {args.config}")
    
    if args.brain:
        logger.info("Starting in BRAIN mode")
        client = BrainClient.from_yaml(args.config)
    else:
        client = Client.from_yaml(args.config)
        
    try:
        client.start()
        logger.info(f"Client {client.device_id} started successfully")
        logger.info(f"Status: {client.get_status()}")
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        client.stop()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 创建 run_mvp.sh**

```bash
#!/bin/bash
# scripts/run_mvp.sh - 一键启动 5 个客户端

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_DIR/config"

echo "Starting dooz MVP..."

# 检查配置文件
for config in computer phone speaker tv light; do
    if [ ! -f "$CONFIG_DIR/${config}.yaml" ]; then
        echo "Error: Config file not found: $CONFIG_DIR/${config}.yaml"
        exit 1
    fi
done

# 启动 5 个客户端 (后台运行)
echo "Starting Computer (Brain)..."
python -m client.main --config "$CONFIG_DIR/computer.yaml" --brain &
PID_COMPUTER=$!

sleep 1

echo "Starting Phone..."
python -m client.main --config "$CONFIG_DIR/phone.yaml" &
PID_PHONE=$!

sleep 1

echo "Starting Speaker..."
python -m client.main --config "$CONFIG_DIR/speaker.yaml" &
PID_SPEAKER=$!

sleep 1

echo "Starting TV..."
python -m client.main --config "$CONFIG_DIR/tv.yaml" &
PID_TV=$!

sleep 1

echo "Starting Light..."
python -m client.main --config "$CONFIG_DIR/light.yaml" &
PID_LIGHT=$!

echo ""
echo "All clients started!"
echo "Computer PID: $PID_COMPUTER"
echo "Phone PID: $PID_PHONE"
echo "Speaker PID: $PID_SPEAKER"
echo "TV PID: $PID_TV"
echo "Light PID: $PID_LIGHT"
echo ""
echo "Press Ctrl+C to stop all clients"

# 等待中断
trap "kill $PID_COMPUTER $PID_PHONE $PID_SPEAKER $PID_TV $PID_LIGHT 2>/dev/null; exit" INT TERM

wait
```

- [ ] **Step 3: 创建 VPN 启动脚本**

```bash
#!/bin/bash
# scripts/vpn/start_vpn.sh - 启动 Headscale VPN

set -e

echo "Starting Headscale VPN..."

# 检查 docker 是否运行
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# 检查 headscale 是否已存在
if docker ps -a --format '{{.Names}}' | grep -q "^headscale$"; then
    echo "Headscale container already exists"
    
    if docker ps --format '{{.Names}}' | grep -q "^headscale$"; then
        echo "Headscale is already running"
    else
        echo "Starting existing Headscale container..."
        docker start headscale
    fi
else
    echo "Creating and starting Headscale container..."
    docker run -d --name headscale \
        --volume "$(pwd)/headscale:/var/lib/headscale" \
        --volume "$(pwd)/headscale/config.yaml:/etc/headscale.yml" \
        -p 8080:8080 \
        headscale/headscale \
        serve &
        
    sleep 3
fi

echo ""
echo "Headscale started!"
echo "Access UI at: http://localhost:8080"
echo ""
echo "To connect clients, run:"
echo "  tailscaled --tun=headscale0 --login-server=http://localhost:8080"
```

- [ ] **Step 4: 设置执行权限**

```bash
chmod +x scripts/run_mvp.sh
chmod +x scripts/vpn/start_vpn.sh
```

- [ ] **Step 5: Commit**

```bash
git add client/main.py scripts/
git commit -m "feat: add main entry point and run scripts"
```

---

## Chunk 12: 集成测试

**目标:** 验证两个场景能正确执行

### Task 13: 场景测试

**Files:**
- Create: `tests/test_scenario1.py`
- Create: `tests/test_scenario2.py`

- [ ] **Step 1: 创建场景测试**

```python
# tests/test_scenario1.py
"""
场景 1 测试: 播放成龙喜剧片
预期: TV 播放, Light 调暗, Speaker 通知
"""
import pytest
from unittest.mock import MagicMock, patch
from client.brain import BrainClient
from core.types import DeviceInfo

@pytest.fixture
def brain_client():
    config = DeviceInfo(
        device_id="computer_001",
        name="Computer",
        role="computer",
        wisdom=90,
        output=True,
        skills=["screen_display", "execute_command"]
    )
    with patch('client.base.DiscoveryService'):
        with patch('client.base.TransportService'):
            client = BrainClient(config)
            client.election.current_brain_id = "computer_001"
            return client

def test_scene1_intent_recognition(brain_client):
    """测试场景1: 意图识别"""
    intent = brain_client.llm.understand("放一部成龙的喜剧片")
    assert intent['intent'] == 'play_movie'
    assert 'actor' in intent['params']

def test_scene1_plan_generation(brain_client):
    """测试场景1: 计划生成"""
    intent = {'intent': 'play_movie', 'params': {'actor': '成龙', 'genre': '喜剧'}}
    plan = brain_client.llm.plan(intent, [])
    
    assert len(plan) >= 3  # play_video, set_light, speak_text
    
    tools = [step['tool'] for step in plan]
    assert 'play_video' in tools
    assert 'set_light' in tools
    assert 'speak_text' in tools
```

```python
# tests/test_scenario2.py
"""
场景 2 测试: 晚餐氛围
预期: Light 30%, Speaker 播放音乐, TV 50%
"""
import pytest
from client.brain import BrainClient
from core.types import DeviceInfo

@pytest.fixture
def brain_client():
    config = DeviceInfo(
        device_id="computer_001",
        name="Computer",
        role="computer",
        wisdom=90,
        output=True,
        skills=["screen_display", "execute_command"]
    )
    with patch('client.base.DiscoveryService'):
        with patch('client.base.TransportService'):
            client = BrainClient(config)
            client.election.current_brain_id = "computer_001"
            return client

def test_scene2_intent_recognition(brain_client):
    """测试场景2: 意图识别"""
    intent = brain_client.llm.understand("我要吃晚饭了")
    assert intent['intent'] == 'dinner_mode'

def test_scene2_plan_generation(brain_client):
    """测试场景2: 计划生成"""
    intent = {'intent': 'dinner_mode', 'params': {}}
    plan = brain_client.llm.plan(intent, [])
    
    assert len(plan) >= 2  # set_light, play_audio, set_light_tv
    
    tools = [step['tool'] for step in plan]
    assert 'set_light' in tools
    assert 'play_audio' in tools
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/test_scenario1.py tests/test_scenario2.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_scenario1.py tests/test_scenario2.py
git commit -m "test: add scenario tests"
```

---

## 总结

**实现计划包含以下 chunks:**
1. 项目基础设置 (requirements.txt, 目录结构)
2. 核心类型定义 (core/types.py)
3. 设备发现服务 (core/discovery.py)
4. 大脑选举服务 (core/election.py)
5. Actor State 管理 (core/actor_state.py)
6. 消息传输服务 (core/transport.py)
7. Client 基类 (client/base.py)
8. Skill 定义 (skills/)
9. 配置文件 (config/)
10. Brain 扩展 (brain/, client/brain.py)
11. 主入口和脚本 (client/main.py, scripts/)
12. 集成测试 (tests/)

**总任务数:** 约 40-50 个步骤

**预期产出:**
- 完整的 MVP 代码
- 单元测试覆盖
- 可运行的演示脚本

---

**Plan complete and saved to `docs/superpowers/plans/2026-03-14-dooz-mvp-implementation-plan.md`. Ready to execute?**

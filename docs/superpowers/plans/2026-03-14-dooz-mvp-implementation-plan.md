# dooz MVP Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 dooz MVP - 分布式多智能体协作系统，包含 Server 端 (API, Auth, LLM, Chat, FastDDS Gateway) 和 Client Python。

**Architecture:** 
- Server: FastAPI + FastDDS (per tenant) + OAuth2
- Client: Python Agent 通过 WebSocket 连接到 Server
- 消息模式: Pub/Sub via FastDDS Topics

**Tech Stack:** Python 3.10+, FastAPI, FastDDS, OAuth2, WebSocket

---

## 阶段划分

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| Phase 1 | 项目结构 + Server 基础 (types, config) | P0 |
| Phase 2 | Server API + Auth (OAuth2) | P0 |
| Phase 3 | FastDDS Gateway + Tenant Manager | P0 |
| Phase 4 | LLM Gateway + Context 组装 | P0 |
| Phase 5 | Chat Session Manager | P1 |
| Phase 6 | Client Python Core | P0 |
| Phase 7 | Client Skills | P1 |

---

## Chunk 1: 项目结构初始化

### Task 1.1: 创建目录结构

**Files:**
- Create: `server/`
- Create: `server/__init__.py`
- Create: `server/config/`
- Create: `server/api/`
- Create: `server/core/`
- Create: `server/tenant/`
- Create: `server/llm/`
- Create: `server/chat/`
- Create: `server/coordinator/`
- Create: `server/transport/`
- Create: `client/python/`
- Create: `client/python/core/`
- Create: `client/python/llm/`
- Create: `client/python/skills/`
- Create: `client/python/config/devices/`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p server/{api,core,tenant,llm,chat,coordinator,transport,config}
mkdir -p client/python/{core,llm,skills,config/devices}
```

- [ ] **Step 2: 验证目录创建**

Run: `find . -type d -name "server" -o -name "client" | head -10`
Expected: 列出所有新目录

- [ ] **Step 3: Commit**

```bash
git add server/ client/python/
git commit -m "chore: create project directory structure"
```

---

### Task 1.2: Server 基础类型定义

**Files:**
- Create: `server/core/__init__.py`
- Create: `server/core/types.py`
- Create: `server/core/protocol.py`
- Create: `server/core/exceptions.py`

- [ ] **Step 1: 创建 server/core/__init__.py**

```python
"""dooz server core package."""

from .types import (
    DeviceInfo,
    TaskRequest,
    TaskDispatch,
    TaskResponse,
    TaskCollaborate,
    TaskTimeout,
    TaskNotify,
    DeviceAnnounce,
    DeviceHeartbeat,
    DeviceOffline,
)
from .protocol import MsgType, TopicPrefix
from .exceptions import (
    DoozException,
    AuthError,
    TenantNotFoundError,
    DeviceNotFoundError,
    LLMError,
)

__all__ = [
    "DeviceInfo",
    "TaskRequest", 
    "TaskDispatch",
    "TaskResponse",
    "TaskCollaborate",
    "TaskTimeout",
    "TaskNotify",
    "DeviceAnnounce",
    "DeviceHeartbeat",
    "DeviceOffline",
    "MsgType",
    "TopicPrefix",
    "DoozException",
    "AuthError",
    "TenantNotFoundError", 
    "DeviceNotFoundError",
    "LLMError",
]
```

- [ ] **Step 2: 创建 server/core/protocol.py**

```python
"""消息协议常量定义."""

from enum import Enum


class MsgType(Enum):
    """消息类型."""
    DEVICE_ANNOUNCE = "device/announce"
    DEVICE_HEARTBEAT = "device/heartbeat"
    DEVICE_OFFLINE = "device/offline"
    TASK_REQUEST = "task/request"
    TASK_DISPATCH = "task/dispatch"
    TASK_RESPONSE = "task/response"
    TASK_COLLABORATE = "task/collaborate"
    TASK_TIMEOUT = "task/timeout"
    TASK_NOTIFY = "task/notify"


class TopicPrefix:
    """Topic 前缀常量."""
    BASE = "dooz"
    
    @staticmethod
    def for_tenant(tenant_id: str) -> str:
        """获取租户的 Topic 前缀."""
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
    def task_collaborate(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/task/collaborate"
    
    @staticmethod
    def task_timeout(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/task/timeout"
    
    @staticmethod
    def task_notify(tenant_id: str) -> str:
        return f"{TopicPrefix.for_tenant(tenant_id)}/task/notify"
```

- [ ] **Step 3: 创建 server/core/exceptions.py**

```python
"""异常定义."""


class DoozException(Exception):
    """基础异常."""
    pass


class AuthError(DoozException):
    """认证错误."""
    pass


class TenantNotFoundError(DoozException):
    """租户不存在."""
    pass


class DeviceNotFoundError(DoozException):
    """设备不存在."""
    pass


class LLMError(DoozException):
    """LLM 请求错误."""
    pass


class SessionNotFoundError(DoozException):
    """Session 不存在."""
    pass


class TaskTimeoutError(DoozException):
    """任务超时."""
    pass
```

- [ ] **Step 4: 创建 server/core/types.py**

```python
"""消息类型定义."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import time
import uuid


@dataclass
class DeviceInfo:
    """设备信息."""
    device_id: str
    name: str
    role: str
    wisdom: int
    output: bool
    llm_enabled: bool = False
    skills: List[str] = field(default_factory=list)
    tenant_id: str = ""
    
    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "role": self.role,
            "wisdom": self.wisdom,
            "output": self.output,
            "llm_enabled": self.llm_enabled,
            "skills": self.skills,
        }


@dataclass
class DeviceAnnounce:
    """设备上线消息."""
    msg_type: str = "device/announce"
    device: Optional[DeviceInfo] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class DeviceHeartbeat:
    """设备心跳."""
    msg_type: str = "device/heartbeat"
    device_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class DeviceOffline:
    """设备离线."""
    msg_type: str = "device/offline"
    device_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskRequest:
    """用户请求."""
    msg_type: str = "task/request"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    requester_id: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type,
            "request_id": self.request_id,
            "text": self.text,
            "requester_id": self.requester_id,
            "timestamp": self.timestamp,
        }


@dataclass
class TaskDispatch:
    """任务分发."""
    msg_type: str = "task/dispatch"
    request_id: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    executor_id: str = ""  # 为空则广播
    requires_llm: bool = False
    collaborate_with: List[str] = field(default_factory=list)
    timeout: int = 30
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "skill_name": self.skill_name,
            "parameters": self.parameters,
            "executor_id": self.executor_id,
            "requires_llm": self.requires_llm,
            "collaborate_with": self.collaborate_with,
            "timeout": self.timeout,
            "timestamp": self.timestamp,
        }


@dataclass
class TaskResponse:
    """任务响应."""
    msg_type: str = "task/response"
    request_id: str = ""
    task_id: str = ""
    success: bool = False
    result: str = ""
    executor_id: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "success": self.success,
            "result": self.result,
            "executor_id": self.executor_id,
            "timestamp": self.timestamp,
        }


@dataclass
class TaskCollaborate:
    """设备间协作请求."""
    msg_type: str = "task/collaborate"
    parent_task_id: str = ""
    request_id: str = ""
    skill_name: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    target_skill: str = ""
    executor_id: str = ""
    timeout: int = 30
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type,
            "parent_task_id": self.parent_task_id,
            "request_id": self.request_id,
            "skill_name": self.skill_name,
            "parameters": self.parameters,
            "target_skill": self.target_skill,
            "executor_id": self.executor_id,
            "timeout": self.timeout,
            "timestamp": self.timestamp,
        }


@dataclass
class TaskTimeout:
    """任务超时."""
    msg_type: str = "task/timeout"
    request_id: str = ""
    task_id: str = ""
    reason: str = "no_agent_response"
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


@dataclass
class TaskNotify:
    """通知用户."""
    msg_type: str = "task/notify"
    request_id: str = ""
    message: str = ""
    source_id: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type,
            "request_id": self.request_id,
            "message": self.message,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
        }
```

- [ ] **Step 5: 运行测试验证**

Run: `python -c "from server.core import MsgType, DeviceInfo, TaskRequest; print('OK')"`
Expected: 无错误输出

- [ ] **Step 6: Commit**

```bash
git add server/core/
git commit -m "feat(server): add core types and protocol definitions"
```

---

## Chunk 2: Server API + Auth

### Task 2.1: FastAPI 入口 + 依赖项

**Files:**
- Create: `server/main.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 更新 requirements.txt**

```txt
fastapi>=0.104.0
uvicorn>=0.24.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
httpx>=0.25.0
pyyaml>=6.0.1
pydantic>=2.0.0
pydantic-settings>=2.0.0
websockets>=12.0
aiohttp>=3.9.0
```

- [ ] **Step 2: 创建 server/main.py**

```python
"""dooz Server - FastAPI 入口."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api import auth, tenant, chat, llm, websocket
from server.tenant.manager import TenantManager
from server.transport.fastdds_gateway import FastDDSGateway

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 全局状态
tenant_manager: TenantManager = None
fastdds_gateway: FastDDSGateway = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    global tenant_manager, fastdds_gateway
    
    # 启动时初始化
    logger.info("Starting dooz server...")
    
    tenant_manager = TenantManager()
    fastdds_gateway = FastDDSGateway()
    
    # 加载已存在的租户
    await tenant_manager.load_tenants()
    
    # 启动 FastDDS Gateway
    await fastdds_gateway.start()
    
    logger.info("dooz server started")
    
    yield
    
    # 关闭时清理
    logger.info("Shutting down dooz server...")
    await fastdds_gateway.stop()
    logger.info("dooz server stopped")


app = FastAPI(
    title="dooz API",
    description="Distributed Multi-Agent Collaboration System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
app.include_router(chat.router, prefix="/tenant/{tenant_id}/chat", tags=["chat"])
app.include_router(llm.router, prefix="/tenant/{tenant_id}/llm", tags=["llm"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check():
    """健康检查."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 3: 创建 server/api/__init__.py**

```python
"""API package."""

from . import auth, tenant, chat, llm, websocket

__all__ = ["auth", "tenant", "chat", "llm", "websocket"]
```

- [ ] **Step 4: Commit**

```bash
git add server/main.py requirements.txt server/api/
git commit -m "feat(server): add FastAPI entry point and dependencies"
```

---

### Task 2.2: OAuth2 认证

**Files:**
- Create: `server/api/auth.py`

- [ ] **Step 1: 创建 server/api/auth.py**

```python
"""OAuth2 认证 API."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt

from server.core.exceptions import AuthError

router = APIRouter()

# JWT 配置 (MVP: 简化，实际应该从环境变量或配置读取)
SECRET_KEY = "dooz-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3600

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# 简化的客户端存储 (MVP: 内存存储)
# 实际应该使用数据库
_client_store: dict = {}


class Token(BaseModel):
    """Token 响应."""
    access_token: str
    token_type: str
    expires_in: int


class ClientCredentials(BaseModel):
    """客户端凭证."""
    client_id: str
    client_secret: str
    tenant_id: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """验证 token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise AuthError("Invalid token")


async def get_current_client(token: str = Depends(oauth2_scheme)) -> dict:
    """获取当前认证的客户端."""
    payload = verify_token(token)
    client_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    
    if not client_id or not tenant_id:
        raise AuthError("Invalid token payload")
    
    return {"client_id": client_id, "tenant_id": tenant_id}


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 Token 端点.
    
    支持 client_credentials 模式:
    - username: client_id
    - password: client_secret
    """
    client_id = form_data.username
    client_secret = form_data.password
    
    # 验证客户端 (MVP: 简化验证)
    # 实际应该从数据库验证
    if not _client_store.get(client_id):
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    
    stored_secret = _client_store[client_id].get("client_secret")
    if stored_secret != client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    
    tenant_id = _client_store[client_id].get("tenant_id")
    
    # 创建 token
    access_token = create_access_token(
        data={"sub": client_id, "tenant_id": tenant_id}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def register_client(client_id: str, client_secret: str, tenant_id: str):
    """注册客户端 (供租户创建时调用)."""
    _client_store[client_id] = {
        "client_secret": client_secret,
        "tenant_id": tenant_id,
    }
```

- [ ] **Step 2: 测试导入**

Run: `python -c "from server.api.auth import router; print('OK')"`
Expected: 无错误

- [ ] **Step 3: Commit**

```bash
git add server/api/auth.py
git commit -m "feat(server): add OAuth2 authentication API"
```

---

### Task 2.3: 租户管理 API

**Files:**
- Create: `server/tenant/config.py`
- Create: `server/tenant/manager.py`
- Create: `server/api/tenant.py`

- [ ] **Step 1: 创建 server/tenant/config.py**

```python
"""租户配置模型."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import yaml
from pathlib import Path


@dataclass
class LLMProvider:
    """LLM Provider 配置."""
    url: str
    api_key: str
    model: str = "gpt-4"


@dataclass
class Profile:
    """用户画像."""
    name: str = ""
    preferences: List[str] = field(default_factory=list)
    family_members: List[str] = field(default_factory=list)


@dataclass
class Soul:
    """灵魂设定."""
    name: str = "助手"
    personality: str = "温暖、贴心"
    role: str = "管家"


@dataclass
class Memory:
    """记忆 (MVP: 简化为文本列表)."""
    items: List[str] = field(default_factory=list)
    
    def add(self, content: str):
        """添加记忆."""
        self.items.append(content)
    
    def get_relevant(self, query: str) -> str:
        """获取相关记忆 (MVP: 简单返回所有)."""
        return "\n".join(self.items[-10:]) if self.items else "无记忆"


@dataclass
class TenantConfig:
    """租户配置."""
    tenant_id: str
    name: str
    llm_provider: LLMProvider
    profile: Profile = field(default_factory=Profile)
    memory: Memory = field(default_factory=Memory)
    soul: Soul = field(default_factory=Soul)
    
    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "llm_provider": {
                "url": self.llm_provider.url,
                "api_key": self.llm_provider.api_key,
                "model": self.llm_provider.model,
            },
            "profile": {
                "name": self.profile.name,
                "preferences": self.profile.preferences,
                "family_members": self.profile.family_members,
            },
            "soul": {
                "name": self.soul.name,
                "personality": self.soul.personality,
                "role": self.soul.role,
            },
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TenantConfig":
        return cls(
            tenant_id=data["tenant_id"],
            name=data["name"],
            llm_provider=LLMProvider(**data.get("llm_provider", {})),
            profile=Profile(**data.get("profile", {})),
            soul=Soul(**data.get("soul", {})),
        )
```

- [ ] **Step 2: 创建 server/tenant/manager.py**

```python
"""租户管理器."""

import logging
import uuid
from typing import Dict, Optional

from server.tenant.config import TenantConfig, LLMProvider, Profile, Soul, Memory
from server.core.exceptions import TenantNotFoundError

logger = logging.getLogger(__name__)


class TenantManager:
    """租户管理器."""
    
    def __init__(self):
        self._tenants: Dict[str, TenantConfig] = {}
    
    async def load_tenants(self):
        """加载租户配置 (MVP: 从内存或配置文件加载)."""
        logger.info("Loading tenants...")
        # MVP: 暂不实现持久化加载
    
    def create_tenant(self, name: str, llm_url: str, llm_api_key: str, llm_model: str = "gpt-4") -> TenantConfig:
        """创建租户."""
        tenant_id = f"tenant-{uuid.uuid4().hex[:8]}"
        
        config = TenantConfig(
            tenant_id=tenant_id,
            name=name,
            llm_provider=LLMProvider(
                url=llm_url,
                api_key=llm_api_key,
                model=llm_model,
            ),
            profile=Profile(),
            soul=Soul(),
            memory=Memory(),
        )
        
        self._tenants[tenant_id] = config
        logger.info(f"Created tenant: {tenant_id}")
        
        return config
    
    def get_tenant(self, tenant_id: str) -> TenantConfig:
        """获取租户配置."""
        if tenant_id not in self._tenants:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        return self._tenants[tenant_id]
    
    def list_tenants(self) -> list:
        """列出所有租户."""
        return [t.to_dict() for t in self._tenants.values()]
    
    def update_tenant(self, tenant_id: str, **kwargs) -> TenantConfig:
        """更新租户配置."""
        config = self.get_tenant(tenant_id)
        
        if "name" in kwargs:
            config.name = kwargs["name"]
        if "llm_provider" in kwargs:
            config.llm_provider = LLMProvider(**kwargs["llm_provider"])
        if "profile" in kwargs:
            config.profile = Profile(**kwargs["profile"])
        if "soul" in kwargs:
            config.soul = Soul(**kwargs["soul"])
        
        return config
    
    def add_memory(self, tenant_id: str, content: str):
        """添加记忆."""
        config = self.get_tenant(tenant_id)
        config.memory.add(content)
    
    def get_memory(self, tenant_id: str) -> list:
        """获取记忆."""
        config = self.get_tenant(tenant_id)
        return config.memory.items
```

- [ ] **Step 3: 创建 server/api/tenant.py**

```python
"""租户管理 API."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from server.tenant.manager import TenantManager
from server.tenant.config import TenantConfig
from server.api.auth import get_current_client

router = APIRouter()

# 全局租户管理器 (通过 app state 注入)
_tenant_manager: TenantManager = None


def set_tenant_manager(manager: TenantManager):
    """设置租户管理器."""
    global _tenant_manager
    _tenant_manager = manager


class CreateTenantRequest(BaseModel):
    """创建租户请求."""
    name: str
    llm_url: str
    llm_api_key: str
    llm_model: str = "gpt-4"


class UpdateProfileRequest(BaseModel):
    """更新画像请求."""
    name: str = None
    preferences: list = None
    family_members: list = None


class UpdateSoulRequest(BaseModel):
    """更新灵魂设定请求."""
    name: str = None
    personality: str = None
    role: str = None


class AddMemoryRequest(BaseModel):
    """添加记忆请求."""
    content: str


@router.post("/create", response_model=dict)
async def create_tenant(request: CreateTenantRequest):
    """创建租户."""
    if _tenant_manager is None:
        raise HTTPException(status_code=500, detail="Tenant manager not initialized")
    
    config = _tenant_manager.create_tenant(
        name=request.name,
        llm_url=request.llm_url,
        llm_api_key=request.llm_api_key,
        llm_model=request.llm_model,
    )
    
    return config.to_dict()


@router.get("/{tenant_id}/config", response_model=dict)
async def get_tenant_config(tenant_id: str, client: dict = Depends(get_current_client)):
    """获取租户配置."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    config = _tenant_manager.get_tenant(tenant_id)
    return config.to_dict()


@router.get("/{tenant_id}/profile", response_model=dict)
async def get_profile(tenant_id: str, client: dict = Depends(get_current_client)):
    """获取用户画像."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    config = _tenant_manager.get_tenant(tenant_id)
    return {
        "name": config.profile.name,
        "preferences": config.profile.preferences,
        "family_members": config.profile.family_members,
    }


@router.put("/{tenant_id}/profile")
async def update_profile(
    tenant_id: str, 
    request: UpdateProfileRequest,
    client: dict = Depends(get_current_client)
):
    """更新用户画像."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    kwargs = {k: v for k, v in request.dict().items() if v is not None}
    config = _tenant_manager.update_tenant(tenant_id, profile=kwargs)
    return {"status": "ok", "profile": config.profile.__dict__}


@router.get("/{tenant_id}/soul", response_model=dict)
async def get_soul(tenant_id: str, client: dict = Depends(get_current_client)):
    """获取灵魂设定."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    config = _tenant_manager.get_tenant(tenant_id)
    return {
        "name": config.soul.name,
        "personality": config.soul.personality,
        "role": config.soul.role,
    }


@router.put("/{tenant_id}/soul")
async def update_soul(
    tenant_id: str,
    request: UpdateSoulRequest,
    client: dict = Depends(get_current_client)
):
    """更新灵魂设定."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    kwargs = {k: v for k, v in request.dict().items() if v is not None}
    config = _tenant_manager.update_tenant(tenant_id, soul=kwargs)
    return {"status": "ok", "soul": config.soul.__dict__}


@router.get("/{tenant_id}/memory", response_model=list)
async def get_memory(tenant_id: str, client: dict = Depends(get_current_client)):
    """获取记忆列表."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return _tenant_manager.get_memory(tenant_id)


@router.post("/{tenant_id}/memory")
async def add_memory(
    tenant_id: str,
    request: AddMemoryRequest,
    client: dict = Depends(get_current_client)
):
    """添加记忆."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    _tenant_manager.add_memory(tenant_id, request.content)
    return {"status": "ok"}
```

- [ ] **Step 4: 测试导入**

Run: `python -c "from server.tenant.manager import TenantManager; print('OK')"`
Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add server/tenant/ server/api/tenant.py
git commit -m "feat(server): add tenant management API"
```

---

## Chunk 3: FastDDS Gateway + WebSocket

### Task 3.1: FastDDS Gateway (MVP: 内存总线模拟)

**Files:**
- Create: `server/transport/fastdds_gateway.py`
- Create: `server/transport/participant.py`

- [ ] **Step 1: 创建 server/transport/__init__.py**

```python
"""Transport package."""

__all__ = ["fastdds_gateway", "participant"]
```

- [ ] **Step 2: 创建 server/transport/participant.py (MVP: 简化为内存)**

```python
"""FastDDS Participant 管理 (MVP: 内存模拟)."""

import logging
import threading
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)


class TenantParticipant:
    """租户的 FastDDS Participant (MVP: 内存模拟).
    
    实际实现应该使用 fastdds Python 绑定。
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._subscribers: Dict[str, List[Callable]] = {}
        self._publishers: Dict[str, bool] = {}
        self._lock = threading.Lock()
        self._running = False
        
    def create_publisher(self, topic_name: str):
        """创建发布者."""
        with self._lock:
            self._publishers[topic_name] = True
        logger.info(f"[Tenant {self.tenant_id}] Publisher created: {topic_name}")
        
    def create_subscriber(self, topic_name: str, callback: Callable):
        """创建订阅者."""
        with self._lock:
            if topic_name not in self._subscribers:
                self._subscribers[topic_name] = []
            if callback not in self._subscribers[topic_name]:
                self._subscribers[topic_name].append(callback)
        logger.info(f"[Tenant {self.tenant_id}] Subscriber created: {topic_name}")
        
    def publish(self, topic_name: str, message: Any, sender_id: str = None):
        """发布消息."""
        with self._lock:
            subscribers = self._subscribers.get(topic_name, []).copy()
        
        for callback in subscribers:
            try:
                if isinstance(message, dict):
                    message["sender_id"] = sender_id
                callback(message)
            except Exception as e:
                logger.error(f"[Tenant {self.tenant_id}] Error in subscriber: {e}")
                
    def remove_subscriber(self, topic_name: str, callback: Callable):
        """移除订阅者."""
        with self._lock:
            if topic_name in self._subscribers:
                if callback in self._subscribers[topic_name]:
                    self._subscribers[topic_name].remove(callback)
                    
    def start(self):
        """启动."""
        self._running = True
        logger.info(f"[Tenant {self.tenant_id}] Participant started")
        
    def stop(self):
        """停止."""
        self._running = False
        with self._lock:
            self._subscribers.clear()
        logger.info(f"[Tenant {self.tenant_id}] Participant stopped")


class ParticipantManager:
    """Participant 管理器."""
    
    def __init__(self):
        self._participants: Dict[str, TenantParticipant] = {}
        self._lock = threading.Lock()
        
    def get_or_create(self, tenant_id: str) -> TenantParticipant:
        """获取或创建 Participant."""
        with self._lock:
            if tenant_id not in self._participants:
                self._participants[tenant_id] = TenantParticipant(tenant_id)
                self._participants[tenant_id].start()
            return self._participants[tenant_id]
        
    def remove(self, tenant_id: str):
        """移除 Participant."""
        with self._lock:
            if tenant_id in self._participants:
                self._participants[tenant_id].stop()
                del self._participants[tenant_id]
                
    def get(self, tenant_id: str) -> TenantParticipant:
        """获取 Participant."""
        return self._participants.get(tenant_id)
```

- [ ] **Step 3: 创建 server/transport/fastdds_gateway.py**

```python
"""FastDDS Gateway - WebSocket ↔ FastDDS 桥接."""

import asyncio
import logging
import json
from typing import Dict, Set

from fastapi import WebSocket

from server.transport.participant import ParticipantManager
from server.core.protocol import TopicPrefix, MsgType

logger = logging.getLogger(__name__)


class ClientConnection:
    """客户端连接."""
    
    def __init__(self, websocket: WebSocket, client_id: str, tenant_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.tenant_id = tenant_id
        self._subscriptions: Set[str] = set()
        
    async def send(self, message: dict):
        """发送消息给客户端."""
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to {self.client_id}: {e}")
            
    async def send_text(self, text: str):
        """发送文本消息."""
        try:
            await self.websocket.send_text(text)
        except Exception as e:
            logger.error(f"Error sending to {self.client_id}: {e}")


class FastDDSGateway:
    """FastDDS Gateway.
    
    MVP: 使用内存总线模拟
    生产: 使用 FastDDS Python 绑定
    """
    
    def __init__(self):
        self.participant_manager = ParticipantManager()
        self._connections: Dict[str, ClientConnection] = {}  # client_id -> connection
        self._topic_callbacks: Dict[str, Dict[str, callable]] = {}  # tenant_id -> {topic: {client_id: callback}}
        self._lock = asyncio.Lock()
        
    async def start(self):
        """启动 Gateway."""
        logger.info("FastDDS Gateway started (MVP: memory mode)")
        
    async def stop(self):
        """停止 Gateway."""
        self._connections.clear()
        logger.info("FastDDS Gateway stopped")
        
    async def connect(self, websocket: WebSocket, client_id: str, tenant_id: str) -> ClientConnection:
        """客户端连接."""
        async with self._lock:
            connection = ClientConnection(websocket, client_id, tenant_id)
            self._connections[client_id] = connection
            
            # 获取或创建租户 Participant
            participant = self.participant_manager.get_or_create(tenant_id)
            
            # 注册默认回调
            self._register_default_topics(tenant_id, client_id, connection)
            
        logger.info(f"Client {client_id} connected to tenant {tenant_id}")
        return connection
    
    async def disconnect(self, client_id: str):
        """客户端断开."""
        async with self._lock:
            if client_id in self._connections:
                conn = self._connections.pop(client_id)
                logger.info(f"Client {client_id} disconnected")
                
    def _register_default_topics(self, tenant_id: str, client_id: str, connection: ClientConnection):
        """注册默认话题回调."""
        topics = [
            TopicPrefix.task_dispatch(tenant_id),
            TopicPrefix.task_response(tenant_id),
            TopicPrefix.task_notify(tenant_id),
            TopicPrefix.task_timeout(tenant_id),
            TopicPrefix.device_announce(tenant_id),
            TopicPrefix.device_offline(tenant_id),
        ]
        
        for topic in topics:
            self.subscribe(tenant_id, client_id, topic, connection)
            
    def subscribe(self, tenant_id: str, client_id: str, topic: str, connection: ClientConnection):
        """订阅话题."""
        participant = self.participant_manager.get(tenant_id)
        if not participant:
            logger.warning(f"Tenant {tenant_id} not found")
            return
            
        async def callback(message: dict):
            # 检查是否是发给特定客户端的
            executor_id = message.get("executor_id", "")
            if executor_id and executor_id != client_id:
                return  # 不是发给我的
            await connection.send(message)
            
        participant.create_subscriber(topic, callback)
        
    def publish(self, tenant_id: str, topic: str, message: dict, sender_id: str = None):
        """发布消息."""
        participant = self.participant_manager.get(tenant_id)
        if not participant:
            logger.warning(f"Tenant {tenant_id} not found")
            return
            
        # 确保 publisher 存在
        participant.create_publisher(topic)
        participant.publish(topic, message, sender_id)
        
    def get_participant(self, tenant_id: str):
        """获取租户的 Participant."""
        return self.participant_manager.get(tenant_id)
```

- [ ] **Step 4: 测试导入**

Run: `python -c "from server.transport.fastdds_gateway import FastDDSGateway; print('OK')"`
Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add server/transport/
git commit -m "feat(server): add FastDDS Gateway (MVP memory mode)"
```

---

### Task 3.2: WebSocket API

**Files:**
- Create: `server/api/websocket.py`

- [ ] **Step 1: 创建 server/api/websocket.py**

```python
"""WebSocket API."""

import asyncio
import logging
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from server.transport.fastdds_gateway import FastDDSGateway, ClientConnection
from server.core.protocol import TopicPrefix

logger = logging.getLogger(__name__)

router = APIRouter()

# Gateway 引用 (通过 app 注入)
_gateway: FastDDSGateway = None


def set_gateway(gateway: FastDDSGateway):
    """设置 Gateway."""
    global _gateway
    _gateway = gateway


@router.websocket("/tenant/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    """
    WebSocket 端点.
    
    连接参数:
    - token: OAuth2 access token
    """
    # 获取 token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
        
    # 验证 token (简化)
    try:
        from server.api.auth import verify_token
        payload = verify_token(token)
        client_id = payload.get("sub")
        if payload.get("tenant_id") != tenant_id:
            await websocket.close(code=4003, reason="Tenant mismatch")
            return
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        await websocket.close(code=4002, reason="Invalid token")
        return
        
    # 接受连接
    await websocket.accept()
    
    # 连接 Gateway
    if _gateway is None:
        await websocket.close(code=5000, reason="Gateway not initialized")
        return
        
    connection = await _gateway.connect(websocket, client_id, tenant_id)
    
    try:
        # 处理消息循环
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("msg_type", "")
                
                # 确定 topic
                topic_map = {
                    "device/announce": TopicPrefix.device_announce,
                    "device/heartbeat": TopicPrefix.device_heartbeat,
                    "device/offline": TopicPrefix.device_offline,
                    "task/request": TopicPrefix.task_request,
                    "task/dispatch": TopicPrefix.task_dispatch,
                    "task/response": TopicPrefix.task_response,
                    "task/collaborate": TopicPrefix.task_collaborate,
                }
                
                topic_func = topic_map.get(msg_type)
                if topic_func:
                    topic = topic_func(tenant_id)
                    _gateway.publish(tenant_id, topic, message, sender_id=client_id)
                else:
                    logger.warning(f"Unknown msg_type: {msg_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {data}")
                
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    finally:
        await _gateway.disconnect(client_id)
```

- [ ] **Step 2: 测试导入**

Run: `python -c "from server.api.websocket import router; print('OK')"`
Expected: 无错误

- [ ] **Step 3: Commit**

```bash
git add server/api/websocket.py
git commit -m "feat(server): add WebSocket API for device connection"
```

---

## Chunk 4: LLM Gateway + Context

### Task 4.1: LLM Gateway

**Files:**
- Create: `server/llm/gateway.py`
- Create: `server/llm/context.py`
- Create: `server/api/llm.py`

- [ ] **Step 1: 创建 server/llm/context.py**

```python
"""LLM Context 组装."""

from typing import List, Dict, Any

from server.tenant.config import TenantConfig


class LLMContextBuilder:
    """LLM Context 建造者."""
    
    def __init__(self, tenant_config: TenantConfig):
        self.tenant = tenant_config
        
    def build_system_prompt(self) -> str:
        """构建 system prompt."""
        soul = self.tenant.soul
        profile = self.tenant.profile
        
        return f"""你是 {soul.name}，{soul.personality}。
你的职责是 {soul.role}。

用户信息:
- 姓名: {profile.name or '未设置'}
- 偏好: {', '.join(profile.preferences) if profile.preferences else '未设置'}
- 家庭成员: {', '.join(profile.family_members) if profile.family_members else '无'}

你是一个智能助手，可以帮助用户管理家庭设备、回答问题、提供建议等。
"""
        
    def build_chat_context(self, messages: List[Dict[str, str]], user_message: str = None) -> List[Dict[str, str]]:
        """构建聊天上下文."""
        context = []
        
        # System prompt
        context.append({
            "role": "system",
            "content": self.build_system_prompt()
        })
        
        # Memory (相关记忆)
        if self.tenant.memory.items:
            memory_content = "以下是之前对话中记录的重要信息:\n"
            memory_content += "\n".join([f"- {m}" for m in self.tenant.memory.items[-10:]])
            context.append({
                "role": "system",
                "content": memory_content
            })
        
        # 历史消息 (简化: 只取最近 10 条)
        for msg in messages[-10:]:
            context.append(msg)
            
        # 当前用户消息
        if user_message:
            context.append({
                "role": "user",
                "content": user_message
            })
            
        return context
        
    def build_task_analysis_prompt(self, task_text: str) -> str:
        """构建任务分析 prompt."""
        return f"""你是一个任务规划助手。请分析以下用户请求，并拆解为可执行的子任务。

用户请求: {task_text}

请以 JSON 格式返回任务拆解结果:
{{
    "intent": "用户意图",
    "subtasks": [
        {{
            "skill_name": "需要的技能",
            "parameters": {{"参数"}},
            "target_devices": ["目标设备类型"],
            "requires_llm": false
        }}
    ]
}}

只返回 JSON，不要其他内容。
"""
```

- [ ] **Step 2: 创建 server/llm/gateway.py**

```python
"""LLM Gateway."""

import logging
import json
from typing import List, Dict, Any, Optional

import httpx

from server.tenant.config import TenantConfig
from server.llm.context import LLMContextBuilder
from server.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMGateway:
    """LLM 请求网关."""
    
    def __init__(self, tenant_config: TenantConfig):
        self.tenant = tenant_config
        self.context_builder = LLMContextBuilder(tenant_config)
        
    async def chat(self, messages: List[Dict[str, str]], system: str = None) -> str:
        """发送聊天请求."""
        provider = self.tenant.llm_provider
        
        # 构建请求
        if system:
            # 如果有额外 system prompt，插入到最前面
            full_messages = [{"role": "system", "content": system}] + messages
        else:
            full_messages = messages
            
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": provider.model,
            "messages": full_messages,
            "temperature": 0.7,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    provider.url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {e.response.status_code} - {e.response.text}")
            raise LLMError(f"LLM request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise LLMError(f"LLM request failed: {e}")
            
    async def chat_with_context(self, user_message: str, history: List[Dict[str, str]] = None) -> str:
        """使用完整上下文聊天."""
        messages = self.context_builder.build_chat_context(
            history or [],
            user_message
        )
        return await self.chat(messages)
        
    async def analyze_task(self, task_text: str) -> Dict[str, Any]:
        """分析任务并拆解 (用于 TaskCoordinator)."""
        prompt = self.context_builder.build_task_analysis_prompt(task_text)
        
        result = await self.chat([
            {"role": "user", "content": prompt}
        ])
        
        # 解析 JSON
        try:
            # 尝试提取 JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
                
            return json.loads(result.strip())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse task analysis: {result}")
            return {
                "intent": task_text,
                "subtasks": []
            }
            
    async def summarize_session(self, messages: List[Dict[str, str]]) -> str:
        """总结会话 (用于生成 Memory)."""
        history_text = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}..."
            for msg in messages
        ])
        
        prompt = f"""总结以下对话，提取关键信息:

对话历史:
{history_text}

请以以下格式返回总结:
1. 用户偏好和习惯:
2. 需要避免的问题:
3. 重要信息:

只返回总结内容，不要其他内容。
"""
        
        return await self.chat([{"role": "user", "content": prompt}])
```

- [ ] **Step 3: 创建 server/api/llm.py**

```python
"""LLM API."""

from typing import List, Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from server.api.auth import get_current_client
from server.llm.gateway import LLMGateway
from server.tenant.manager import TenantManager

router = APIRouter()

_tenant_manager: TenantManager = None


def set_tenant_manager(manager: TenantManager):
    """设置租户管理器."""
    global _tenant_manager
    _tenant_manager = manager


class ChatRequest(BaseModel):
    """聊天请求."""
    messages: List[Dict[str, str]] = []
    system: str = None


class ChatResponse(BaseModel):
    """聊天响应."""
    content: str


class TaskAnalysisRequest(BaseModel):
    """任务分析请求."""
    task_text: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    tenant_id: str,
    request: ChatRequest,
    client: dict = Depends(get_current_client)
):
    """LLM 聊天接口."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    tenant_config = _tenant_manager.get_tenant(tenant_id)
    gateway = LLMGateway(tenant_config)
    
    result = await gateway.chat_with_context(
        request.messages[-1]["content"] if request.messages else "",
        request.messages[:-1] if request.messages else []
    )
    
    return ChatResponse(content=result)


@router.post("/analyze-task")
async def analyze_task(
    tenant_id: str,
    request: TaskAnalysisRequest,
    client: dict = Depends(get_current_client)
):
    """任务分析接口 (供 TaskCoordinator 使用)."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    tenant_config = _tenant_manager.get_tenant(tenant_id)
    gateway = LLMGateway(tenant_config)
    
    result = await gateway.analyze_task(request.task_text)
    
    return result
```

- [ ] **Step 4: 测试导入**

Run: `python -c "from server.llm.gateway import LLMGateway; print('OK')"`
Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add server/llm/ server/api/llm.py
git commit -m "feat(server): add LLM Gateway with context assembly"
```

---

### Task 4.2: Chat Session Manager

**Files:**
- Create: `server/chat/session.py`
- Create: `server/chat/manager.py`
- Create: `server/api/chat.py`

- [ ] **Step 1: 创建 server/chat/session.py**

```python
"""Chat Session 模型."""

from dataclasses import dataclass, field
from typing import List, Dict
import uuid
import time


@dataclass
class ChatSession:
    """Chat Session."""
    session_id: str
    tenant_id: str
    requester_id: str
    status: str = "active"  # active, completed
    messages: List[Dict[str, str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    ended_at: float = None
    
    def add_message(self, role: str, content: str):
        """添加消息."""
        self.messages.append({
            "role": role,
            "content": content
        })
        
    def end(self):
        """结束 session."""
        self.status = "completed"
        self.ended_at = time.time()
        
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "requester_id": self.requester_id,
            "status": self.status,
            "messages": self.messages,
            "created_at": self.created_at,
            "ended_at": self.ended_at,
        }
```

- [ ] **Step 2: 创建 server/chat/manager.py**

```python
"""Chat Session 管理器."""

import logging
from typing import Dict, Optional

from server.chat.session import ChatSession
from server.llm.gateway import LLMGateway
from server.tenant.config import TenantConfig

logger = logging.getLogger(__name__)


class ChatSessionManager:
    """Chat Session 管理器."""
    
    def __init__(self, tenant_config: TenantConfig):
        self.tenant = tenant_config
        self.sessions: Dict[str, ChatSession] = {}
        self.llm_gateway = LLMGateway(tenant_config)
        
    def create_session(self, tenant_id: str, requester_id: str) -> ChatSession:
        """创建 Session."""
        import uuid
        session_id = f"sess-{uuid.uuid4().hex[:12]}"
        
        session = ChatSession(
            session_id=session_id,
            tenant_id=tenant_id,
            requester_id=requester_id,
        )
        
        self.sessions[session_id] = session
        logger.info(f"Created session: {session_id}")
        
        return session
        
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取 Session."""
        return self.sessions.get(session_id)
        
    async def send_message(self, session_id: str, content: str) -> str:
        """发送消息."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        if session.status != "active":
            raise ValueError("Session is not active")
            
        # 添加用户消息
        session.add_message("user", content)
        
        # 调用 LLM
        response = await self.llm_gateway.chat_with_context(
            content,
            session.messages[:-1]  # 不包含刚加的这条
        )
        
        # 添加助手消息
        session.add_message("assistant", response)
        
        return response
        
    async def end_session(self, session_id: str) -> str:
        """结束 Session 并生成 Memory."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        session.end()
        
        # 调用 LLM 总结
        summary = await self.llm_gateway.summarize_session(session.messages)
        
        # 存储到 Memory
        self.tenant.memory.add(summary)
        
        logger.info(f"Session {session_id} ended, summary: {summary[:100]}...")
        
        return summary
```

- [ ] **Step 3: 创建 server/api/chat.py**

```python
"""Chat API."""

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from server.api.auth import get_current_client
from server.chat.manager import ChatSessionManager
from server.tenant.manager import TenantManager
from server.core.exceptions import SessionNotFoundError

router = APIRouter()

_tenant_manager: TenantManager = None
_session_managers: dict = {}  # tenant_id -> ChatSessionManager


def set_tenant_manager(manager: TenantManager):
    """设置租户管理器."""
    global _tenant_manager, _session_managers
    _tenant_manager = manager
    
    # 为每个租户创建 session manager
    for tenant_id, config in manager._tenants.items():
        _session_managers[tenant_id] = ChatSessionManager(config)


class StartSessionRequest(BaseModel):
    """创建 Session 请求."""
    pass


class MessageRequest(BaseModel):
    """消息请求."""
    content: str


class MessageResponse(BaseModel):
    """消息响应."""
    session_id: str
    content: str


class EndResponse(BaseModel):
    """结束响应."""
    session_id: str
    summary: str


@router.post("/start")
async def start_session(
    tenant_id: str,
    client: dict = Depends(get_current_client)
):
    """创建 Chat Session."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # 确保 session manager 存在
    if tenant_id not in _session_managers:
        config = _tenant_manager.get_tenant(tenant_id)
        _session_managers[tenant_id] = ChatSessionManager(config)
    
    manager = _session_managers[tenant_id]
    session = manager.create_session(tenant_id, client["client_id"])
    
    return {
        "session_id": session.session_id,
        "status": session.status
    }


@router.post("/{session_id}/message", response_model=MessageResponse)
async def send_message(
    tenant_id: str,
    session_id: str,
    request: MessageRequest,
    client: dict = Depends(get_current_client)
):
    """发送消息."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if tenant_id not in _session_managers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    manager = _session_managers[tenant_id]
    
    try:
        response = await manager.send_message(session_id, request.content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return MessageResponse(
        session_id=session_id,
        content=response
    )


@router.post("/{session_id}/end", response_model=EndResponse)
async def end_session(
    tenant_id: str,
    session_id: str,
    client: dict = Depends(get_current_client)
):
    """结束 Session."""
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if tenant_id not in _session_managers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    manager = _session_managers[tenant_id]
    
    try:
        summary = await manager.end_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return EndResponse(
        session_id=session_id,
        summary=summary
    )
```

- [ ] **Step 4: 测试导入**

Run: `python -c "from server.chat.manager import ChatSessionManager; print('OK')"`
Expected: 无错误

- [ ] **Step 5: Commit**

```bash
git add server/chat/ server/api/chat.py
git commit -m "feat(server): add Chat Session Manager with memory summarization"
```

---

## Chunk 5: Client Python

### Task 5.1: Client Python 核心

**Files:**
- Create: `client/python/core/types.py`
- Create: `client/python/core/transport.py`
- Create: `client/python/core/connection.py`

- [ ] **Step 1: 创建 client/python/core/types.py (复用 server/core/types.py 的子集)**

```python
"""Client 消息类型."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import time
import uuid


@dataclass
class DeviceInfo:
    """设备信息."""
    device_id: str
    name: str
    role: str
    wisdom: int
    output: bool
    llm_enabled: bool = False
    skills: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "role": self.role,
            "wisdom": self.wisdom,
            "output": self.output,
            "llm_enabled": self.llm_enabled,
            "skills": self.skills,
        }


@dataclass
class TaskDispatch:
    """任务分发."""
    msg_type: str = "task/dispatch"
    request_id: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    executor_id: str = ""
    requires_llm: bool = False
    collaborate_with: List[str] = field(default_factory=list)
    timeout: int = 30
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskResponse:
    """任务响应."""
    msg_type: str = "task/response"
    request_id: str = ""
    task_id: str = ""
    success: bool = False
    result: str = ""
    executor_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskNotify:
    """通知."""
    msg_type: str = "task/notify"
    request_id: str = ""
    message: str = ""
    source_id: str = ""
    timestamp: float = field(default_factory=time.time)
```

- [ ] **Step 2: 创建 client/python/core/connection.py**

```python
"""Client 连接."""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict

import websockets

from client.python.core.types import DeviceInfo

logger = logging.getLogger(__name__)


class ClientConnection:
    """Client 到 Server 的连接."""
    
    def __init__(
        self,
        server_url: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
    ):
        self.server_url = server_url
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        
        self._websocket = None
        self._token = None
        self._running = False
        self._callbacks: Dict[str, Callable] = {}
        
    async def connect(self) -> bool:
        """连接 Server."""
        # 1. 获取 token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/auth/token",
                data={
                    "username": self.client_id,
                    "password": self.client_secret,
                }
            )
            if response.status_code != 200:
                logger.error(f"Auth failed: {response.status_code}")
                return False
                
            data = response.json()
            self._token = data["access_token"]
            
        # 2. 连接 WebSocket
        ws_url = f"{self.server_url.replace('http', 'ws')}/ws/tenant/{self.tenant_id}?token={self._token}"
        self._websocket = await websockets.connect(ws_url)
        
        self._running = True
        logger.info(f"Connected to {self.server_url}")
        
        # 3. 发送 device announce
        await self._send_announce()
        
        return True
        
    async def disconnect(self):
        """断开连接."""
        self._running = False
        if self._websocket:
            await self._websocket.close()
            
    async def _send_announce(self):
        """发送设备上线消息."""
        # TODO: 从配置获取设备信息
        message = {
            "msg_type": "device/announce",
            "device": {
                "device_id": self.client_id,
                "name": "Device",
                "role": "agent",
                "wisdom": 50,
                "output": True,
                "llm_enabled": True,
                "skills": []
            }
        }
        await self.send(message)
        
    async def send(self, message: dict):
        """发送消息."""
        if self._websocket:
            await self._websocket.send(json.dumps(message))
            
    def on(self, msg_type: str, callback: Callable):
        """注册消息回调."""
        self._callbacks[msg_type] = callback
        
    async def loop(self):
        """消息循环."""
        try:
            async for message in self._websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("msg_type", "")
                    
                    if msg_type in self._callbacks:
                        self._callbacks[msg_type](data)
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {message}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        finally:
            self._running = False
```

- [ ] **Step 3: 创建 client/python/core/transport.py**

```python
"""Client 消息传输."""

import asyncio
import logging
from typing import Callable, Optional

from client.python.core.connection import ClientConnection

logger = logging.getLogger(__name__)


class ClientTransport:
    """Client 消息传输."""
    
    def __init__(self, connection: ClientConnection):
        self.connection = connection
        self._handlers: dict = {}
        
    def subscribe(self, msg_type: str, handler: Callable):
        """订阅消息."""
        self._handlers[msg_type] = handler
        self.connection.on(msg_type, handler)
        
    async def publish(self, msg_type: str, message: dict):
        """发布消息."""
        await self.connection.send(message)
        
    async def request_task(self, text: str, requester_id: str):
        """发送任务请求."""
        import uuid, time
        message = {
            "msg_type": "task/request",
            "request_id": str(uuid.uuid4()),
            "text": text,
            "requester_id": requester_id,
            "timestamp": time.time()
        }
        await self.publish("task/request", message)
```

- [ ] **Step 4: Commit**

```bash
git add client/python/core/
git commit -m "feat(client): add Python client core"
```

---

### Task 5.2: Client Agent 主类

**Files:**
- Create: `client/python/agent.py`

- [ ] **Step 1: 创建 client/python/agent.py**

```python
"""dooz Agent 主类."""

import asyncio
import logging
from typing import Optional

from client.python.core.connection import ClientConnection
from client.python.core.transport import ClientTransport
from client.python.core.types import DeviceInfo
from client.python.llm.client import LLmClient

logger = logging.getLogger(__name__)


class Agent:
    """dooz Agent (Client)."""
    
    def __init__(
        self,
        config: dict,
    ):
        self.config = config
        
        # 设备信息
        device = config.get("device", {})
        self.device_id = device.get("id")
        self.device_name = device.get("name")
        self.wisdom = device.get("wisdom", 50)
        self.output = device.get("output", False)
        self.llm_enabled = device.get("llm_enabled", False)
        self.skills = {s.get("name"): s for s in device.get("skills", [])}
        
        # Server 配置
        server = config.get("server", {})
        self.server_url = server.get("url", "http://localhost:8000")
        self.tenant_id = server.get("tenant_id")
        auth = server.get("auth", {})
        self.client_id = auth.get("client_id")
        self.client_secret = auth.get("client_secret")
        
        # 连接
        self._connection: Optional[ClientConnection] = None
        self._transport: Optional[ClientTransport] = None
        self._llm_client: Optional[LLmClient] = None
        self._running = False
        
    async def start(self):
        """启动 Agent."""
        logger.info(f"Starting agent: {self.device_id}")
        
        # 创建连接
        self._connection = ClientConnection(
            server_url=self.server_url,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        
        # 连接 Server
        if not await self._connection.connect():
            raise RuntimeError("Failed to connect to server")
            
        # 创建传输层
        self._transport = ClientTransport(self._connection)
        
        # 注册消息处理
        self._register_handlers()
        
        # 创建 LLM 客户端
        if self.llm_enabled:
            self._llm_client = LLmClient(
                server_url=self.server_url,
                tenant_id=self.tenant_id,
            )
            
        # 启动消息循环
        self._running = True
        asyncio.create_task(self._connection.loop())
        
        logger.info(f"Agent {self.device_id} started")
        
    async def stop(self):
        """停止 Agent."""
        self._running = False
        if self._connection:
            await self._connection.disconnect()
        logger.info(f"Agent {self.device_id} stopped")
        
    def _register_handlers(self):
        """注册消息处理."""
        self._transport.subscribe("task/dispatch", self._on_task_dispatch)
        self._transport.subscribe("task/collaborate", self._on_task_collaborate)
        
    async def _on_task_dispatch(self, message: dict):
        """处理任务分发."""
        executor_id = message.get("executor_id", "")
        
        # 检查是否是发给我的
        if executor_id and executor_id != self.device_id:
            return
            
        skill_name = message.get("skill_name")
        params = message.get("parameters", {})
        request_id = message.get("request_id")
        task_id = message.get("task_id")
        requires_llm = message.get("requires_llm", False)
        
        logger.info(f"Received task: {skill_name}")
        
        # 执行 skill
        if requires_llm and self.llm_enabled:
            # 需要 LLM 推理
            result = await self._execute_with_llm(skill_name, params, request_id)
        else:
            # 直接执行
            result = await self._execute_skill(skill_name, params)
            
        # 发送响应
        response = {
            "msg_type": "task/response",
            "request_id": request_id,
            "task_id": task_id,
            "success": result.get("success", False),
            "result": result.get("message", ""),
            "executor_id": self.device_id,
        }
        await self._transport.publish("task/response", response)
        
    async def _on_task_collaborate(self, message: dict):
        """处理协作请求."""
        # 类似 task dispatch
        await self._on_task_dispatch(message)
        
    async def _execute_skill(self, skill_name: str, params: dict) -> dict:
        """执行 skill."""
        # 动态导入 skill
        try:
            from skills import get_skill
            skill = get_skill(skill_name)
            if skill:
                return skill.execute(**params)
        except Exception as e:
            logger.error(f"Skill execution error: {e}")
            
        return {"success": False, "message": f"Skill {skill_name} not found"}
        
    async def _execute_with_llm(self, skill_name: str, params: dict, request_id: str) -> dict:
        """使用 LLM 执行复杂任务."""
        if not self._llm_client:
            return {"success": False, "message": "LLM not enabled"}
            
        # 调用 Server 的 LLM 分析任务
        # 这里简化处理
        return await self._llm_client.analyze_and_execute(
            f"执行任务: {skill_name}, 参数: {params}"
        )
        
    async def send_request(self, text: str):
        """发送用户请求."""
        await self._transport.request_task(text, self.device_id)
```

- [ ] **Step 2: 创建 client/python/llm/client.py**

```python
"""Client LLM 客户端."""

import httpx


class LLmClient:
    """Client LLM 客户端 (调用 Server 代理)."""
    
    def __init__(self, server_url: str, tenant_id: str):
        self.server_url = server_url
        self.tenant_id = tenant_id
        self._token = None
        
    async def _ensure_token(self):
        """确保 token (简化)."""
        # TODO: 实现 token 管理
        pass
        
    async def chat(self, messages: list) -> str:
        """聊天."""
        await self._ensure_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/tenant/{self.tenant_id}/llm/chat",
                json={"messages": messages},
            )
            response.raise_for_status()
            return response.json()["content"]
            
    async def analyze_and_execute(self, task: str) -> dict:
        """分析并执行任务."""
        # 这里简化处理
        return {"success": True, "message": f"Task completed: {task}"}
```

- [ ] **Step 3: 创建 client/python/__init__.py**

```python
"""dooz Python Client."""

__version__ = "0.1.0"

from .agent import Agent

__all__ = ["Agent"]
```

- [ ] **Step 4: Commit**

```bash
git add client/python/
git commit -m "feat(client): add Python Agent implementation"
```

---

## Chunk 6: Skills (复用现有)

### Task 6.1: 迁移 Skills

**Files:**
- Copy: `skills/*.py` → `client/python/skills/`

- [ ] **Step 1: 复制现有 skills 到 client/python/skills/**

```bash
cp -r skills/* client/python/skills/
```

- [ ] **Step 2: 更新 skills/__init__.py 导出**

```python
"""Skills package."""

from skills.screen_display import ScreenDisplaySkill
from skills.send_notification import SendNotificationSkill
from skills.play_audio import PlayAudioSkill
from skills.display_video import DisplayVideoSkill
from skills.toggle_light import ToggleLightSkill
from skills.set_brightness import SetBrightnessSkill


SKILL_REGISTRY = {
    "screen_display": ScreenDisplaySkill(),
    "send_notification": SendNotificationSkill(),
    "play_audio": PlayAudioSkill(),
    "display_video": DisplayVideoSkill(),
    "toggle_light": ToggleLightSkill(),
    "set_brightness": SetBrightnessSkill(),
}


def get_skill(name: str):
    """获取 skill."""
    return SKILL_REGISTRY.get(name)
```

- [ ] **Step 3: Commit**

```bash
git add client/python/skills/
git commit -m "feat(client): migrate skills to client/python/skills"
```

---

## 实施顺序

建议按以下顺序执行:

1. **Phase 1**: 创建目录结构 + Server 基础类型
2. **Phase 2**: Server API + Auth + Tenant Manager
3. **Phase 3**: FastDDS Gateway + WebSocket
4. **Phase 4**: LLM Gateway
5. **Phase 5**: Chat Session Manager
6. **Phase 6**: Client Python Core
7. **Phase 7**: Client Skills

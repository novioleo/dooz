# dooz MVP Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 dooz MVP - 最简可用版本，包含 Server 基础 + Python Client。

**Architecture:** Server-Client 架构，Server 提供 LLM 代理 + 消息路由，Client 通过 WebSocket 连接。

**Tech Stack:** Python 3.10+, FastAPI, WebSocket, OAuth2

---

## MVP 目标

最小可用功能：
1. 租户创建 + LLM Provider 配置
2. OAuth2 认证
3. Client 连接 (WebSocket)
4. 消息 Pub/Sub (内存模式)
5. LLM 代理接口
6. Python Client 基础 + Skills

---

## Chunk 1: Server 基础

### Task 1.1: 项目结构 + 依赖

**Files:**
- Create: `server/`
- Modify: `requirements.txt`

- [ ] **Step 1: 创建目录**

```bash
mkdir -p server/{api,core,tenant,llm,transport}
mkdir -p client/python/{core,skills,config/devices}
```

- [ ] **Step 2: 更新 requirements.txt**

```txt
fastapi>=0.104.0
uvicorn>=0.24.0
python-jose[cryptography]>=3.3.0
httpx>=0.25.0
pyyaml>=6.0.1
websockets>=12.0
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add server dependencies"
```

---

### Task 1.2: 核心类型

**Files:**
- Create: `server/core/types.py`
- Create: `server/core/protocol.py`
- Create: `server/core/__init__.py`

- [ ] **Step 1: 创建 server/core/protocol.py**

```python
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
```

- [ ] **Step 2: 创建 server/core/types.py**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add server/core/
git commit -m "feat(server): add core types"
```

---

## Chunk 2: Server API + Auth

### Task 2.1: FastAPI 入口

**Files:**
- Create: `server/main.py`

- [ ] **Step 1: 创建 server/main.py**

```python
"""dooz Server."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting...")
    yield
    logger.info("Server stopped")


app = FastAPI(title="dooz", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 2: Commit**

```bash
git add server/main.py
git commit -m "feat(server): add FastAPI entry point"
```

---

### Task 2.2: 租户管理

**Files:**
- Create: `server/tenant/manager.py`
- Create: `server/api/tenant.py`
- Create: `server/api/auth.py`

- [ ] **Step 1: 创建 server/tenant/manager.py**

```python
"""租户管理器."""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LLMProvider:
    url: str
    api_key: str
    model: str = "gpt-4"


@dataclass
class Tenant:
    tenant_id: str
    name: str
    llm_provider: LLMProvider
    client_id: str = ""
    client_secret: str = ""


class TenantManager:
    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
    
    def create(self, name: str, llm_url: str, llm_key: str, model: str = "gpt-4") -> Tenant:
        tid = f"tenant-{uuid.uuid4().hex[:8]}"
        client_id = f"client-{uuid.uuid4().hex[:8]}"
        client_secret = uuid.uuid4().hex[:16]
        
        tenant = Tenant(
            tenant_id=tid,
            name=name,
            llm_provider=LLMProvider(llm_url, llm_key, model),
            client_id=client_id,
            client_secret=client_secret,
        )
        self._tenants[tid] = tenant
        return tenant
    
    def get(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)
    
    def verify_client(self, client_id: str, client_secret: str) -> Optional[Tenant]:
        for t in self._tenants.values():
            if t.client_id == client_id and t.client_secret == client_secret:
                return t
        return None


# 全局实例
tenant_manager = TenantManager()
```

- [ ] **Step 2: 创建 server/api/auth.py**

```python
"""Auth API."""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt, JWTError

SECRET_KEY = "dooz-secret"
ALGORITHM = "HS256"

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

_tenant_manager = None


def set_tenant_manager(mgr):
    global _tenant_manager
    _tenant_manager = mgr


class Token(BaseModel):
    access_token: str
    token_type: str


def create_token(client_id: str, tenant_id: str) -> str:
    return jwt.encode(
        {"sub": client_id, "tenant_id": tenant_id, "exp": datetime.utcnow() + timedelta(hours=1)},
        SECRET_KEY, algorithm=ALGORITHM
    )


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/token", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    tenant = _tenant_manager.verify_client(form.username, form.password)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return Token(
        access_token=create_token(tenant.client_id, tenant.tenant_id),
        token_type="bearer"
    )
```

- [ ] **Step 3: 创建 server/api/tenant.py**

```python
"""Tenant API."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

_tenant_manager = None


def set_tenant_manager(mgr):
    global _tenant_manager
    _tenant_manager = mgr


class CreateRequest(BaseModel):
    name: str
    llm_url: str
    llm_api_key: str
    llm_model: str = "gpt-4"


@router.post("/create")
async def create_tenant(req: CreateRequest):
    tenant = _tenant_manager.create(req.name, req.llm_url, req.llm_api_key, req.llm_model)
    return {
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "client_id": tenant.client_id,
        "client_secret": tenant.client_secret,
        "llm_provider": {
            "url": tenant.llm_provider.url,
            "model": tenant.llm_provider.model,
        }
    }
```

- [ ] **Step 4: 更新 server/main.py 注册路由**

```python
from server.api import auth, tenant

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tenant.router, prefix="/tenant", tags=["tenant"])

# 注入依赖
auth.set_tenant_manager(tenant_manager)
tenant.set_tenant_manager(tenant_manager)
```

- [ ] **Step 5: Commit**

```bash
git add server/tenant/ server/api/
git commit -m "feat(server): add tenant management and auth"
```

---

## Chunk 3: FastDDS Gateway + WebSocket

### Task 3.1: 内存消息总线

**Files:**
- Create: `server/transport/bus.py`

- [ ] **Step 1: 创建 server/transport/bus.py**

```python
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


# 全局总线
bus = MessageBus()
```

- [ ] **Step 2: Commit**

```bash
git add server/transport/
git commit -m "feat(server): add in-memory message bus"
```

---

### Task 3.2: WebSocket API

**Files:**
- Create: `server/api/websocket.py`

- [ ] **Step 1: 创建 server/api/websocket.py**

```python
"""WebSocket API."""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from server.transport.bus import bus
from server.core.protocol import TopicPrefix

logger = logging.getLogger(__name__)

router = APIRouter()

_clients: Dict[str, WebSocket] = {}


@router.websocket("/tenant/{tenant_id}")
async def ws_endpoint(ws: WebSocket, tenant_id: str):
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4001)
        return
    
    # 验证 token
    try:
        from server.api.auth import verify_token
        payload = verify_token(token)
        client_id = payload.get("sub")
        if payload.get("tenant_id") != tenant_id:
            await ws.close(code=4003)
            return
    except:
        await ws.close(code=4002)
        return
    
    await ws.accept()
    _clients[client_id] = ws
    
    try:
        async for msg in ws:
            data = json.loads(msg)
            msg_type = data.get("msg_type", "")
            
            # 映射到 topic
            topics = {
                "device/announce": TopicPrefix.device_announce(tenant_id),
                "device/heartbeat": TopicPrefix.device_heartbeat(tenant_id),
                "device/offline": TopicPrefix.device_offline(tenant_id),
                "task/request": TopicPrefix.task_request(tenant_id),
                "task/dispatch": TopicPrefix.task_dispatch(tenant_id),
                "task/response": TopicPrefix.task_response(tenant_id),
            }
            
            topic = topics.get(msg_type)
            if topic:
                bus.publish(topic, data)
                
    except WebSocketDisconnect:
        pass
    finally:
        _clients.pop(client_id, None)
```

- [ ] **Step 2: 更新 server/main.py**

```python
from server.api import websocket
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
```

- [ ] **Step 3: Commit**

```bash
git add server/api/websocket.py
git commit -m "feat(server): add WebSocket API"
```

---

## Chunk 4: LLM Gateway

### Task 4.1: LLM 代理

**Files:**
- Create: `server/api/llm.py`

- [ ] **Step 1: 创建 server/api/llm.py**

```python
"""LLM API."""

import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

_tenant_manager = None


def set_tenant_manager(mgr):
    global _tenant_manager
    _tenant_manager = mgr


class ChatRequest(BaseModel):
    messages: list


class ChatResponse(BaseModel):
    content: str


async def get_current_client(token: str = Depends(oauth2_scheme)):
    from server.api.auth import verify_token
    return verify_token(token)


@router.post("/{tenant_id}/chat")
async def chat(tenant_id: str, req: ChatRequest, client: dict = Depends(get_current_client)):
    if client["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403)
    
    tenant = _tenant_manager.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404)
    
    # 调用 LLM
    headers = {"Authorization": f"Bearer {tenant.llm_provider.api_key}"}
    payload = {
        "model": tenant.llm_provider.model,
        "messages": req.messages,
    }
    
    async with httpx.AsyncClient(timeout=60.0) as http:
        resp = await http.post(tenant.llm_provider.url, headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()
        return ChatResponse(content=result["choices"][0]["message"]["content"])
```

- [ ] **Step 2: 更新 server/main.py**

```python
from server.api import llm
app.include_router(llm.router, prefix="/tenant", tags=["llm"])
llm.set_tenant_manager(tenant_manager)
```

- [ ] **Step 3: Commit**

```bash
git add server/api/llm.py
git commit -m "feat(server): add LLM proxy API"
```

---

## Chunk 5: Python Client

### Task 5.1: Client 核心

**Files:**
- Create: `client/python/client.py`

- [ ] **Step 1: 创建 client/python/client.py**

```python
"""dooz Python Client."""

import asyncio
import json
import logging
import httpx
import websockets
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Client:
    def __init__(self, config: dict):
        self.config = config
        device = config.get("device", {})
        self.device_id = device.get("id")
        self.wisdom = device.get("wisdom", 50)
        self.output = device.get("output", False)
        self.skills = {s.get("name"): s for s in device.get("skills", [])}
        
        server = config.get("server", {})
        self.server_url = server.get("url", "http://localhost:8000")
        self.tenant_id = server.get("tenant_id")
        self.client_id = server.get("auth", {}).get("client_id")
        self.client_secret = server.get("auth", {}).get("client_secret")
        
        self._ws = None
        self._token = None
        self._handlers = {}
    
    async def connect(self) -> bool:
        # 获取 token
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{self.server_url}/auth/token",
                data={"username": self.client_id, "password": self.client_secret}
            )
            if resp.status_code != 200:
                logger.error("Auth failed")
                return False
            self._token = resp.json()["access_token"]
        
        # 连接 WebSocket
        ws_url = f"{self.server_url.replace('http', 'ws')}/ws/tenant/{self.tenant_id}?token={self._token}"
        self._ws = await websockets.connect(ws_url)
        
        # 发送 announce
        await self.send({
            "msg_type": "device/announce",
            "device": {
                "device_id": self.device_id,
                "name": self.config.get("device", {}).get("name"),
                "wisdom": self.wisdom,
                "output": self.output,
                "skills": list(self.skills.keys())
            }
        })
        
        logger.info(f"Connected: {self.device_id}")
        return True
    
    async def disconnect(self):
        if self._ws:
            await self._ws.close()
    
    def on(self, msg_type: str, handler):
        self._handlers[msg_type] = handler
    
    async def send(self, msg: dict):
        await self._ws.send(json.dumps(msg))
    
    async def loop(self):
        try:
            async for msg in self._ws:
                data = json.loads(msg)
                msg_type = data.get("msg_type", "")
                if msg_type in self._handlers:
                    self._handlers[msg_type](data)
        except Exception as e:
            logger.error(f"Connection error: {e}")
    
    async def send_request(self, text: str):
        import uuid
        await self.send({
            "msg_type": "task/request",
            "request_id": str(uuid.uuid4()),
            "text": text,
            "requester_id": self.device_id,
        })
```

- [ ] **Step 2: 创建 client/python/main.py**

```python
"""Client 入口."""

import asyncio
import yaml
from client.python.client import Client


async def main():
    # 加载配置
    with open("config/devices/computer.yaml") as f:
        config = yaml.safe_load(f)
    
    client = Client(config)
    
    # 注册 handler
    client.on("task/dispatch", lambda msg: print(f"Task: {msg.get('skill_name')}"))
    client.on("task/notify", lambda msg: print(f"Notify: {msg.get('message')}"))
    
    # 连接
    if not await client.connect():
        return
    
    # 消息循环
    asyncio.create_task(client.loop())
    
    # 发送测试请求
    await asyncio.sleep(1)
    await client.send_request("开灯")
    
    # 保持运行
    await asyncio.sleep(10)
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Commit**

```bash
git add client/python/
git commit -m "feat(client): add Python client"
```

---

## Chunk 6: Skills

### Task 6.1: 基础 Skills

**Files:**
- Create: `client/python/skills/__init__.py`
- Create: `client/python/skills/light.py`

- [ ] **Step 1: 创建 skills**

```python
"""Skills."""

class LightSkill:
    def execute(self, action: str = "toggle", **kwargs):
        print(f"[Light] Action: {action}")
        return {"success": True, "message": f"Light {action} done"}


SKILLS = {
    "toggle_light": LightSkill(),
    "set_brightness": LightSkill(),
}


def get_skill(name: str):
    return SKILLS.get(name)
```

- [ ] **Step 2: Commit**

```bash
git add client/python/skills/
git commit -m "feat(client): add skills"
```

---

## 实施顺序

1. Server 基础 (types, protocol)
2. FastAPI 入口 + 依赖
3. 租户管理 + Auth
4. 消息总线 + WebSocket
5. LLM 代理
6. Python Client
7. Skills

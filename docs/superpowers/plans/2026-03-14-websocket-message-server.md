# WebSocket Message Server Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a WebSocket-based message relay server using FastAPI + WebSocket + pypubsub where clients can connect, query connected clients, send messages to specific clients, maintain heartbeats, and handle offline message delivery with timeout.

**Architecture:** 
- FastAPI handles HTTP endpoints for client management and health checks
- WebSocket connections maintained for real-time bidirectional communication
- pypubsub used for internal message distribution between components
- In-memory client registry tracks connected clients with their metadata
- Message queue system stores undelivered messages with TTL support
- Heartbeat mechanism detects client connectivity status

**Tech Stack:** FastAPI, Uvicorn, websockets, pypubsub

---

## New Features Added

1. **Heartbeat**: Clients send periodic ping/pong to maintain connection
2. **Offline Message Persistence**: Messages stored when recipient is offline, delivered on reconnect
3. **Message Timeout**: Messages expire after specified duration if not read

---

## File Structure

```
dooz_server/
├── pyproject.toml                    # Dependencies configuration
├── main.py                          # Application entry point
├── src/
│   └── dooz_server/
│       ├── __init__.py
│       ├── client_manager.py        # Client registry and connection management
│       ├── message_queue.py         # Message persistence with TTL support
│       ├── heartbeat.py             # Heartbeat mechanism for connection monitoring
│       ├── message_handler.py       # Message routing and pypubsub integration
│       ├── schemas.py               # Pydantic models for requests/responses
│       └── router.py                # FastAPI route definitions
├── test_clients/                     # Test client scripts for manual testing
│   ├── __init__.py
│   ├── client_base.py               # Base WebSocket client class
│   ├── client_alice.py              # Alice - interactive client
│   ├── client_bob.py                # Bob - auto-reply client
│   ├── client_charlie.py           # Charlie - offline simulation client
│   └── test_clients.py              # Run all clients
└── tests/
    ├── __init__.py
    ├── test_client_manager.py       # Tests for client management
    ├── test_message_queue.py        # Tests for message persistence
    ├── test_heartbeat.py            # Tests for heartbeat mechanism
    ├── test_message_handler.py      # Tests for message routing
    ├── test_router.py               # Tests for FastAPI routes
    ├── test_websocket.py           # Tests for WebSocket endpoint
    ├── test_main.py                 # Tests for main app
    └── test_integration.py          # Integration tests
```

---

## Chunk 1: Project Setup and Dependencies

### Task 1: Update pyproject.toml with required dependencies

**Files:**
- Modify: `dooz_server/pyproject.toml`

- [ ] **Step 1: Add dependencies to pyproject.toml**

```toml
[project]
name = "dooz-server"
version = "0.1.0"
description = "WebSocket message relay server"
readme = "README.md"
authors = [
    { name = "novio", email = "744351893@qq.com" }
]
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "websockets>=12.0",
    "pypubsub>=4.0.3",
    "pydantic>=2.5.0",
    "httpx>=0.25.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]

[project.scripts]
dooz-server = "dooz_server:main"
```

- [ ] **Step 2: Install dependencies**

Configure pip source in pyproject.toml first:

```toml
[project]
name = "dooz-server"
version = "0.1.0"
description = "WebSocket message relay server"
readme = "README.md"
authors = [
    { name = "novio", email = "744351893@qq.com" }
]
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "websockets>=12.0",
    "pypubsub>=4.0.3",
    "pydantic>=2.5.0",
    "httpx>=0.25.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]

[project.scripts]
dooz-server = "dooz_server:main"

[[tool.uv.index]]
url = "https://mirrors.cloud.tencent.com/pypi/simple/"
default = true
```

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server/dooz_server && uv sync`
Expected: Dependencies installed successfully

- [ ] **Step 3: Commit**

```bash
git add dooz_server/pyproject.toml
git commit -m "chore: add websocket, pypubsub dependencies with Tencent pip mirror"
```

---

## Chunk 2: Core Data Models

### Task 2: Create Pydantic schemas

**Files:**
- Create: `dooz_server/src/dooz_server/schemas.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schemas.py
import pytest
from pydantic import ValidationError
from dooz_server.schemas import ClientInfo, MessageRequest, MessageResponse, ClientListResponse

def test_client_info_creation():
    client = ClientInfo(client_id="test-123", name="TestUser", connected_at="2024-01-01T00:00:00Z")
    assert client.client_id == "test-123"
    assert client.name == "TestUser"

def test_message_request_valid():
    req = MessageRequest(to_client_id="client-456", content="Hello!")
    assert req.to_client_id == "client-456"
    assert req.content == "Hello!"

def test_message_request_empty_content():
    with pytest.raises(ValidationError):
        MessageRequest(to_client_id="client-456", content="")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_schemas.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server'"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClientInfo(BaseModel):
    """Information about a connected client."""
    client_id: str
    name: str
    connected_at: str


class MessageRequest(BaseModel):
    """Request to send a message to another client."""
    to_client_id: str = Field(..., description="Target client ID")
    content: str = Field(..., min_length=1, description="Message content")
    ttl_seconds: Optional[int] = Field(default=3600, description="Message TTL in seconds (0 = no expiry)")


class MessageResponse(BaseModel):
    """Response after sending a message."""
    success: bool
    message: str
    message_id: Optional[str] = None
    from_client_id: Optional[str] = None
    error_code: Optional[str] = None


class PendingMessagesResponse(BaseModel):
    """Response containing pending messages for a client."""
    messages: list[dict]  # List of stored messages
    total: int


class ClientListResponse(BaseModel):
    """Response containing list of connected clients."""
    clients: list[ClientInfo]
    total: int
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_server/src/dooz_server/schemas.py dooz_server/tests/test_schemas.py
git commit -m "feat: add Pydantic schemas for client and message models"
```

---

## Chunk 3: Client Manager

### Task 3: Implement client manager

**Files:**
- Create: `dooz_server/src/dooz_server/client_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_client_manager.py
import pytest
from dooz_server.client_manager import ClientManager

@pytest.fixture
def client_manager():
    return ClientManager()

def test_register_client(client_manager):
    client_id = client_manager.register_client("user1", "WebSocket")
    assert client_id is not None
    assert len(client_manager.get_all_clients()) == 1

def test_unregister_client(client_manager):
    client_id = client_manager.register_client("user1", "WebSocket")
    client_manager.unregister_client(client_id)
    assert len(client_manager.get_all_clients()) == 0

def test_get_client_info(client_manager):
    client_id = client_manager.register_client("user1", "WebSocket")
    info = client_manager.get_client_info(client_id)
    assert info is not None
    assert info.name == "user1"

def test_list_all_clients(client_manager):
    client_manager.register_client("user1", "WebSocket")
    client_manager.register_client("user2", "WebSocket")
    clients = client_manager.get_all_clients()
    assert len(clients) == 2

def test_get_nonexistent_client(client_manager):
    info = client_manager.get_client_info("nonexistent")
    assert info is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_client_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server.client_manager'"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/client_manager.py
import uuid
from datetime import datetime
from typing import Optional
from .schemas import ClientInfo


class ClientManager:
    """Manages connected client registry and WebSocket connections."""
    
    def __init__(self):
        self._clients: dict[str, ClientInfo] = {}
        self._connections: dict[str, any] = {}  # client_id -> websocket
    
    def register_client(self, name: str, connection_type: str = "WebSocket") -> str:
        """Register a new client and return their client_id."""
        client_id = str(uuid.uuid4())
        client_info = ClientInfo(
            client_id=client_id,
            name=name,
            connected_at=datetime.utcnow().isoformat() + "Z"
        )
        self._clients[client_id] = client_info
        return client_id
    
    def unregister_client(self, client_id: str) -> bool:
        """Unregister a client by ID. Returns True if client was removed."""
        if client_id in self._clients:
            del self._clients[client_id]
            if client_id in self._connections:
                del self._connections[client_id]
            return True
        return False
    
    def get_client_info(self, client_id: str) -> Optional[ClientInfo]:
        """Get client information by ID."""
        return self._clients.get(client_id)
    
    def get_all_clients(self) -> list[ClientInfo]:
        """Get list of all connected clients."""
        return list(self._clients.values())
    
    def add_connection(self, client_id: str, websocket: any) -> bool:
        """Associate a WebSocket connection with a client."""
        if client_id in self._clients:
            self._connections[client_id] = websocket
            return True
        return False
    
    def get_connection(self, client_id: str) -> Optional[any]:
        """Get WebSocket connection for a client."""
        return self._connections.get(client_id)
    
    def is_connected(self, client_id: str) -> bool:
        """Check if a client is connected."""
        return client_id in self._clients and client_id in self._connections
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_client_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_server/src/dooz_server/client_manager.py dooz_server/tests/test_client_manager.py
git commit -m "feat: add ClientManager for client registry"
```

---

## Chunk 4: Heartbeat Mechanism

### Task 4: Implement heartbeat system

**Files:**
- Create: `dooz_server/src/dooz_server/heartbeat.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_heartbeat.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from dooz_server.heartbeat import HeartbeatMonitor

@pytest.mark.asyncio
async def test_heartbeat_monitor_creation():
    monitor = HeartbeatMonitor()
    assert monitor is not None

@pytest.mark.asyncio
async def test_record_heartbeat():
    monitor = HeartbeatMonitor()
    await monitor.record_heartbeat("client-123")
    assert monitor.is_alive("client-123")

@pytest.mark.asyncio
async def test_client_timeout():
    monitor = HeartbeatMonitor(timeout_seconds=1)
    await monitor.record_heartbeat("client-123")
    await asyncio.sleep(1.5)
    assert not monitor.is_alive("client-123")

@pytest.mark.asyncio
async def test_remove_client():
    monitor = HeartbeatMonitor()
    await monitor.record_heartbeat("client-123")
    monitor.remove_client("client-123")
    assert not monitor.is_alive("client-123")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_heartbeat.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server.heartbeat'"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/heartbeat.py
import asyncio
import time
from typing import Dict, Optional
from datetime import datetime, timedelta


class HeartbeatMonitor:
    """Monitors client heartbeats and detects timeouts."""
    
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self._heartbeats: Dict[str, float] = {}  # client_id -> last heartbeat timestamp
    
    async def record_heartbeat(self, client_id: str) -> None:
        """Record a heartbeat from a client."""
        self._heartbeats[client_id] = time.time()
    
    def is_alive(self, client_id: str) -> bool:
        """Check if a client is still alive (within timeout)."""
        if client_id not in self._heartbeats:
            return False
        
        last_heartbeat = self._heartbeats[client_id]
        elapsed = time.time() - last_heartbeat
        return elapsed < self.timeout_seconds
    
    def remove_client(self, client_id: str) -> None:
        """Remove a client from heartbeat tracking."""
        if client_id in self._heartbeats:
            del self._heartbeats[client_id]
    
    def get_last_heartbeat(self, client_id: str) -> Optional[float]:
        """Get the last heartbeat timestamp for a client."""
        return self._heartbeats.get(client_id)
    
    async def cleanup_dead_clients(self) -> list[str]:
        """Remove dead clients and return their IDs."""
        dead_clients = []
        for client_id in list(self._heartbeats.keys()):
            if not self.is_alive(client_id):
                self.remove_client(client_id)
                dead_clients.append(client_id)
        return dead_clients
    
    async def start_monitor_loop(self, callback=None):
        """Start the background monitoring loop."""
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            dead = await self.cleanup_dead_clients()
            if callback and dead:
                for client_id in dead:
                    await callback(client_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_heartbeat.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_server/src/dooz_server/heartbeat.py dooz_server/tests/test_heartbeat.py
git commit -m "feat: add HeartbeatMonitor for connection health tracking"
```

---

## Chunk 5: Message Queue with TTL

### Task 5: Implement message queue with timeout

**Files:**
- Create: `dooz_server/src/dooz_server/message_queue.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_message_queue.py
import pytest
import asyncio
from dooz_server.message_queue import MessageQueue, StoredMessage

def test_store_message():
    queue = MessageQueue()
    msg_id = queue.store_message("from-1", "to-2", "Hello!")
    assert msg_id is not None
    
def test_get_pending_messages():
    queue = MessageQueue()
    queue.store_message("from-1", "to-2", "Hello!")
    messages = queue.get_pending_messages("to-2")
    assert len(messages) == 1
    assert messages[0].content == "Hello!"

def test_mark_as_read():
    queue = MessageQueue()
    msg_id = queue.store_message("from-1", "to-2", "Hello!")
    queue.mark_as_read(msg_id)
    messages = queue.get_pending_messages("to-2")
    assert len(messages) == 0

def test_message_timeout():
    queue = MessageQueue(default_ttl_seconds=1)
    queue.store_message("from-1", "to-2", "Hello!")
    asyncio.run(asyncio.sleep(1.5))
    expired = queue.get_pending_messages("to-2")
    assert len(expired) == 0  # Should be cleaned up
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_message_queue.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server.message_queue'"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/message_queue.py
import uuid
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StoredMessage:
    """Represents a stored message with metadata."""
    message_id: str
    from_client_id: str
    to_client_id: str
    content: str
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    is_read: bool = False


class MessageQueue:
    """Queue for storing undelivered messages with TTL support."""
    
    def __init__(self, default_ttl_seconds: int = 3600):  # Default 1 hour
        self.default_ttl_seconds = default_ttl_seconds
        self._messages: Dict[str, StoredMessage] = {}
        self._client_messages: Dict[str, List[str]] = {}  # client_id -> [message_ids]
    
    def store_message(
        self, 
        from_client_id: str, 
        to_client_id: str, 
        content: str,
        ttl_seconds: Optional[int] = None
    ) -> str:
        """Store a message for later delivery."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        
        message_id = str(uuid.uuid4())
        message = StoredMessage(
            message_id=message_id,
            from_client_id=from_client_id,
            to_client_id=to_client_id,
            content=content,
            expires_at=time.time() + ttl if ttl > 0 else None
        )
        
        self._messages[message_id] = message
        
        if to_client_id not in self._client_messages:
            self._client_messages[to_client_id] = []
        self._client_messages[to_client_id].append(message_id)
        
        return message_id
    
    def get_pending_messages(self, client_id: str) -> List[StoredMessage]:
        """Get all unread, unexpired messages for a client."""
        if client_id not in self._client_messages:
            return []
        
        current_time = time.time()
        pending = []
        
        for msg_id in self._client_messages[client_id]:
            msg = self._messages.get(msg_id)
            if msg and not msg.is_read:
                # Check expiration
                if msg.expires_at and msg.expires_at < current_time:
                    # Message expired - remove it
                    self._remove_message(msg_id, client_id)
                    continue
                pending.append(msg)
        
        return pending
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        if message_id in self._messages:
            self._messages[message_id].is_read = True
            return True
        return False
    
    def get_message(self, message_id: str) -> Optional[StoredMessage]:
        """Get a specific message by ID."""
        return self._messages.get(message_id)
    
    def _remove_message(self, message_id: str, client_id: str) -> None:
        """Remove a message from storage."""
        if message_id in self._messages:
            del self._messages[message_id]
        if client_id in self._client_messages and message_id in self._client_messages[client_id]:
            self._client_messages[client_id].remove(message_id)
    
    def cleanup_expired(self) -> int:
        """Remove all expired messages. Returns count of removed messages."""
        current_time = time.time()
        expired_ids = [
            msg_id for msg_id, msg in self._messages.items()
            if msg.expires_at and msg.expires_at < current_time
        ]
        
        for msg_id in expired_ids:
            msg = self._messages[msg_id]
            self._remove_message(msg_id, msg.to_client_id)
        
        return len(expired_ids)
    
    def get_expired_messages(self) -> List[StoredMessage]:
        """Get list of expired messages (for notifying sender)."""
        current_time = time.time()
        return [
            msg for msg in self._messages.values()
            if msg.expires_at and msg.expires_at < current_time and not msg.is_read
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_message_queue.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_server/src/dooz_server/message_queue.py dooz_server/tests/test_message_queue.py
git commit -m "feat: add MessageQueue with TTL for offline message storage"
```

---

## Chunk 6: Message Handler with PubSub

### Task 6: Implement message handler with pypubsub

**Files:**
- Create: `dooz_server/src/dooz_server/message_handler.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_message_handler.py
import pytest
from unittest.mock import Mock, AsyncMock
from dooz_server.message_handler import MessageHandler
from dooz_server.client_manager import ClientManager
from dooz_server.message_queue import MessageQueue

@pytest.fixture
def client_manager():
    return ClientManager()

@pytest.fixture
def message_queue():
    return MessageQueue()

@pytest.fixture
def message_handler(client_manager, message_queue):
    return MessageHandler(client_manager, message_queue)

def test_send_message_to_online_client(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    
    # Mock the websocket send
    mock_ws = Mock()
    mock_ws.send_json = AsyncMock()
    client_manager.add_connection(recipient_id, mock_ws)
    
    success, msg, msg_id = message_handler.send_message(sender_id, recipient_id, "Hello!")
    assert success is True
    mock_ws.send_json.assert_called_once()

def test_send_message_to_nonexistent(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    success, msg, msg_id = message_handler.send_message(sender_id, "nonexistent", "Hello!")
    assert success is False

def test_send_message_to_offline_client_queues(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    # Don't add connection - recipient is offline
    
    success, msg, msg_id = message_handler.send_message(sender_id, recipient_id, "Hello!")
    assert success is True
    assert msg_id is not None  # Message was queued
    assert "queued" in msg.lower()

def test_send_message_with_ttl_zero_no_queue(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    # Don't add connection - recipient is offline
    
    success, msg, msg_id = message_handler.send_message(
        sender_id, recipient_id, "Hello!", ttl_seconds=0
    )
    assert success is False
    assert "offline" in msg.lower()

def test_deliver_pending_messages(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    
    # Queue a message while recipient is offline
    success, msg, msg_id = message_handler.send_message(
        sender_id, recipient_id, "Hello!"
    )
    
    # Now connect the recipient
    mock_ws = Mock()
    mock_ws.send_json = AsyncMock()
    client_manager.add_connection(recipient_id, mock_ws)
    
    # Deliver pending messages
    delivered = message_handler.deliver_pending_messages(recipient_id)
    assert delivered == 1
    mock_ws.send_json.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_message_handler.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server.message_handler'"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/message_handler.py
import json
from typing import Optional
from pubsub import pub
from .client_manager import ClientManager
from .message_queue import MessageQueue
from .schemas import MessageRequest, MessageResponse


class MessageHandler:
    """Handles message routing between clients using pypubsub."""
    
    def __init__(self, client_manager: ClientManager, message_queue: MessageQueue = None):
        self.client_manager = client_manager
        self.message_queue = message_queue or MessageQueue()
        self._setup_pubsub_listeners()
    
    def _setup_pubsub_listeners(self):
        """Set up pubsub listeners for message events."""
        pub.subscribe(self._on_message, 'message.send')
        pub.subscribe(self._on_message_expired, 'message.expired')
    
    def _on_message(self, data: dict):
        """Handle incoming message events."""
        pass
    
    def _on_message_expired(self, data: dict):
        """Handle expired messages - notify sender."""
        # This would be triggered by a background task checking for expired messages
        pass
    
    def send_message(
        self, 
        from_client_id: str, 
        to_client_id: str, 
        content: str,
        ttl_seconds: int = 3600
    ) -> tuple[bool, str, str]:
        """
        Send a message from one client to another.
        Returns: (success, message, message_id or error_code)
        """
        # Verify sender exists
        if not self.client_manager.get_client_info(from_client_id):
            return (False, "Sender not found", None)
        
        # Verify recipient exists
        recipient_info = self.client_manager.get_client_info(to_client_id)
        if not recipient_info:
            return (False, "Recipient not found", None)
        
        # Check if recipient is connected
        ws = self.client_manager.get_connection(to_client_id)
        
        if ws:
            # Recipient is online - send directly
            message = {
                "type": "message",
                "from_client_id": from_client_id,
                "from_client_name": self.client_manager.get_client_info(from_client_id).name,
                "to_client_id": to_client_id,
                "content": content
            }
            
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(ws.send_json(message))
                else:
                    loop.run_until_complete(ws.send_json(message))
                return (True, "Message delivered", None)
            except Exception as e:
                return (False, f"Failed to send: {str(e)}", None)
        else:
            # Recipient is offline - store message
            if ttl_seconds == 0:
                return (False, "Recipient offline and TTL is 0 (no offline storage)", None)
            
            msg_id = self.message_queue.store_message(
                from_client_id=from_client_id,
                to_client_id=to_client_id,
                content=content,
                ttl_seconds=ttl_seconds
            )
            return (True, "Message queued for offline delivery", msg_id)
    
    def deliver_pending_messages(self, client_id: str) -> int:
        """Deliver all pending messages to a newly connected client."""
        pending = self.message_queue.get_pending_messages(client_id)
        ws = self.client_manager.get_connection(client_id)
        
        if not ws:
            return 0
        
        delivered = 0
        for msg in pending:
            message = {
                "type": "message",
                "message_id": msg.message_id,
                "from_client_id": msg.from_client_id,
                "from_client_name": self.client_manager.get_client_info(msg.from_client_id).name,
                "to_client_id": msg.to_client_id,
                "content": msg.content,
                "is_offline": True
            }
            
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(ws.send_json(message))
                else:
                    loop.run_until_complete(ws.send_json(message))
                self.message_queue.mark_as_read(msg.message_id)
                delivered += 1
            except Exception:
                pass
        
        return delivered
    
    def get_pending_messages(self, client_id: str) -> list:
        """Get pending messages for a client (without marking as read)."""
        return self.message_queue.get_pending_messages(client_id)
    
    def check_expired_messages(self) -> list:
        """Check and return expired messages, notify senders."""
        expired = self.message_queue.get_expired_messages()
        results = []
        
        for msg in expired:
            results.append({
                "message_id": msg.message_id,
                "from_client_id": msg.from_client_id,
                "to_client_id": msg.to_client_id,
                "content": msg.content
            })
            # Notify sender about expiration
            sender_ws = self.client_manager.get_connection(msg.from_client_id)
            if sender_ws:
                notification = {
                    "type": "message_expired",
                    "message_id": msg.message_id,
                    "to_client_id": msg.to_client_id,
                    "content": msg.content
                }
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.ensure_future(sender_ws.send_json(notification))
                    else:
                        loop.run_until_complete(sender_ws.send_json(notification))
                except Exception:
                    pass
        
        # Clean up expired messages
        self.message_queue.cleanup_expired()
        return results
    
    def broadcast_message(self, from_client_id: str, content: str) -> int:
        """Broadcast a message to all connected clients."""
        clients = self.client_manager.get_all_clients()
        sent_count = 0
        
        for client in clients:
            if client.client_id != from_client_id:
                success, _, _ = self.send_message(from_client_id, client.client_id, content)
                if success:
                    sent_count += 1
        
        return sent_count
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_message_handler.py -v`
Expected: PASS (may need to adjust for async behavior)

- [ ] **Step 5: Commit**

```bash
git add dooz_server/src/dooz_server/message_handler.py dooz_server/tests/test_message_handler.py
git commit -m "feat: add MessageHandler with pypubsub for message routing"
```

---

## Chunk 7: FastAPI Router

### Task 7: Implement FastAPI routes

**Files:**
- Create: `dooz_server/src/dooz_server/router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_router.py
import pytest
from fastapi.testclient import TestClient
from dooz_server.router import router, get_client_manager, get_message_handler
from dooz_server.client_manager import ClientManager
from dooz_server.message_handler import MessageHandler

@pytest.fixture
def client_manager():
    return ClientManager()

@pytest.fixture
def message_handler(client_manager):
    return MessageHandler(client_manager)

@pytest.fixture
def test_client(client_manager, message_handler):
    # Override dependencies
    router.dependency_overrides[get_client_manager] = lambda: client_manager
    router.dependency_overrides[get_message_handler] = lambda: message_handler
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_clients(test_client, client_manager):
    client_manager.register_client("user1")
    client_manager.register_client("user2")
    
    response = test_client.get("/clients")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["clients"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_router.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server.router'"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/router.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from .client_manager import ClientManager
from .message_handler import MessageHandler
from .schemas import ClientListResponse, MessageRequest, MessageResponse


router = APIRouter()

# Dependency injection
_client_manager: ClientManager = None
_message_handler: MessageHandler = None


def get_client_manager() -> ClientManager:
    global _client_manager
    if _client_manager is None:
        _client_manager = ClientManager()
    return _client_manager


def get_message_handler() -> MessageHandler:
    global _message_handler
    if _message_handler is None:
        _message_handler = MessageHandler(get_client_manager())
    return _message_handler


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/clients", response_model=ClientListResponse)
async def list_clients(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)]
):
    """List all connected clients."""
    clients = client_manager.get_all_clients()
    return ClientListResponse(clients=clients, total=len(clients))


@router.get("/clients/{client_id}")
async def get_client(
    client_id: str,
    client_manager: Annotated[ClientManager, Depends(get_client_manager)]
):
    """Get specific client information."""
    client_info = client_manager.get_client_info(client_id)
    if not client_info:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_info


@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    from_client_id: str,  # Would come from WebSocket auth in production
    message_handler: Annotated[MessageHandler, Depends(get_message_handler)]
):
    """Send a message to another client."""
    success, msg, msg_id = message_handler.send_message(
        from_client_id=from_client_id,
        to_client_id=request.to_client_id,
        content=request.content,
        ttl_seconds=request.ttl_seconds
    )
    
    if not success:
        error_code = "recipient_not_found" if "not found" in msg.lower() else "recipient_offline"
        return MessageResponse(
            success=False,
            message=msg,
            error_code=error_code
        )
    
    return MessageResponse(
        success=True,
        message=msg,
        message_id=msg_id,
        from_client_id=from_client_id
    )


@router.get("/messages/pending/{client_id}")
async def get_pending_messages(
    client_id: str,
    message_handler: Annotated[MessageHandler, Depends(get_message_handler)]
):
    """Get pending messages for a client."""
    messages = message_handler.get_pending_messages(client_id)
    return {
        "messages": [
            {
                "message_id": m.message_id,
                "from_client_id": m.from_client_id,
                "content": m.content,
                "created_at": m.created_at,
                "expires_at": m.expires_at
            }
            for m in messages
        ],
        "total": len(messages)
    }


@router.post("/messages/check-expired")
async def check_expired_messages(
    message_handler: Annotated[MessageHandler, Depends(get_message_handler)]
):
    """Check for expired messages and notify senders."""
    expired = message_handler.check_expired_messages()
    return {
        "expired_count": len(expired),
        "messages": expired
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_server/src/dooz_server/router.py dooz_server/tests/test_router.py
git commit -m "feat: add FastAPI router for HTTP endpoints"
```

---

## Chunk 8: WebSocket Endpoint

### Task 8: Implement WebSocket endpoint

**Files:**
- Modify: `dooz_server/src/dooz_server/router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_websocket.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from dooz_server.router import router, websocket_endpoint

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection handling."""
    # This is a simplified test - full test would use TestClient with WS
    pass

def test_websocket_route_exists():
    """Test that WebSocket route is registered."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    
    # Check routes include websocket
    routes = [r.path for r in app.routes]
    assert "/ws/{client_id}" in routes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_websocket.py -v`
Expected: FAIL with "websocket_endpoint not defined"

- [ ] **Step 3: Write minimal implementation**

Add to `dooz_server/src/dooz_server/router.py`:

```python
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
import asyncio


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


# Global connection manager
ws_manager = ConnectionManager()
_heartbeat_monitor = None


def get_heartbeat_monitor():
    global _heartbeat_monitor
    if _heartbeat_monitor is None:
        from dooz_server.heartbeat import HeartbeatMonitor
        _heartbeat_monitor = HeartbeatMonitor(timeout_seconds=30)
    return _heartbeat_monitor


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for client connections with heartbeat support."""
    await ws_manager.connect(client_id, websocket)
    
    # Register with client manager
    client_manager = get_client_manager()
    client_manager.add_connection(client_id, websocket)
    
    # Record initial heartbeat
    heartbeat_monitor = get_heartbeat_monitor()
    await heartbeat_monitor.record_heartbeat(client_id)
    
    # Deliver any pending offline messages
    message_handler = get_message_handler()
    pending_count = message_handler.deliver_pending_messages(client_id)
    if pending_count > 0:
        await ws_manager.send_personal_message({
            "type": "pending_delivered",
            "count": pending_count
        }, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "message":
                # Send message to another client
                message_handler = get_message_handler()
                to_client = message_data.get("to_client_id")
                content = message_data.get("content")
                ttl_seconds = message_data.get("ttl_seconds", 3600)
                
                success, msg, msg_id = message_handler.send_message(
                    from_client_id=client_id,
                    to_client_id=to_client,
                    content=content,
                    ttl_seconds=ttl_seconds
                )
                
                # Send confirmation back to sender
                await ws_manager.send_personal_message({
                    "type": "message_sent",
                    "success": success,
                    "message": msg,
                    "message_id": msg_id,
                    "to_client_id": to_client
                }, client_id)
            
            elif message_type == "ping":
                # Record heartbeat and respond
                await heartbeat_monitor.record_heartbeat(client_id)
                await ws_manager.send_personal_message({
                    "type": "pong"
                }, client_id)
            
            elif message_type == "heartbeat":
                # Explicit heartbeat from client
                await heartbeat_monitor.record_heartbeat(client_id)
                await ws_manager.send_personal_message({
                    "type": "heartbeat_ack",
                    "server_time": asyncio.get_event_loop().time()
                }, client_id)
                
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        heartbeat_monitor.remove_client(client_id)
        # Don't unregister client - they may reconnect
        # client_manager.unregister_client(client_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_websocket.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_server/src/dooz_server/router.py dooz_server/tests/test_websocket.py
git commit -m "feat: add WebSocket endpoint for real-time messaging"
```

---

## Chunk 9: Main Application Entry Point

### Task 9: Create main.py entry point

**Files:**
- Modify: `dooz_server/main.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_main.py
import pytest

def test_main_imports():
    """Test that main.py can be imported."""
    import dooz_server.main as main
    assert main.app is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_main.py -v`
Expected: FAIL with "app not defined"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dooz_server.router import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Dooz WebSocket Server",
        description="WebSocket message relay server for client-to-client communication",
        version="0.1.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(router)
    
    return app


app = create_app()


def main():
    """Run the server using uvicorn."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_server/main.py dooz_server/tests/test_main.py
git commit -m "feat: add main.py entry point with FastAPI app"
```

---

## Chunk 10: Integration Tests

### Task 10: Create integration tests

**Files:**
- Create: `dooz_server/tests/test_integration.py`

- [ ] **Step 1: Write the integration test**

```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from dooz_server.main import app
from dooz_server.client_manager import ClientManager
from dooz_server.message_handler import MessageHandler


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_clients_empty(client):
    """Test listing clients when none connected."""
    response = client.get("/clients")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["clients"] == []


def test_get_nonexistent_client(client):
    """Test getting info for nonexistent client."""
    response = client.get("/clients/nonexistent-id")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/test_integration.py -v`
Expected: May need adjustments

- [ ] **Step 3: Fix and verify tests pass**

```bash
# Run and fix any issues
```

- [ ] **Step 4: Commit**

```bash
git add dooz_server/tests/test_integration.py
git commit -m "test: add integration tests"
```

---

## Chunk 11: Final Verification

### Task 11: Run all tests and verify server starts

**Files:**
- N/A

- [ ] **Step 1: Run all tests**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server && python -m pytest dooz_server/tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Verify server can start**

Run: `cd /Users/taoluo/projects/gcode/dooz/.worktrees/websocket-server/dooz_server && timeout 5 python -c "from main import app; print('App loaded successfully')" || true`
Expected: App loads without errors

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete WebSocket message server implementation"
```

---

## Chunk 12: Test Clients

### Task 12: Create 3 test client scripts

**Files:**
- Create: `dooz_server/test_clients/__init__.py`
- Create: `dooz_server/test_clients/client_base.py`
- Create: `dooz_server/test_clients/client_alice.py`
- Create: `dooz_server/test_clients/client_bob.py`
- Create: `dooz_server/test_clients/client_charlie.py`
- Create: `dooz_server/test_clients/test_clients.py`

- [ ] **Step 1: Create client package structure**

```python
# dooz_server/test_clients/__init__.py
"""Test clients for WebSocket message server."""

from .client_alice import run_alice
from .client_bob import run_bob
from .client_charlie import run_charlie

__all__ = ["run_alice", "run_bob", "run_charlie"]
```

- [ ] **Step 2: Create base client class**

```python
# dooz_server/test_clients/client_base.py
"""Base client class for WebSocket communication."""
import asyncio
import websockets
import json
from typing import Optional


class WebSocketClient:
    """Base WebSocket client with message handling."""
    
    def __init__(self, client_id: str, name: str, server_url: str = "ws://localhost:8000"):
        self.client_id = client_id
        self.name = name
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
    
    async def connect(self):
        """Connect to the WebSocket server."""
        uri = f"{self.server_url}/ws/{self.client_id}"
        self.websocket = await websockets.connect(uri)
        print(f"[{self.name}] Connected as {self.client_id}")
    
    async def send(self, message: dict):
        """Send a JSON message."""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
    
    async def receive(self) -> dict:
        """Receive a JSON message."""
        if self.websocket:
            data = await self.websocket.recv()
            return json.loads(data)
        return {}
    
    async def handle_message(self, message: dict):
        """Handle incoming message - override in subclass."""
        msg_type = message.get("type")
        print(f"[{self.name}] Received: {message}")
        
        if msg_type == "message":
            print(f"  >> Message from {message.get('from_client_id')}: {message.get('content')}")
        elif msg_type == "message_sent":
            success = message.get("success")
            print(f"  >> Message send result: {success}")
        elif msg_type == "pending_delivered":
            print(f"  >> Received {message.get('count')} pending messages")
        elif msg_type == "message_expired":
            print(f"  >> Message expired! To: {message.get('to_client_id')}, Content: {message.get('content')}")
        elif msg_type == "heartbeat_ack":
            print(f"  >> Heartbeat acknowledged")
    
    async def listen(self):
        """Listen for incoming messages."""
        self.running = True
        try:
            while self.running:
                message = await self.receive()
                if message:
                    await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.name}] Connection closed")
    
    async def send_heartbeat(self):
        """Send periodic heartbeat."""
        while self.running:
            await asyncio.sleep(10)
            await self.send({"type": "heartbeat"})
    
    async def close(self):
        """Close the connection."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
```

- [ ] **Step 3: Create Alice client**

```python
# dooz_server/test_clients/client_alice.py
"""Alice - Test client 1."""
import asyncio
from .client_base import WebSocketClient


class AliceClient(WebSocketClient):
    """Alice client with interactive commands."""
    
    def __init__(self):
        super().__init__(
            client_id="alice-001",
            name="Alice"
        )
    
    async def handle_message(self, message: dict):
        """Handle messages with Alice-specific behavior."""
        msg_type = message.get("type")
        
        if msg_type == "message":
            print(f"\n[Alice] New message from {message.get('from_client_id')}: {message.get('content')}")
        elif msg_type == "message_expired":
            print(f"\n[Alice] My message expired! Content: {message.get('content')}")
        else:
            await super().handle_message(message)
    
    async def interactive_loop(self):
        """Interactive command loop."""
        print("\n=== Alice's Commands ===")
        print("msg <client_id> <content> - Send message")
        print("list - List all clients")
        print("quit - Exit")
        print("========================\n")
        
        while self.running:
            try:
                cmd = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("Alice> ").strip()
                )
                
                if not cmd:
                    continue
                
                if cmd == "quit":
                    break
                elif cmd == "list":
                    # Use HTTP to list clients
                    import httpx
                    async with httpx.AsyncClient() as client:
                        resp = await client.get("http://localhost:8000/clients")
                        data = resp.json()
                        print(f"\nConnected clients ({data['total']}):")
                        for c in data['clients']:
                            print(f"  - {c['client_id']}: {c['name']}")
                elif cmd.startswith("msg "):
                    parts = cmd.split(" ", 2)
                    if len(parts) == 3:
                        _, to_client, content = parts
                        await self.send({
                            "type": "message",
                            "to_client_id": to_client,
                            "content": content,
                            "ttl_seconds": 3600
                        })
                        print(f"[Alice] Sent message to {to_client}")
            except EOFError:
                break


async def run_alice():
    """Run Alice client."""
    client = AliceClient()
    try:
        await client.connect()
        
        # Start listening and heartbeat in background
        listen_task = asyncio.create_task(client.listen())
        heartbeat_task = asyncio.create_task(client.send_heartbeat())
        
        # Run interactive loop
        await client.interactive_loop()
        
        # Cleanup
        client.running = False
        await asyncio.gather(listen_task, heartbeat_task, return_exceptions=True)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_alice())
```

- [ ] **Step 4: Create Bob client**

```python
# dooz_server/test_clients/client_bob.py
"""Bob - Test client 2."""
import asyncio
from .client_base import WebSocketClient


class BobClient(WebSocketClient):
    """Bob client with auto-response capability."""
    
    async def handle_message(self, message: dict):
        """Handle messages and auto-reply."""
        msg_type = message.get("type")
        
        if msg_type == "message":
            content = message.get("content", "")
            from_id = message.get("from_client_id")
            print(f"\n[Bob] Message from {from_id}: {content}")
            
            # Auto-reply
            await asyncio.sleep(0.5)
            await self.send({
                "type": "message",
                "to_client_id": from_id,
                "content": f"Bob received: {content}"
            })
            print(f"[Bob] Auto-replied to {from_id}")
        elif msg_type == "message_expired":
            print(f"\n[Bob] My message expired! Content: {message.get('content')}")
        else:
            await super().handle_message(message)


async def run_bob():
    """Run Bob client."""
    client = BobClient(
        client_id="bob-001",
        name="Bob"
    )
    try:
        await client.connect()
        
        # Start listening and heartbeat
        listen_task = asyncio.create_task(client.listen())
        heartbeat_task = asyncio.create_task(client.send_heartbeat())
        
        # Wait for commands
        print("\n[Bob] Running... Press Ctrl+C to exit")
        await asyncio.Future()  # Run forever
        
    except asyncio.CancelledError:
        pass
    finally:
        client.running = False
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_bob())
```

- [ ] **Step 5: Create Charlie client**

```python
# dooz_server/test_clients/client_charlie.py
"""Charlie - Test client 3."""
import asyncio
from .client_base import WebSocketClient


class CharlieClient(WebSocketClient):
    """Charlie client - simulates offline/online behavior."""
    
    def __init__(self):
        super().__init__(
            client_id="charlie-001",
            name="Charlie"
        )
        self.was_online = False
    
    async def handle_message(self, message: dict):
        """Handle messages with offline simulation."""
        msg_type = message.get("type")
        
        if msg_type == "message":
            print(f"\n[Charlie] NEW MESSAGE from {message.get('from_client_id')}: {message.get('content')}")
            if message.get("is_offline"):
                print("  (This was delivered from offline queue)")
        elif msg_type == "pending_delivered":
            print(f"\n[Charlie] Reconnected! Delivered {message.get('count')} pending messages")
            self.was_online = True
        elif msg_type == "message_expired":
            print(f"\n[Charlie] My message expired!")
        else:
            await super().handle_message(message)
    
    async def simulate_offline(self, duration: int = 10):
        """Simulate going offline for a duration."""
        print(f"\n[Charlie] Going offline for {duration} seconds...")
        self.running = False
        if self.websocket:
            await self.websocket.close()
        
        await asyncio.sleep(duration)
        
        print("[Charlie] Coming back online...")
        await self.connect()
        self.running = True


async def run_charlie():
    """Run Charlie client with offline simulation."""
    client = CharlieClient()
    try:
        await client.connect()
        
        listen_task = asyncio.create_task(client.listen())
        heartbeat_task = asyncio.create_task(client.send_heartbeat())
        
        print("\n[Charlie] Running... Type 'offline' to simulate going offline")
        print("[Charlie] Type 'msg <id> <msg>' to send messages")
        
        async def input_loop():
            while client.running:
                try:
                    cmd = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: input("Charlie> ").strip()
                    )
                    
                    if cmd == "offline":
                        await client.simulate_offline(10)
                        # Restart tasks after coming back online
                        listen_task = asyncio.create_task(client.listen())
                        heartbeat_task = asyncio.create_task(client.send_heartbeat())
                    elif cmd.startswith("msg "):
                        parts = cmd.split(" ", 2)
                        if len(parts) == 3:
                            await client.send({
                                "type": "message",
                                "to_client_id": parts[1],
                                "content": parts[2]
                            })
                except:
                    break
        
        await input_loop()
        
    finally:
        client.running = False
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_charlie())
```

- [ ] **Step 6: Create test script to run all clients**

```python
# dooz_server/test_clients/test_clients.py
"""Test script to run all clients."""
import asyncio
import sys


async def run_all_clients():
    """Run all three test clients concurrently."""
    from client_alice import run_alice
    from client_bob import run_bob
    from client_charlie import run_charlie
    
    print("=" * 50)
    print("Starting 3 test clients...")
    print("=" * 50)
    
    try:
        await asyncio.gather(
            run_alice(),
            run_bob(),
            run_charlie()
        )
    except KeyboardInterrupt:
        print("\n\nShutting down clients...")


if __name__ == "__main__":
    asyncio.run(run_all_clients())
```

- [ ] **Step 7: Test running the clients**

Run server first:
```bash
cd dooz_server
uv main:app --host 0.0.0.0 --port 8000
```

Run individual clients:
```bash
# Terminal 1
cd dooz_server
uv run python test_clients/client_alice.py

# Terminal 2
cd dooz_server
uv run python test_clients/client_bob.py

# Terminal 3
cd dooz_server
uv run python test_clients/client_charlie.py
```

- [ ] **Step 8: Commit**

```bash
git add dooz_server/test_clients/
git commit -m "feat: add 3 test client scripts for manual testing"
```

---

## Usage Instructions

### Starting the Server

```bash
cd dooz_server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Connecting a Client

```python
import asyncio
import websockets
import json

async def connect_client(client_id: str, name: str):
    uri = "ws://localhost:8000/ws/test-client-id"
    async with websockets.connect(uri) as websocket:
        # Send registration (optional - client_id is in URL)
        await websocket.send(json.dumps({
            "type": "register",
            "client_id": client_id,
            "name": name
        }))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            
            # Handle different message types
            if data.get("type") == "message":
                # New message received
                print(f"Message from {data['from_client_id']}: {data['content']}")
            elif data.get("type") == "pending_delivered":
                # Offline messages delivered on reconnect
                print(f"Delivered {data['count']} pending messages")
            elif data.get("type") == "message_expired":
                # Your sent message expired
                print(f"Message to {data['to_client_id']} expired: {data['content']}")

# Run: asyncio.run(connect_client("client-1", "Alice"))
```

### Heartbeat (Keep-Alive)

Clients should send periodic heartbeats to stay connected:

```python
async def heartbeat_loop(websocket):
    while True:
        await asyncio.sleep(10)  # Send every 10 seconds
        await websocket.send(json.dumps({
            "type": "heartbeat"
        }))

# Run both in parallel:
# await asyncio.gather(listen_loop, heartbeat_loop)
```

### Listing Clients (via HTTP)

```bash
curl http://localhost:8000/clients
```

### Sending a Message (via WebSocket)

```python
await websocket.send(json.dumps({
    "type": "message",
    "to_client_id": "recipient-client-id",
    "content": "Hello!",
    "ttl_seconds": 3600  # Optional: message expires in 1 hour
}))
```

Response:
```json
{
    "type": "message_sent",
    "success": true,
    "message": "Message queued for offline delivery",
    "message_id": "uuid-of-queued-message",
    "to_client_id": "recipient-client-id"
}
```

### Sending a Message (via HTTP API)

```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -d '{
    "to_client_id": "recipient-client-id",
    "content": "Hello via HTTP!",
    "ttl_seconds": 3600
  }' \
  -H "X-Client-ID: sender-client-id"
```

### Get Pending Messages

```bash
curl http://localhost:8000/messages/pending/client-id
```

### Check Expired Messages (Server-side)

```bash
curl -X POST http://localhost:8000/messages/check-expired
```

### Message Flow Examples

**1. Online to Online:**
- Client A sends message to Client B (who is online)
- Message delivered immediately via WebSocket

**2. Online to Offline:**
- Client A sends message to Client B (who is offline)
- Message stored in queue with TTL
- When Client B reconnects, pending messages delivered automatically

**3. Message Timeout:**
- If TTL expires before recipient reads message
- Sender receives `message_expired` notification
- Message removed from queue

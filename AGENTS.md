# Agent Instructions

This file provides guidelines for AI agents working in this codebase.

## Project Overview

This is a WebSocket message relay server (`dooz-server`) with a Python client library. The server manages client connections, handles message routing, and supports offline message queuing.

**Tech Stack:**
- Server: FastAPI + uvicorn + websockets
- Client: Python
- Testing: pytest + pytest-asyncio
- Python: 3.12+

---

## Issue Tracking (CRITICAL)

This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or external trackers.

### Quick Reference

```bash
bd ready              # Find unblocked work available
bd list --status=open # List all open issues
bd show <id>         # View issue details
bd create "Title" --type task --priority 2  # Create new issue
bd update <id> --status=in_progress  # Claim work
bd close <id>        # Complete work
bd dolt push         # Push beads to remote (REQUIRED at session end)
```

### Workflow Rules

- **Always use beads** for task tracking (`bd create`, `bd ready`, `bd close`)
- **Create issue BEFORE writing code** - check `bd ready` first
- **Never use** `bd edit` - it opens $EDITOR which blocks agents
- **Memory**: Use `bd remember "insight"` for persistent knowledge across sessions
- **Priority format**: Use 0-4 (0=critical, 2=medium, 4=backlog), NOT "high/medium/low"

### Session Close Protocol (MANDATORY)

Before ending ANY session, you MUST complete ALL steps:

1. **File issues** for remaining work
2. **Run quality gates**: `uv run pytest`
3. **Close completed work**: `bd close <id> --reason="Done"`
4. **Push beads**: `bd dolt push`
5. **Commit code**: `git add . && git commit -m "description"`
6. **Push code**: `git push`
7. **Verify**: `git status` must show "up to date with origin"

**CRITICAL**: Work is NOT complete until `git push` succeeds. Never skip this.

---

## Build, Test & Development Commands

### Server (dooz_server/)

**Install dependencies:**
```bash
cd dooz_server
uv sync  # Uses uv.lock for reproducible installs
```

**Run the server:**
```bash
cd dooz_server
uv run uvicorn dooz_server.main:app --reload --port 8000
# Or use the installed script:
uv run dooz-server
```

**Run all tests:**
```bash
cd dooz_server
uv run pytest
```

**Run a single test file:**
```bash
cd dooz_server
uv run pytest tests/test_router.py
```

**Run a single test by name:**
```bash
cd dooz_server
uv run pytest tests/test_router.py::test_health_check
uv run pytest -k "test_send_message"
```

**Run tests with verbose output:**
```bash
cd dooz_server
uv run pytest -v
```

**Run tests with coverage:**
```bash
cd dooz_server
uv run pytest --cov=dooz_server --cov-report=term-missing
```

### Client Library (dooz_python_client/)

**Install:**
```bash
cd client/dooz_python_client
uv sync
```

---

## Code Style Guidelines

### General Principles

- Write **clean, readable code** over clever code
- Follow **PEP 8** conventions with the specifics below
- Use **type hints** throughout (Python 3.12+)
- Keep functions **small and focused** (single responsibility)
- Add docstrings to public APIs

### Imports

**Organization (in order):**
1. Standard library (`import json`, `import asyncio`)
2. Third-party packages (`from fastapi import ...`, `import pytest`)
3. Local application (`from .client_manager import ...`)

```python
# Good
import json
import asyncio
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from pydantic import BaseModel, Field

from .client_manager import ClientManager
from .schemas import MessageRequest
```

**Avoid wildcard imports:**
```python
# Bad
from dooz_server import *

# Good
from dooz_server.router import router
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | snake_case | `client_manager.py` |
| Classes | PascalCase | `class ClientManager:` |
| Functions | snake_case | `def get_client_manager():` |
| Variables | snake_case | `client_id = "abc"` |
| Constants | UPPER_SNAKE | `MAX_CONNECTIONS = 100` |
| Type aliases | PascalCase | `MessageHandler = ...` |

```python
# Classes
class ConnectionManager:
    pass

# Functions and variables
def get_client_manager() -> ClientManager:
    client_id = "user-123"
    return client_manager

# Constants
DEFAULT_TIMEOUT = 30
MAX_MESSAGE_SIZE = 1024 * 1024
```

### Type Hints

**Always use type hints for function signatures:**

```python
# Good
def send_message(
    from_client_id: str,
    to_client_id: str,
    content: str,
    ttl_seconds: Optional[int] = 3600
) -> tuple[bool, str, Optional[str]]:
    ...

def get_client_info(client_id: str) -> Optional[ClientInfo]:
    ...

# For complex types, use typing module
from typing import Optional, Annotated
from collections.abc import AsyncIterator
```

### Pydantic Models

Use Pydantic v2 for data validation:

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator

class ClientProfile(BaseModel):
    """Profile information for a registered client."""
    model_config = ConfigDict(extra='ignore')  # Ignore unknown fields
    
    device_id: str = Field(..., min_length=1, description="Unique device identifier")
    name: str = Field(..., min_length=1)
    role: str
    extra_info: Optional[str] = Field(default=None)
    skills: list[tuple[str, str]] = Field(default_factory=list)

    @field_validator('device_id', 'name', mode='before')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v
```

### Error Handling

**Use exceptions for unexpected errors, return values for expected failures:**

```python
# Good - return tuple for expected failure cases
def send_message(from_client_id: str, to_client_id: str, content: str):
    recipient = self.client_manager.get_client_info(to_client_id)
    if not recipient:
        return (False, "Recipient not found", None)  # Expected failure
    # ... success case

# Good - raise for unexpected errors
async def connect(self, client_id: str, websocket: WebSocket):
    try:
        await websocket.accept()
        self.active_connections[client_id] = websocket
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        raise  # Unexpected error, let caller handle
```

**Log appropriately:**
```python
import logging
logger = logging.getLogger("dooz_server")

# Use appropriate log levels
logger.debug(f"Processing message: {message_id}")
logger.info(f"Client connected: {client_id}")
logger.warning(f"Client not found: {client_id}")
logger.error(f"Failed to send message: {e}")
```

### Async/Await

**Use async for I/O operations:**

```python
# Good - async for WebSocket operations
async def connect(self, client_id: str, websocket: WebSocket):
    await websocket.accept()
    self.active_connections[client_id] = websocket

async def send_personal_message(self, message: dict, client_id: str):
    if client_id in self.active_connections:
        await self.active_connections[client_id].send_json(message)

# Mark async test functions
@pytest.mark.asyncio
async def test_websocket_connection():
    ...
```

### Testing Conventions

**Use pytest fixtures:**

```python
@pytest.fixture
def client_manager():
    return ClientManager()

@pytest.fixture
def message_handler(client_manager):
    return MessageHandler(client_manager, MessageQueue())

def test_send_message(message_handler, client_manager):
    sender_id = client_manager.register_client("sender")
    recipient_id = client_manager.register_client("recipient")
    
    success, msg, msg_id = message_handler.send_message(
        sender_id, recipient_id, "Hello!"
    )
    assert success is True
```

**Mock external dependencies:**

```python
from unittest.mock import Mock, AsyncMock

def test_with_mock_websocket(message_handler, client_manager):
    mock_ws = Mock()
    mock_ws.send_json = AsyncMock()
    client_manager.add_connection("recipient", mock_ws)
    # ...
```

### FastAPI Patterns

**Use dependency injection:**

```python
from fastapi import APIRouter, Depends
from typing import Annotated

router = APIRouter()

def get_client_manager() -> ClientManager:
    global _client_manager
    if _client_manager is None:
        _client_manager = ClientManager()
    return _client_manager

@router.get("/clients")
async def list_clients(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)]
):
    return client_manager.get_all_clients()
```

---

## Non-Interactive Shell Commands

**ALWAYS use non-interactive flags** with file operations:

```bash
# Force overwrite without prompting
cp -f source dest
mv -f source dest
rm -f file

# For recursive operations
rm -rf directory
cp -rf source dest
```

---

## File Structure

```
dooz/
├── dooz_server/              # Server package
│   ├── src/dooz_server/      # Source code
│   │   ├── __init__.py
│   │   ├── main.py           # App entry point
│   │   ├── router.py         # FastAPI routes
│   │   ├── client_manager.py
│   │   ├── message_handler.py
│   │   ├── message_queue.py
│   │   ├── heartbeat.py
│   │   └── schemas.py       # Pydantic models
│   ├── tests/                # Test suite
│   └── pyproject.toml
├── client/
│   └── dooz_python_client/  # Python client library
├── .opencode/                # OpenCode configuration
└── AGENTS.md                # This file
```

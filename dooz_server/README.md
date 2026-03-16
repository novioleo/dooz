# dooz_server

<p align="center">
  <strong>WebSocket Message Relay Server</strong><br/>
  The core server component of the dooz distributed multi-agent system.
</p>

<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.12+-blue" alt="Python">
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-0.115+-green" alt="FastAPI">
  </a>
</p>

---

## What is dooz_server?

dooz_server is a **WebSocket-based message relay server** that acts as the communication backbone for the dooz distributed multi-agent system.

### Key Features

- **WebSocket Communication** — Real-time bidirectional messaging between agents
- **Message Routing** — Intelligent message delivery to connected clients
- **Offline Message Queue** — Stores messages for disconnected clients
- **Heartbeat Monitoring** — Detects and handles disconnected clients
- **System Agents** — Built-in AI agent support (DoozAgent, TaskScheduler)
- **Sub-agent Connection** — Can connect to other dooz servers as a nested agent

---

## 🌳 Infinite Nesting Support

dooz_server is designed with **infinite nesting** in mind — any server can act as a sub-agent to another server.

```
Root Server (Level 0)
    │
    ├── Sub Agent Server (Level 1) ──▶ Can further nest...
    │       │
    │       └── Sub-Sub Server (Level 2)
    │
    └── Sub Agent Server (Level 1)
            │
            └── Sub-Sub Server (Level 2)
                    │
                    └── ... (unlimited depth)
```

### How Sub-agent Connection Works

1. A dooz_server can connect to another dooz_server via WebSocket
2. The connecting server registers as a sub-agent
3. Task delegation flows down the hierarchy
4. Results flow back up to the root coordinator

---

## Quick Start

### Installation

```bash
cd dooz_server
uv sync
```

### Running the Server

```bash
# Using uvicorn directly
uv run uvicorn dooz_server.main:app --reload --port 8000

# Or using the installed script
uv run dooz-server
```

### Running Tests

```bash
uv run pytest
```

---

## Architecture

### Core Components

| Module | Description |
|--------|-------------|
| `router.py` | FastAPI routes and WebSocket endpoints |
| `client_manager.py` | Manages connected clients and their profiles |
| `message_handler.py` | Handles message sending and routing |
| `message_queue.py` | Offline message storage and delivery |
| `heartbeat.py` | Connection health monitoring |
| `system_agents/` | AI agent implementations |

### Message Flow

```
Client A ──WebSocket──▶ dooz_server ──▶ Client B
                              │
                              ▼
                       [Message Queue]
                              │
                              ▼
                       [Offline Delivery]
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/clients` | GET | List all connected clients |
| `/clients/{client_id}` | GET | Get client info |
| `/message` | POST | Send a message |
| `/ws/{client_id}` | WebSocket | WebSocket connection |

---

## Configuration

Configuration is managed via environment variables or `pyproject.toml`:

```python
# Default settings
HOST = "0.0.0.0"
PORT = 8000
HEARTBEAT_TIMEOUT = 30  # seconds
MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
```

---

## System Agents

### DoozAgent

AI agent that processes user messages and coordinates with sub-agents:

```python
from dooz_server.system_agents.dooz_agent import DoozAgent

agent = DoozAgent(
    config={
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
        "api_key": "sk-..."
    },
    prompt_loader=loader
)
```

### TaskScheduler

Manages task distribution to sub-agents:

```python
from dooz_server.system_agents.task_scheduler import TaskScheduler

scheduler = TaskScheduler(ws_manager)
task_id = await scheduler.submit_task(Task(agent_id="sub-1", goal="process data"))
```

---

## Status

Early MVP stage — actively developing!

---

<p align="center">Made with ❤️ by Novio</p>

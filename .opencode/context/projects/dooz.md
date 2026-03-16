# dooz Project Context

**Version**: 3.0  
**Last Updated**: 2026-03-16  
**Status**: Active Development (MVP Phase)

---

## Project Overview

**dooz** is a distributed multi-agent collaboration system with a unique **infinite nesting** design philosophy.

### Core Vision

> "One sentence — the device thinks, acts, checks, and reports by itself."

### Core Design Philosophy: Infinite Nesting

The defining characteristic of dooz is **infinite nesting** — any dooz server can act as a sub-agent to another dooz server, creating unlimited hierarchical structures.

```
Root Dooz Server (Level 0)
    │
    ├── Sub Agent Server (Level 1) ──▶ Can further nest...
    │       │
    │       └── Sub-Sub Server (Level 2)
    │               │
    │               └── ... (unlimited depth)
    │
    └── Sub Agent Server (Level 1)
            │
            └── ... (unlimited depth)
```

**Why Infinite Nesting?**
- **Scalability**: Handle millions of devices by organizing in hierarchical groups
- **Fault tolerance**: Local failures don't cascade to entire system
- **Geographic optimization**: Group devices by location, network proximity
- **Natural mapping**: Mirrors how organizations and biological systems work

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Server | FastAPI + uvicorn + websockets | Latest |
| Client | Python | 3.12+ |
| Testing | pytest + pytest-asyncio | Latest |
| AI Agents | Claude Agent SDK | Latest |

---

## Project Structure

```
dooz/
├── dooz_server/              # Server package
│   ├── src/dooz_server/      # Source code
│   │   ├── main.py           # App entry point
│   │   ├── router.py         # FastAPI routes + WebSocket
│   │   ├── client_manager.py # Client connection management
│   │   ├── message_handler.py # Message routing
│   │   ├── message_queue.py  # Offline message storage
│   │   ├── heartbeat.py      # Connection health monitoring
│   │   ├── schemas.py        # Pydantic models
│   │   └── system_agents/    # AI agent implementations
│   │       ├── dooz_agent.py    # Dooz AI agent
│   │       ├── task_scheduler.py # Task distribution
│   │       └── loader.py         # Prompt loader
│   └── tests/                # Test suite
├── client/
│   └── dooz_python_client/  # Python client library
├── docs/
│   ├── dev/                  # Development docs
│   └── user/                 # User docs
└── .opencode/                # OpenCode configuration
    └── context/              # Context files
```

---

## Core Components

### dooz_server

WebSocket-based message relay server with:

- **Real-time messaging** via WebSocket connections
- **Message routing** between connected clients
- **Offline message queue** for disconnected clients
- **Heartbeat monitoring** for connection health
- **System agents** (DoozAgent, TaskScheduler) for AI task execution
- **Sub-agent connection** support for infinite nesting

### Key Modules

| Module | Responsibility |
|--------|----------------|
| `router.py` | FastAPI routes, WebSocket endpoints |
| `client_manager.py` | Track connected clients and profiles |
| `message_handler.py` | Route messages to recipients |
| `message_queue.py` | Store/retrieve offline messages |
| `heartbeat.py` | Detect and handle disconnections |
| `system_agents/` | AI agent implementations |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/clients` | GET | List all connected clients |
| `/clients/{client_id}` | GET | Get client info |
| `/message` | POST | Send a message |
| `/ws/{client_id}` | WebSocket | WebSocket connection |

---

## Message Protocol

### Client Messages

```json
{
  "type": "message",
  "from": "client-a",
  "to": "client-b",
  "content": "Hello!",
  "timestamp": "2026-03-16T10:00:00Z"
}
```

### Task Messages (for sub-agent)

```json
{
  "type": "task_submit",
  "task_id": "task-123",
  "agent_id": "sub-agent-1",
  "goal": "Process this data"
}
```

---

## Code Standards

All code must follow:

1. **Modular Design** — Single responsibility, clear interfaces
2. **Type Hints** — Full Python type annotations (3.12+)
3. **Async/Await** — Use async for I/O operations
4. **Error Handling** — Return tuples for expected failures, raise for unexpected
5. **Pydantic v2** — Use for data validation

See `.opencode/context/core/standards/code-quality.md` for detailed standards.

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `client_manager.py` |
| Classes | PascalCase | `class ClientManager:` |
| Functions | snake_case | `def get_client_manager():` |
| Variables | snake_case | `client_id = "abc"` |
| Constants | UPPER_SNAKE | `MAX_CONNECTIONS = 100` |

---

## Running the Server

```bash
cd dooz_server
uv sync
uv run uvicorn dooz_server.main:app --reload --port 8000
```

## Running Tests

```bash
cd dooz_server
uv run pytest
```

---

## MVP Milestones

| Milestone | Description | Status |
|-----------|-------------|--------|
| M1 | Project structure & README | ✅ Complete |
| M2 | WebSocket server with message relay | ✅ Complete |
| M3 | Offline message queue | ✅ Complete |
| M4 | System agents (DoozAgent) | ✅ Complete |
| M5 | Sub-agent connection support | 🔄 In Progress |
| M6 | Python client library | ⏳ Pending |

---

## Key Design Decisions

### Why WebSocket?

- Real-time bidirectional communication
- Lower overhead than HTTP polling
- Native support in browsers and most platforms

### Why FastAPI?

- Modern Python async framework
- Built-in validation with Pydantic
- Easy WebSocket integration
- Auto-generated API docs

### Why Infinite Nesting?

- Natural hierarchical organization
- Scales to millions of devices
- Fault-tolerant distributed architecture
- Matches real-world organizational patterns

---

## Reference Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- **Context Files**: See `.opencode/context/project-intelligence/`

---

## Notes

- Current implementation: FastAPI + WebSocket + Python
- Original ROS2 design deferred to Phase 2
- Focus now: server stability and client library
- Infinite nesting is the core differentiating feature

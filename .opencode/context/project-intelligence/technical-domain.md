<!-- Context: project-intelligence/technical | Priority: critical | Version: 3.0 | Updated: 2026-03-16 -->

# Technical Domain

> dooz technical foundation: WebSocket-based distributed agent system with Python server and client.

## Quick Reference

- **Purpose**: Understand dooz architecture, tech stack, and development patterns
- **Update When**: Tech stack changes, new components, architecture decisions
- **Audience**: Developers building the server, client library, or system agents

---

## Primary Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Server | FastAPI + uvicorn + websockets | Latest | Modern async Python, WebSocket support, auto-docs |
| Client | Python | 3.12+ | Simple, widespread, async-native |
| Testing | pytest + pytest-asyncio | Latest | Async testing support |
| AI Agents | Claude Agent SDK | Latest | LLM-powered task execution |
| Message Format | JSON | - | Simple, widely supported |

---

## Core Design Philosophy: Infinite Nesting

The defining characteristic of dooz is **infinite nesting** — any dooz server can act as a sub-agent to another dooz server.

```
Root Dooz Server (Level 0)
    │
    ├── Sub Agent Server (Level 1)
    │       │
    │       └── Sub-Sub Server (Level 2)
    │               │
    │               └── ... (unlimited depth)
    │
    └── Sub Agent Server (Level 1)
            │
            └── ... (unlimited depth)
```

**Benefits:**
- **Scalability**: Organize millions of devices hierarchically
- **Fault tolerance**: Local failures don't cascade
- **Geographic optimization**: Group by location/proximity
- **Natural mapping**: Mirrors organizational/biological patterns

---

## Architecture Pattern

```
Type: Agent-based distributed system (hierarchical)
Pattern: Infinite nesting with WebSocket communication
```

### Why This Architecture?

- **WebSocket**: Real-time bidirectional messaging, low overhead
- **Hierarchical coordination**: Tasks flow down, results flow up
- **Sub-agent protocol**: Standardized task delegation between servers
- **Offline message queue**: Handles disconnected clients gracefully

---

## Project Structure

```
dooz/
├── dooz_server/                     # Server package
│   ├── src/dooz_server/
│   │   ├── main.py                 # App entry point
│   │   ├── router.py               # FastAPI routes + WebSocket endpoints
│   │   ├── client_manager.py       # Connected client management
│   │   ├── message_handler.py      # Message routing logic
│   │   ├── message_queue.py        # Offline message storage
│   │   ├── heartbeat.py            # Connection health monitoring
│   │   ├── schemas.py              # Pydantic models
│   │   └── system_agents/          # AI agent implementations
│   │       ├── dooz_agent.py       # Dooz AI agent
│   │       ├── task_scheduler.py   # Task distribution to sub-agents
│   │       └── loader.py           # Prompt loader
│   └── tests/                      # Test suite
├── client/
│   └── dooz_python_client/         # Python client library
├── docs/
│   ├── dev/                        # Development docs
│   └── user/                        # User docs
└── .opencode/
    └── context/                     # Context files
```

---

## Key Technical Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| FastAPI + WebSocket | Modern async framework, native WebSocket, auto API docs | Fast development, easy debugging |
| Python 3.12+ | Native async/await, type hints, modern syntax | Clean, maintainable code |
| JSON messages | Simple, universal, easy to debug | Broad compatibility |
| Task delegation protocol | Standardized sub-agent communication | Enables infinite nesting |
| Offline message queue | Store messages for disconnected clients | Reliability, eventual delivery |

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

### Task Messages (Sub-agent Protocol)

```json
{
  "type": "task_submit",
  "task_id": "task-123",
  "agent_id": "sub-agent-1",
  "goal": "Process this data"
}
```

```json
{
  "type": "task_result",
  "task_id": "task-123",
  "success": true,
  "result": "Processed 100 items"
}
```

---

## Development Environment

### Server Setup

```bash
cd dooz_server
uv sync
uv run uvicorn dooz_server.main:app --reload --port 8000
```

### Running Tests

```bash
cd dooz_server
uv run pytest
uv run pytest --cov=dooz_server --cov-report=term-missing
```

### Code Quality

```bash
# Type checking (if mypy configured)
uv run mypy dooz_server

# Linting (if ruff configured)
uv run ruff check dooz_server
```

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `client_manager.py` |
| Classes | PascalCase | `class ClientManager:` |
| Functions | snake_case | `def get_client_manager():` |
| Variables | snake_case | `client_id = "abc"` |
| Constants | UPPER_SNAKE | `MAX_CONNECTIONS = 100` |
| Type aliases | PascalCase | `MessageHandler = ...` |

---

## MVP Milestones

| Milestone | Status | Description |
|-----------|--------|-------------|
| M1 | ✅ Complete | Project structure, README |
| M2 | ✅ Complete | WebSocket server with message relay |
| M3 | ✅ Complete | Offline message queue |
| M4 | ✅ Complete | System agents (DoozAgent) |
| M5 | 🔄 In Progress | Sub-agent connection (infinite nesting) |
| M6 | ⏳ Pending | Python client library |

---

## Related Files

- `business-domain.md` - Business vision and problem statement
- `business-tech-bridge.md` - How business needs map to technical solutions
- `decisions-log.md` - Full decision history
- `projects/dooz.md` - Project context overview

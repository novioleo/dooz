# dooz Project Context

**Version**: 4.0  
**Last Updated**: 2026-03-18  
**Status**: Active Development (MQTT Architecture Migration)

---

## Project Overview

**dooz** is a distributed multi-agent collaboration system with a unique **infinite nesting** design philosophy, now using MQTT for inter-agent communication.

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
| Core | Python | 3.12+ |
| MQTT Broker | NanoMQ | Latest |
| CLI ↔ Daemon | WebSocket | Latest |
| Agent Communication | MQTT 5.0 | Latest |
| Async | asyncio | Built-in |
| Validation | Pydantic v2 | Latest |
| Config | PyYAML | Latest |
| Testing | pytest + pytest-asyncio | Latest |

---

## Project Structure

```
dooz/
├── dooz_daemon/              # Daemon package (核心进程管理器)
│   ├── src/
│   │   └── dooz_daemon/
│   │       ├── __init__.py
│   │       ├── __main__.py      # 入口点: dooz-daemon
│   │       ├── daemon.py        # 主 Daemon 类
│   │       ├── agent_manager.py  # Agent 进程生命周期管理
│   │       ├── mqtt_client.py   # MQTT 客户端
│   │       ├── websocket_server.py  # WebSocket 服务器 (CLI 连接)
│   │       ├── router.py        # 消息路由
│   │       ├── config.py        # 配置加载
│   │       ├── schemas/         # Pydantic 模型
│   │       │   ├── dooz.py
│   │       │   └── agent.py
│   │       ├── loader/          # YAML 加载器
│   │       │   ├── dooz_loader.py
│   │       │   └── agent_loader.py
│   │       └── agents/          # System Agents (内置)
│   │           ├── base.py
│   │           ├── monitor.py   # Monitor Agent (role: system)
│   │           ├── orchestrator.py  # Orchestrator Agent (role: system)
│   │           └── scheduler.py # Task Scheduler (role: system)
│   │
│   ├── definitions/            # YAML 定义文件
│   │   ├── dooz/               # Dooz 定义
│   │   │   ├── home-dooz.yaml
│   │   │   └── office-dooz.yaml
│   │   └── agents/             # Agent 定义
│   │       ├── light-agent.yaml
│   │       └── speaker-agent.yaml
│   │
│   ├── tests/
│   └── pyproject.toml
│
├── dooz_cli/                  # CLI 包 (用户界面)
│   ├── src/
│   │   └── dooz_cli/
│   │       ├── __init__.py
│   │       ├── __main__.py     # 入口点: dooz
│   │       ├── cli.py          # CLI 主界面
│   │       ├── websocket_client.py  # WebSocket 客户端
│   │       ├── clarification/  # Clarification Agent
│   │       │   ├── agent.py
│   │       │   ├── intent_detector.py
│   │       │   ├── questions.py
│   │       │   └── state.py
│   │       └── config.py
│   ├── tests/
│   └── pyproject.toml
│
├── docs/
│   └── superpowers/
│       ├── specs/              # 架构设计文档
│       └── plans/              # 实现计划
│
└── prompts/                    # Prompt 文件 (给 Orchestrator Agent)
    ├── 00_system_role.md
    ├── 10_available_agents.md
    └── 20_task_template.md
```

---

## Core Components

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLI                                    │
│  ┌──────────────────────┐                                       │
│  │ Clarification Agent  │ ← User (interactive chat)            │
│  └──────────┬───────────┘                                       │
│             │ WS                                                │
└─────────────┼───────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Daemon                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • WebSocket Server (CLI connection)                        │ │
│  │ • Agent Process Manager (spawn/kill agents)                │ │
│  │ • Message Router (CLI ↔ MQTT ↔ Agents)                    │ │
│  │ • MQTT Client (publish/subscribe)                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  所有 Agent 都是 Daemon 拉起的独立进程，区别只是 role/权限           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Agents (按 role 区分)                                        │ │
│  │  • monitor     → role: system (监控)                      │ │
│  │  • dooz        → role: system (主 Agent)                  │ │
│  │  • scheduler   → role: system (任务分发)                  │ │
│  │  • light       → role: sub-agent (业务 Agent)             │ │
│  │  • speaker     → role: sub-agent (业务 Agent)             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ MQTT
                              ▼
                    ┌─────────────────┐
                    │   NanoMQ        │
                    │   Broker        │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ dooz_1_1/      │ │ dooz_1_1/      │ │ dooz_1_1/      │
│ agents/monitor │ │ agents/dooz    │ │ agents/light   │
│ (role:system)  │ │ (role:system) │ │ (role:sub)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### dooz_daemon

守护进程，负责：
- WebSocket 服务器 (CLI 连接)
- Agent/Dooz 进程生命周期管理
- MQTT 客户端 (发布/订阅)
- 消息路由 (CLI ↔ MQTT ↔ Agents)
- 根据消息中的 dooz_id 路由到对应的 Dooz

### dooz_cli

命令行界面，负责：
- WebSocket 客户端连接 Daemon
- 内置 Clarification Agent (非 MQTT)
- 多轮交互式聊天澄清用户需求
- 只与顶层 Dooz 交互 (通过 dooz_id 指定)

### Key Modules (dooz_daemon)

| Module | Responsibility |
|--------|----------------|
| `daemon.py` | 主 Daemon 类，进程管理 |
| `agent_manager.py` | Agent 进程生命周期 (spawn/kill) |
| `mqtt_client.py` | MQTT 连接和消息收发 |
| `websocket_server.py` | WebSocket 服务器 (CLI 连接) |
| `router.py` | 消息路由 |
| `config.py` | 配置加载 (YAML) |
| `loader/` | YAML 定义文件加载器 |
| `agents/` | System Agents (Monitor, Orchestrator, Scheduler) |

### Agent Roles

**核心概念：** 所有 Agent 都是平等的进程，区别只是 role 不同。

```
┌─────────────────────────────────────────────────────────┐
│  Dooz: dooz_1_1                                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │ role: system (内置)                               │  │
│  │  • monitor     → 跟踪本 dooz 内 agents 心跳      │  │
│  │  • orchestrator → 主 Agent，处理用户请求         │  │
│  │  • scheduler   → 任务分发                        │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ role: sub-agent (业务定义，来自 YAML)             │  │
│  │  • light       → 灯光控制                         │  │
│  │  • speaker     → 音箱控制                         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**System Roles (内置):**
- `monitor` - 跟踪本 dooz 内 agents 心跳
- `orchestrator` - 主 Agent，处理用户请求
- `scheduler` - 任务分发

**Sub-agent Roles (YAML 定义):**
- 业务 Agent，来自 `definitions/agents/*.yaml`

---

## Communication Protocol

### CLI ↔ Daemon (WebSocket)

**Connection:**
```
ws://localhost:8765/cli
```

### CLI → Daemon Messages

```json
{
    "type": "user_message",
    "dooz_id": "my-home-dooz",
    "content": "播放音乐",
    "session_id": "uuid"
}
```

```json
{
    "type": "clarified_request",
    "dooz_id": "my-home-dooz",
    "session_id": "uuid",
    "clarified_goal": "用户想听舒缓的轻音乐",
    "original_request": "播放音乐"
}
```

### Daemon → CLI Messages

```json
{
    "type": "clarification_prompt",
    "session_id": "uuid",
    "question": "您是想打开客厅的灯光吗？"
}
```

```json
{
    "type": "task_result",
    "session_id": "uuid",
    "content": "客厅灯光已打开",
    "status": "completed",
    "task_id": "uuid"
}
```

```json
{
    "type": "error",
    "session_id": "uuid",
    "message": "任务执行失败",
    "details": "..."
}
```

### Agent ↔ Agent (MQTT)

**MQTT Topic Structure:**
```
dooz/
├── dooz_1_1/           # 顶层 Dooz (CLI 直接交互)
│   ├── system/
│   │   ├── monitor    # Monitor Agent
│   │   ├── dooz       # 该 Dooz 的主 Agent
│   │   └── scheduler  # Task Scheduler
│   ├── agents/
│   │   └── {agent_id}
│   ├── tasks/
│   │   └── {agent_id}
│   └── results/
│       └── {task_id}
│
├── dooz_2_3/           # 嵌套 Dooz
│   ├── system/
│   ├── agents/
│   ├── tasks/
│   └── results/
```

### Heartbeat (Agent → Monitor)

```json
{
    "type": "heartbeat",
    "dooz_id": "dooz_1_1",
    "agent_id": "light-agent",
    "timestamp": 1234567890,
    "status": "online"
}
```

### Task Message (Scheduler → Sub-Agent)

```json
{
    "type": "task",
    "task_id": "uuid",
    "sub_task_id": "1",
    "goal": "打开客厅灯光",
    "parameters": {"brightness": 80},
    "timeout": 30
}
```

### Task Result (Sub-Agent → Scheduler)

```json
{
    "type": "task_result",
    "task_id": "uuid",
    "sub_task_id": "1",
    "success": true,
    "result": "灯光已打开"
}
```

### MQTT Topic Summary

| Topic | Publisher | Subscriber | Description |
|-------|-----------|-------------|-------------|
| `dooz/{dooz_id}/system/monitor` | All Agents | Monitor Agent | Heartbeats |
| `dooz/{dooz_id}/system/monitor/response/{request_id}` | Monitor Agent | Orchestrator Agent | Query response |
| `dooz/{dooz_id}/system/orchestrator` | CLI/Daemon | Orchestrator Agent | User requests |
| `dooz/{dooz_id}/system/orchestrator` | Orchestrator Agent | Task Scheduler | Task submission |
| `dooz/{dooz_id}/system/scheduler` | Orchestrator Agent | Task Scheduler | Task submission |
| `dooz/{dooz_id}/tasks/{agent_id}` | Task Scheduler | Sub Agent | Task execution |
| `dooz/{dooz_id}/results/{task_id}` | Sub Agent | Task Scheduler | Results |

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

## Running the Daemon

```bash
cd dooz_daemon
uv sync
uv run dooz-daemon --config config.yaml
```

### Configuration (config.yaml)

```yaml
daemon:
  host: "0.0.0.0"
  port: 8765

mqtt:
  broker: "localhost"
  port: 1883
  client_id: "daemon"

agents:
  directory: "./definitions"
  system:
    - monitor
    - dooz
    - task-scheduler

monitor:
  heartbeat_interval: 10
  offline_threshold: 30
```

## Running the CLI

```bash
cd dooz_cli
uv sync
uv run dooz
```

## Running Tests

```bash
# Daemon tests
cd dooz_daemon
uv run pytest

# CLI tests
cd dooz_cli
uv run pytest
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [x] MQTT Broker Setup (NanoMQ)
- [x] Daemon Skeleton (WebSocket server, MQTT client, message routing)
- [x] CLI Skeleton (WebSocket client, basic command interface)

### Phase 2: System Agents
- [x] Monitor Agent (heartbeat reception, online status tracking)
- [x] Task Scheduler Agent (task distribution, result aggregation)
- [x] Orchestrator Agent (LLM integration, task creation)

### Phase 3: Business Agents
- [ ] Agent YAML Loader (load from directory, validate schema)
- [ ] Agent Process Spawner (spawn agent processes, manage lifecycle)

### Phase 4: Clarification Agent
- [ ] Clarification Agent (multi-turn chat, requirement clarification)

---

## Key Design Decisions

### Why MQTT?

- **Decoupled communication**: Agents don't need to know about each other
- **Built-in delivery guarantees**: QoS levels ensure message delivery
- **Topic-based routing**: Natural fit for multi-agent architecture
- **Scalability**: Supports millions of topics and messages
- **NanoMQ**: High-performance MQTT broker suitable for edge devices

### Why WebSocket for CLI ↔ Daemon?

- Real-time bidirectional communication
- Lower overhead than HTTP polling
- Native support in browsers and most platforms
- Simple text-based message format

### Why NanoMQ?

- Lightweight and high-performance
- Designed for edge computing
- Full MQTT 5.0 support
- Easy to deploy on various platforms

### Why Infinite Nesting?

- Natural hierarchical organization
- Scales to millions of devices
- Fault-tolerant distributed architecture
- Matches real-world organizational patterns

### Why Clarification Agent?

- Reduces ambiguity before task execution
- Improves user experience with natural conversation
- Can be enhanced with LLM in future
- Rule-based for MVP, fallback for reliability

---

## Reference Links

- [MQTT 5.0 Specification](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)
- [NanoMQ Documentation](https://nanomq.io/docs/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- **Architecture Design**: See `docs/superpowers/specs/2026-03-17-dooz-mqtt-architecture-design.md`
- **Implementation Plans**: See `docs/superpowers/plans/`
- **Context Files**: See `.opencode/context/project-intelligence/`

## YAML Schema Reference

### Dooz Definition (dooz.yaml)

```yaml
dooz:
  dooz_id: "dooz_1_1"        # 第一层第一个 Dooz (顶层)
  name: "智能家居"
  description: "控制家中智能设备"
  role: "dooz-group"          # 或 "dooz"
  agents:
    - light-agent
    - speaker-agent
  nested_dooz:
    - dooz_2_1               # 嵌套第二层第一个 Dooz
  capabilities:
    - smart_home_control
  skills:
    - name: "device_control"
      description: "控制智能家居设备"
  mqtt:
    topic_prefix: "dooz/dooz_1_1"
  config:
    auto_discover: true
```

### Agent Definition (agent.yaml)

```yaml
agent:
  agent_id: "light-agent"
  name: "灯光控制"
  description: "控制家中灯光"
  role: "sub-agent"
  capabilities:
    - light_on
    - light_off
    - light_brightness
  skills:
    - name: "light_control"
      description: "控制灯光开关和亮度"
  mqtt:
    topic: "light-control"   # 完整: dooz/dooz_1_1/agents/light-control
    subscribe:
      - "tasks/light-agent"
  config:
    device_type: "smart_light"
    brand: "xiaomi"
```

## Notes

- Current implementation: MQTT + WebSocket + Python
- Architecture follows agentic worker pattern
- Focus now: Phase 3 & 4 (Custom Agents + Clarification Agent)
- Infinite nesting is the core differentiating feature

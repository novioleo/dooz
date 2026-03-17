# Dooz MQTT Architecture Design

> **For agentic workers:** This is the design document. See implementation plan in `../plans/`.

**Goal:** Refactor dooz from WebSocket server to MQTT-based agent system with daemon + CLI architecture. All agents communicate via MQTT, with a front-end Clarification Agent for user interaction.

**Architecture:** Daemon process manages all agent processes (system + custom), communicates with CLI via WebSocket. System agents (Monitor, Dooz, Task Scheduler) are built-in. Custom agents loaded from YAML definitions. MQTT broker (NanoMQ) handles inter-agent communication.

**Tech Stack:** Python, NanoMQ (MQTT broker), WebSocket (CLI-Daemon), asyncio, Pydantic, PyYAML

---

## 1. System Overview

### 1.1 Components

| Component | Type | Description |
|-----------|------|-------------|
| CLI | User Interface | Command-line interface with Clarification Agent for user interaction |
| Daemon | Core | Manages agent processes, handles WebSocket connections, routes messages |
| Clarification Agent | Built-in (CLI) | Interactive multi-turn chatbot to clarify user requirements |
| Monitor Agent | System Agent | Receives heartbeats, tracks online agent status |
| Dooz Agent | System Agent | Main AI agent for task execution |
| Task Scheduler Agent | System Agent | Distributes tasks to sub-agents |
| Custom Agents | YAML-loaded | User-defined agents loaded from YAML files |
| MQTT Broker | Infrastructure | NanoMQ for inter-agent message routing |

### 1.2 Communication Flow

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
│  │ • MQTT Client (publish/subscribe)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ System Agents (built-in, not in YAML)                      │ │
│  │  • monitor-agent    → Track heartbeats                     │ │
│  │  • dooz-agent       → Main AI agent                        │ │
│  │  • task-scheduler   → Task distribution                    │ │
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
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ dooz/topic-A   │ │ dooz/topic-B   │ │ dooz/topic-N   │
│ (main agent)   │ │ (sub-agent)    │ │ (sub-agent)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 1.3 Process Architecture

```
PID: 1xxx              PID: 2xxx           PID: 3xxx           PID: Nxxx
┌──────────┐           ┌──────────┐        ┌──────────┐        ┌──────────┐
│   CLI    │◄───WS────►│  Daemon  │◄──MQTT─►│ Agent A  │◄──MQTT─►│ Agent N  │
│ (Python) │           │ (Python) │         │ (Python) │         │ (Python) │
└──────────┘           └──────────┘         └──────────┘         └──────────┘
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
              ┌─────────┐ ┌─────────┐ ┌─────────┐
              │Monitor  │ │  Dooz   │ │  Task   │
              │ Agent   │ │  Agent  │ │Scheduler│
              └─────────┘ └─────────┘ └─────────┘
```

---

## 2. Component Details

### 2.1 CLI (Command Line Interface)

**Responsibility:** User interaction entry point with Clarification Agent.

**Features:**
- WebSocket client connecting to Daemon
- Built-in Clarification Agent (non-MQ)
- Interactive multi-turn chat to clarify requirements
- Display results to user
- **只与顶层 Dooz 交互**（通过 dooz_id 指定）

**Connection:**
```bash
# Connect to Daemon
WS ws://localhost:8765/cli
```

**Message Format (CLI ↔ Daemon):**
```json
{
    "type": "user_message",
    "dooz_id": "my-home-dooz",  // 目标 Dooz
    "content": "播放音乐",
    "session_id": "uuid"
}
```

```json
{
    "type": "clarified_request",
    "dooz_id": "my-home-dooz",  // 目标 Dooz
    "session_id": "uuid",
    "clarified_goal": "用户想听舒缓的轻音乐",
    "original_request": "播放音乐"
}
```

```json
{
    "type": "task_result",
    "session_id": "uuid",
    "content": "已为您播放舒缓的轻音乐",
    "status": "completed"
}
```

### 2.2 Daemon (守护进程)

**Responsibility:** Central hub for agent management and message routing. Supports multiple Dooz instances simultaneously.

**Features:**
- WebSocket server for CLI connections
- Agent/Dooz process lifecycle management (spawn/kill)
- MQTT client for inter-agent communication
- Message routing between CLI, MQTT, and agents
- **根据消息中的 dooz_id 路由到对应的 Dooz**

**Startup:**
```bash
# Start daemon
dooz-daemon --config config.yaml --mqtt broker:1883
```

**Configuration (config.yaml):**
```yaml
daemon:
  host: "0.0.0.0"
  port: 8765
  mqtt:
    broker: "localhost"
    port: 1883
    client_id: "daemon"

definitions:
  directory: "./definitions"  # Dooz/Agent YAML 目录
  dooz:
    - "home-dooz"
    - "office-dooz"
  system_agents:
    - monitor
    - dooz
    - task-scheduler

monitor:
  heartbeat_interval: 10
  offline_threshold: 30
```

**Agent/Dooz Process Management:**
- 每个 Dooz 作为独立的进程组运行
- Agents run as separate processes within their Dooz namespace
- Daemon spawns Dooz and agent processes on startup
- Daemon monitors agent health via Monitor Agent
- Agents communicate via MQTT with dooz_id isolation

### 2.3 System Agents

**Note:** System agents are built-in, NOT loaded from YAML files.

#### 2.3.1 Monitor Agent

- **Purpose:** Track online sub-agents via heartbeat (per Dooz)
- **Device ID:** `monitor-agent`
- **MQTT Topic:** `dooz/{dooz_id}/system/monitor`
- **Heartbeat Format:**
```json
{
    "type": "heartbeat",
    "dooz_id": "dooz_1_1",
    "agent_id": "light-agent-001",
    "timestamp": 1234567890,
    "status": "online"
}
```
- **State Storage:** In-memory dict (can be extended to Redis/file)
- **Query Interface:** Responds to discovery requests from Dooz Agent

#### 2.3.2 Dooz Agent

- **Purpose:** Main AI agent for task execution
- **Device ID:** `dooz-agent`
- **MQTT Topic:** `dooz/{dooz_id}/system/dooz`
- **Features:**
  - Uses LLM for task understanding
  - Creates tasks for Task Scheduler
  - Blocks waiting for results
  - Queries Monitor Agent for available sub-agents (包括嵌套 dooz 的 agents)

**Query Protocol (Dooz → Monitor):**
```json
// Publish to: dooz/{dooz_id}/system/monitor
{
    "type": "query_agents",
    "request_id": "uuid",
    "capabilities": ["light_control"]  // Optional filter
}

// Subscribe to: dooz/{dooz_id}/system/monitor/response/{request_id}
{
    "type": "agent_list",
    "request_id": "uuid",
    "agents": [
        {"agent_id": "light-agent-001", "name": "客厅灯光", "capabilities": ["light_on", "light_off"]},
        {"agent_id": "speaker-agent-001", "name": "客厅音箱", "capabilities": ["play_music"]}
    ]
}
```

#### 2.3.3 Task Scheduler Agent

- **Purpose:** Distribute tasks to sub-agents in parallel (including nested dooz agents)
- **Device ID:** `task-scheduler`
- **MQTT Topic:** `dooz/{dooz_id}/system/scheduler`
- **Features:**
  - Receives task structure from Dooz Agent
  - Resolves agent_id to target MQTT topic (本 dooz 或嵌套 dooz)
  - Distributes sub-tasks to target agents
  - Aggregates results

**Agent ID 解析机制：**
```
agent_id: "light-agent" → dooz_1_1/tasks/light-agent (本 dooz)
agent_id: "nested-dooz/agent-C1" → dooz_2_3/tasks/agent-C1 (嵌套 dooz)
```

### 2.4 Custom Agents (YAML-defined)

**Location:** `./definitions/agents/*.yaml`

**Agent Definition (agent.yaml):**
```yaml
agent:
  id: "light-agent-001"
  name: "客厅灯光控制"
  description: "控制客厅灯光开关和亮度"
  role: "sub-agent"
  capabilities:
    - light_on
    - light_off
    - light_brightness
  skills:
    - name: "light_control"
      description: "控制灯光开关和亮度"
  mqtt:
    topic: "light-001"           # 完整: dooz/{dooz_id}/agents/light-001
    subscribe:
      - "tasks/light-001"       # 完整: dooz/{dooz_id}/tasks/light-001
  config:
    device_type: "smart_light"
    brand: "xiaomi"
```

**Loading:**
- Daemon scans `agents/` directory on startup
- Loads all `.yaml` files
- Spawns agent process for each

---

## 3. MQTT Topic Structure

### 3.1 Topic Hierarchy (Multi-Dooz Support)

**Dooz ID 格式：** `{level}_{index}`，例如：
- `dooz_1_1` - 第一层第一个 Dooz (顶层)
- `dooz_2_3` - 第二层第三个 Dooz (嵌套)
- `dooz_3_2` - 第三层第二个 Dooz

```
dooz/
├── dooz_1_1/           # 顶层 Dooz (CLI 直接交互)
│   ├── system/
│   │   ├── monitor    # Monitor Agent
│   │   ├── dooz       # 该 Dooz 的主 Agent
│   │   └── scheduler  # Task Scheduler
│   ├── agents/
│   │   ├── agent-A
│   │   └── ...
│   ├── tasks/
│   │   └── {agent_id}
│   └── results/
│       └── {task_id}
│
├── dooz_2_3/           # 第二层第三个 Dooz (嵌套)
│   ├── system/
│   ├── agents/
│   ├── tasks/
│   └── results/
```

**说明：**
- `{dooz_id}` 隔离不同的 Dooz 实例
- 同一个 MQTT broker 可以运行多个 Dooz (通过 dooz_id 区分)
- 每个 Dooz 有自己独立的 agent 命名空间

### 3.2 Dooz Group 嵌套

```
Dooz Group (dooz_1_1 - 顶层)
│
├── 包含的 sub-agent: agent-A, agent-B
│
└── 嵌套的 dooz: dooz_2_1
                      │
                      ├── sub-agent: agent-C1, agent-C2
                      │
                      └── 嵌套的 dooz: dooz_3_1
                              └── sub-agent: agent-C1-1
```

**嵌套路由规则：**
- `agent_id` 格式支持嵌套路径：`agent_id: "dooz_2_1/agent-C1"`
- Task Scheduler 解析 `agent_id` 中的 dooz 前缀，路由到对应的 MQTT topic
- 如果 agent_id 不包含 dooz 前缀，则默认使用当前 dooz

**示例：**
```
# 在 dooz_1_1 中分发任务
sub_task: { agent_id: "agent-A", goal: "打开灯光" }
  → 路由到 dooz_1_1/tasks/agent-A

sub_task: { agent_id: "dooz_2_1/agent-C1", goal: "关闭摄像头" }
  → 路由到 dooz_2_1/tasks/agent-C1
```

**交互规则：**
- CLI 只与**顶层 Dooz** (`dooz_1_x`) 交互
- 顶层 Dooz 的 Task Scheduler 负责解析 agent_id 并路由到正确的 dooz
- 嵌套的 Dooz 对 CLI 不可见（透明）

### 3.3 Message Types

| Topic | Publisher | Subscriber | Description |
|-------|-----------|-------------|-------------|
| `dooz/{dooz_id}/system/monitor` | All Agents (in this dooz) | Monitor Agent | Heartbeats |
| `dooz/{dooz_id}/system/monitor/response/{request_id}` | Monitor Agent | Dooz Agent | Query response |
| `dooz/{dooz_id}/system/dooz` | CLI/Daemon | Dooz Agent | User requests |
| `dooz/{dooz_id}/system/scheduler` | Dooz Agent | Task Scheduler | Task submission |
| `dooz/{dooz_id}/tasks/{agent_id}` | Task Scheduler | Sub Agent | Task execution |
| `dooz/{dooz_id}/results/{task_id}` | Sub Agent | Task Scheduler | Results |

---

## 4. WebSocket Protocol (CLI ↔ Daemon)

### 4.1 Connection

```bash
ws://localhost:8765/cli
```

### 4.2 Message Types

#### CLI → Daemon

```json
{
    "type": "user_message",
    "session_id": "uuid",
    "content": "打开客厅灯光"
}
```

```json
{
    "type": "clarified_request",
    "session_id": "uuid",
    "clarified_goal": "打开客厅灯光并播放舒缓音乐",
    "original_request": "打开灯光播放音乐"
}
```

#### Daemon → CLI

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

---

## 5. Data Structures

### 5.1 Dooz Definition (YAML Schema)

```python
class DoozDefinition(BaseModel):
    """Dooz 顶层配置 - 每个 dooz.yaml 定义一个 Dooz"""
    dooz_id: str = Field(
        ...,
        description="唯一标识符，格式: dooz_{level}_{index}，例如 dooz_1_1 (顶层), dooz_2_3 (第二层第三个)"
    )
    name: str = Field(..., description="人类可读名称")
    description: str = Field(default="", description="Dooz 描述")
    role: Literal["dooz", "dooz-group"] = Field(
        default="dooz",
        description="dooz: 单一 dooz; dooz-group: 包含嵌套 dooz 的组"
    )
    agents: list[str] = Field(
        default_factory=list,
        description="引用的 agent_id 列表 (来自同目录下的 agent yaml)"
    )
    nested_dooz: list[str] = Field(
        default_factory=list,
        description="嵌套的 dooz_id 列表"
    )
    capabilities: list[str] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    mqtt: MqttConfig
    config: dict = Field(default_factory=dict)

class Skill(BaseModel):
    name: str
    description: str

class MqttConfig(BaseModel):
    topic_prefix: str = Field(
        default="dooz/{dooz_id}",
        description="MQTT topic 前缀，自动包含 dooz_id"
    )
```

### 5.2 Agent Definition (YAML Schema)

```python
class AgentDefinition(BaseModel):
    """Agent 配置 - 每个 agent.yaml 定义一个 Agent"""
    agent_id: str = Field(..., description="唯一标识符")
    name: str = Field(..., description="人类可读名称")
    description: str = Field(default="", description="Agent 描述")
    role: Literal["sub-agent"] = Field(default="sub-agent")
    capabilities: list[str] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    mqtt: MqttConfig
    config: dict = Field(default_factory=dict)

class MqttConfig(BaseModel):
    topic: str  # 相对于 dooz/{dooz_id}/agents/
    subscribe: list[str] = Field(default_factory=list)
    publish: list[str] = Field(default_factory=list)
```

### 5.3 Task Structure

```python
class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: uuid4().hex)
    session_id: str
    dooz_id: str  # 目标 Dooz
    goal: str
    sub_tasks: list[SubTask] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

class SubTask(BaseModel):
    sub_task_id: str
    agent_id: str  # 目标 Agent (可以是本 dooz 的，也可以是嵌套 dooz 的)
    goal: str
    parameters: dict = Field(default_factory=dict)
    timeout: int = Field(default=30)
```

### 5.4 Task Result

```python
class SubTaskResult(BaseModel):
    sub_task_id: str
    agent_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None

class TaskResult(BaseModel):
    task_id: str
    session_id: str
    dooz_id: str
    status: Literal["completed", "failed", "partial"]
    sub_results: list[SubTaskResult]
```

### 5.4 Heartbeat

```python
class Heartbeat(BaseModel):
    agent_id: str
    timestamp: float
    status: Literal["online", "offline"]
    capabilities: list[str] = Field(default_factory=list)
```

---

## 6. Error Handling

### 6.1 Startup Errors

| Scenario | Handling |
|----------|----------|
| MQTT broker unavailable | Daemon fails to start, exits with error code 1 |
| Invalid agent YAML | Log error, skip that agent, continue with others |
| Port already in use | Exit with error, suggest different port |

### 6.2 Runtime Errors

| Scenario | Handling |
|----------|----------|
| MQTT broker disconnects | Agent attempts reconnect every 5s, max 3 retries |
| MQTT message lost | Use QoS 1 for task delivery (at-least-once) |
| Agent process crashes | Daemon logs error, removes from active list |
| WebSocket CLI disconnects | Session preserved for 60s, then cleanup |
| LLM API failure | Return error to user, allow retry |
| Task timeout | Sub-agent sends `task_failed`, Task Scheduler marks as failed |
| Malformed JSON message | Log error, skip message, continue |

### 6.3 Agent Lifecycle Errors

| Scenario | Handling |
|----------|----------|
| Agent doesn't send heartbeat for 30s | Monitor marks as offline, notifies Task Scheduler |
| Sub-agent disconnects mid-task | Task Scheduler waits for timeout, then marks failed |
| Task Scheduler receives no response | Returns partial results with failed status |

### 6.4 Graceful Shutdown

```
SIGTERM/SIGINT → 
  1. Stop accepting new CLI connections
  2. Wait 10s for in-flight tasks to complete
  3. Send SIGTERM to all agent processes
  4. Wait 5s for graceful shutdown
  5. Kill remaining processes
  6. Disconnect MQTT
  7. Exit
```

---

## 7. Agent Process Interface

### 7.1 Process Lifecycle

```
┌─────────────┐
│   Start     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│  Register   │────►│   Listen    │
│  to Monitor │     │  MQTT Topic │
└─────────────┘     └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Process    │
                    │   Task      │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Send      │
                    │   Result    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Repeat    │
                    └─────────────┘
```

### 7.2 Heartbeat Interval

- Default: **10 seconds**
- Agent sends heartbeat to `dooz/{dooz_id}/system/monitor`
- Monitor tracks last_seen timestamp
- Agent not heard from for **30 seconds** → marked as offline

### 7.3 Task Execution

- Agent subscribes to `dooz/{dooz_id}/tasks/{agent_id}`
- Receives task JSON
- Executes task (sync or async)
- Publishes result to `dooz/{dooz_id}/results/{task_id}`

**Task Message Format (Sub-Agent receives):**
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

**Result Message Format (Sub-Agent sends):**
```json
{
    "type": "task_result",
    "task_id": "uuid",
    "sub_task_id": "1",
    "success": true,
    "result": "灯光已打开"
}
```

---

## 8. Clarification Agent

### 8.1 Purpose

Front-facing chatbot to help users clarify their requirements before sending to the task queue. Built into CLI (not MQTT-based).

### 8.2 Implementation Details

**Approach:** Rule-based with optional LLM enhancement

**Clarification Strategy:**
- Parse user's intent using keyword matching and simple rules
- If ambiguous, ask clarifying questions (max 3 turns)
- When requirements are clear, send `clarified_request` to Daemon

**Clarification Rules:**
```
User Input → Intent Detection → [Ambiguous?] → [Ask Question | Send to Daemon]

Examples:
- "播放音乐" → intent=play_music, missing=room → "在哪个房间？"
- "打开灯光" → intent=light_on, missing=device → "客厅还是卧室？"
- "播放客厅音乐" → intent=play_music, room=living_room → Send to Daemon
```

**Max Turns:** 3 questions, after which force-sends best-effort interpretation

**Error Handling:**
- LLM fails: Fall back to rule-based parsing
- User disconnects: Session cleanup after 60s
- Intent still unclear after max turns: Send with `confidence: low`, let Dooz Agent handle ambiguity

**Failure Handling:**
- If clarification fails after max turns → send what we have with `confidence: low`
- User can always bypass clarification with `--force` flag

### 8.3 Flow

```
User: "播放音乐"
        │
        ▼
┌───────────────────┐
│ Clarification     │
│ Agent             │
│ "您想听什么类型    │
│ 的音乐？"          │
└─────────┬─────────┘
          │
User: "舒缓的"
          │
          ▼
┌───────────────────┐
│ Clarification     │
│ Agent             │
│ "在哪个房间播放？  │
└─────────┬─────────┘
          │
User: "客厅"
          │
          ▼
┌───────────────────┐
│ Clarification     │
│ Agent             │
│ "好的，为您在客   │
│ 厅播放舒缓音乐    │
│                   │
│ [Send to Daemon]  │
└───────────────────┘
```

### 8.4 Implementation

- Built into CLI (not an MQTT agent)
- Uses simple LLM or rule-based system
- When requirements are clear → sends `clarified_request` to Daemon

---

## 9. File Structure

### 9.1 Project Layout

```
dooz/
├── dooz_cli/                 # CLI package
│   ├── src/
│   │   └── dooz_cli/
│   │       ├── __init__.py
│   │       ├── main.py       # CLI entry point
│   │       ├── cli.py        # CLI interface
│   │       ├── websocket.py  # WS client
│   │       ├── clarification.py  # Clarification Agent
│   │       └── config.py     # CLI config
│   ├── tests/
│   └── pyproject.toml
│
├── dooz_daemon/              # Daemon package
│   ├── src/
│   │   └── dooz_daemon/
│   │       ├── __init__.py
│   │       ├── main.py       # Daemon entry point
│   │       ├── daemon.py     # Main daemon
│   │       ├── agent_manager.py    # Agent lifecycle
│   │       ├── mqtt_client.py       # MQTT client
│   │       ├── websocket_server.py  # WS server
│   │       ├── router.py     # Message routing
│   │       └── config.py     # Daemon config
│   │
│   ├── system_agents/        # System agents
│   │   ├── __init__.py
│   │   ├── base.py          # Base agent class
│   │   ├── monitor.py       # Monitor Agent
│   │   ├── dooz.py          # Dooz Agent
│   │   └── scheduler.py     # Task Scheduler
│   │
│   ├── definitions/          # Dooz/Agent YAML definitions
│   │   ├── dooz/
│   │   │   ├── home-dooz.yaml      # Dooz 定义
│   │   │   └── office-dooz.yaml   # 另一个 Dooz
│   │   └── agents/
│   │       ├── light-agent.yaml   # Agent 定义
│   │       └── speaker-agent.yaml
│   │
│   ├── tests/
│   └── pyproject.toml
│
├── docs/
│   └── superpowers/
│       ├── specs/
│       └── plans/
│
└── prompts/                  # Prompt files for Dooz Agent
    ├── 00_system_role.md
    ├── 10_available_agents.md
    └── 20_task_template.md
```

### 9.2 Dooz/Agent YAML 示例

**dooz.yaml (Dooz 定义):**
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

**agent.yaml (Agent 定义):**
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

### 9.3 Configuration Files

**config.yaml (Daemon):**
```yaml
daemon:
  host: "0.0.0.0"
  port: 8765

mqtt:
  broker: "localhost"
  port: 1883
  client_id: "daemon"

agents:
  directory: "./agents"
  system:
    - monitor
    - dooz
    - task-scheduler

monitor:
  heartbeat_interval: 10
  offline_threshold: 30
```

---

## 10. Implementation Phases

> **Note:** This spec covers the entire architecture. Each phase below will be implemented as a **separate plan**:
> - Plan 1: Core Infrastructure (Phase 1)
> - Plan 2: System Agents (Phase 2)
> - Plan 3: Custom Agents (Phase 3)
> - Plan 4: Clarification Agent (Phase 4)

### Phase 1: Core Infrastructure

1. **MQTT Broker Setup**
   - Install and configure NanoMQ
   - Test connectivity

2. **Daemon Skeleton**
   - WebSocket server for CLI
   - MQTT client
   - Message routing

3. **CLI Skeleton**
   - WebSocket client
   - Basic command interface

### Phase 2: System Agents

4. **Monitor Agent**
   - Heartbeat reception
   - Online status tracking
   - Query interface

5. **Task Scheduler Agent**
   - Task distribution
   - Result aggregation

6. **Dooz Agent**
   - LLM integration
   - Task creation

### Phase 3: Custom Agents

7. **Agent YAML Loader**
   - Load from directory
   - Validate schema

8. **Agent Process Spawner**
   - Spawn agent processes
   - Manage lifecycle

### Phase 4: Clarification Agent

9. **Clarification Agent**
   - Multi-turn chat
   - Requirement clarification

---

## 11. Security (MVP Scope)

> **Note:** This is an MVP design. Production deployments should add proper authentication.

| Area | MVP Approach | Production Enhancement |
|------|--------------|----------------------|
| CLI → Daemon | No auth (localhost only) | Token-based auth |
| MQTT | No auth | MQTT username/password or ACLs |
| Agent registration | Profile validation only | Signed certificates |
| Message integrity | None | Message signing |

---

## 12. Acceptance Criteria

- [ ] Daemon starts and listens on WebSocket port
- [ ] CLI connects to Daemon via WebSocket
- [ ] Monitor Agent tracks agent heartbeats
- [ ] Dooz Agent can query available sub-agents
- [ ] Task Scheduler distributes tasks to sub-agents
- [ ] Custom agents load from YAML files
- [ ] Clarification Agent performs multi-turn chat
- [ ] Results flow back to CLI correctly
- [ ] Agent offline detection works
- [ ] System handles multiple concurrent sessions

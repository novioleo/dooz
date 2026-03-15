# Dooz Agent Task Orchestration Design

> **For agentic workers:** This is the design document. See implementation plan in `../plans/`.

**Goal:** Implement a task orchestration system where Dooz Agent handles multi-turn conversation with users, creates tasks with sub-agents, and blocks until Task Scheduler returns results.

**Architecture:** Two system agents (Dooz Agent + Task Scheduler) run via FastAPI lifespan. Dooz Agent uses claude-agent-sdk for LLM对话, communicates via WebSocket. Task Scheduler is a simple component that distributes tasks to sub-agents in parallel. Prompts stored as MD files in prompts directory.

**Tech Stack:** Python, FastAPI, WebSocket, claude-agent-sdk==0.1.48

---

## 1. System Overview

### 1.1 Components

| Component | Type | Description |
|-----------|------|-------------|
| Dooz Agent | System Agent | Main AI agent using claude-agent-sdk for LLM conversation |
| Task Scheduler | System Agent | Simple component that distributes tasks to sub-agents and aggregates results |
| Client Registry | Core | Manages all connected clients (system + sub-agents) |
| Prompt Loader | Core | Loads prompt MD files from work directory |

### 1.2 Communication Flow

```
User <--WS--> Dooz Server <--WS--> Dooz Agent (claude-sdk)
                                          │
                                          │ Create task
                                          ▼
                               Task Scheduler
                                          │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
            Sub-Agent A            Sub-Agent B            Sub-Agent C
            (parallel)             (parallel)             (parallel)
                    └──────────────────────┼──────────────────────┘
                                           │
                                           ▼
                               Task Scheduler (aggregate)
                                           │
                                           ▼
                               Dooz Agent (result to user)
```

---

## 2. System Agents

### 2.1 Registration

System agents are registered via FastAPI lifespan to make them visible in the client registry:

```python
# lifespan startup - register in client manager
client_manager.register_client("dooz-agent", "Dooz Assistant", role="dooz")
client_manager.register_client("task-scheduler", "Task Scheduler", role="system")
```

**Note:** This registration makes system agents visible in the client registry so other agents can address them. However, **Dooz Agent and Task Scheduler connect to the server as external WebSocket clients** - they are not in-process components. The lifespan just pre-registers them so messages can be routed.

**IMPORTANT - Hardcoded IDs:**
These system agent IDs are **hardcoded** and must NOT be changed:
- `dooz-agent` - Main AI agent device_id
- `task-scheduler` - Task scheduler device_id

These IDs are referenced in prompt files and sub-agent expectations. If changed, the system will break.

### 2.2 Dooz Agent

- **device_id**: `dooz-agent`
- **Implementation**: Uses `ClaudeSDKClient` from claude-agent-sdk
- **Features**:
  - Multi-turn conversation via session
  - Block on task execution (WS wait)
  - Prompt from MD files
  - Task creation and submission

**LLM Configuration (via config.json):**
```json
{
    "llm": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "api_key": "${ANTHROPIC_API_KEY}"
    },
    "prompts": {
        "directory": "prompts"
    }
}
```

**OpenAI-Compatible Provider:**
```json
{
    "llm": {
        "provider": "openai-compatible",
        "model": "qwen-plus",
        "api_key": "${DASHSCOPE_API_KEY}",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
    "prompts": {
        "directory": "prompts"
    }
}
```

**Task Creation Trigger:**
- Dooz Agent uses LLM to determine if user's request requires sub-agent execution
- LLM returns response in format:
  ```
  Direct response: (plain text response to user)
  
  --OR--
  
  Tasks:
  [
    {"agent_id": "light-agent", "goal": "打开客厅灯光"},
    {"agent_id": "speaker-agent", "goal": "播放舒缓音乐"}
  ]
  ```
- Dooz Agent parses response to detect task structure
- If tasks detected → submit to Task Scheduler → block for result

### 2.3 Task Scheduler

- **device_id**: `task-scheduler`
- **Implementation**: Simple Python component (no LLM)
- **Features**:
  - Receive task structure
  - Distribute to sub-agents in parallel
  - Collect results with timeout handling
  - Aggregate and return results

---

## 3. Data Structures

### 3.1 Task Structure

```python
class Task(BaseModel):
    task_id: str              # UUID
    goal: str                 # User's final goal description
    sub_tasks: list[SubTask]  # List of sub-tasks

class SubTask(BaseModel):
    sub_task_id: str
    agent_id: str             # Target agent device_id
    goal: str                 # What this sub-agent should achieve
    parameters: dict = {}     # Optional parameters
```

**Validation:**
- If LLM returns malformed JSON → return error to user "Failed to parse task"
- If sub_task missing required fields → skip that sub-task, continue with others
- If agent_id not found → mark as failed in results

### 3.2 Task Result

```python
class SubTaskResult(BaseModel):
    sub_task_id: str
    success: bool
    result: Optional[str]      # Result message
    error: Optional[str]        # Error message if failed

class TaskResult(BaseModel):
    task_id: str
    status: Literal["completed", "failed", "partial"]
    sub_results: list[SubTaskResult]
```

### 3.3 Message Types

| Message Type | From | To | Description |
|--------------|------|-----|-------------|
| user_message | User | Dooz Agent | User's input |
| agent_response | Dooz Agent | User | Agent's response |
| task_submit | Dooz Agent | Task Scheduler | Submit task for execution |
| task_result | Task Scheduler | Dooz Agent | Aggregated task result |
| sub_task | Task Scheduler | Sub-Agent | Execute a sub-task |
| sub_task_result | Sub-Agent | Task Scheduler | Sub-task completion |
| task_failed | Sub-Agent | Task Scheduler | Sub-task failure (after retries) |

---

## 4. WebSocket Protocol

### 4.1 Connection

```
# Connect as dooz-agent (with profile)
WS /ws/dooz-agent?profile=%7B%22device_id%22%3A%22dooz-agent%22%2C%22name%22%3A%22Dooz%20Assistant%22%2C%22role%22%3A%22dooz%22%2C%22skills%22%3A%5B%5D%7D

# Connect as task-scheduler  
WS /ws/task-scheduler

# Connect as sub-agent (with profile containing skills)
WS /ws/light-agent-001?profile=%7B%22device_id%22%3A%22light-agent-001%22%2C%22name%22%3A%22Living%20Room%20Light%22%2C%22role%22%3A%22sub-agent%22%2C%22skills%22%3A%5B%5B%22light_control%22%2C%22%E6%8E%A7%E5%88%B6%E7%81%AF%E5%85%89%E5%BC%80%E5%85%B3%E5%92%8C%E4%BA%AE%E5%BA%A6%22%5D%5D%7D
```

**Profile JSON Structure:**
```json
{
    "device_id": "light-agent-001",
    "name": "Living Room Light",
    "role": "sub-agent",
    "skills": [["light_control", "控制灯光开关和亮度"]]
}
```

### 4.2 Message Format

```json
{
    "type": "message",
    "content": "...",
    "from_client_id": "...",
    "to_client_id": "..."
}
```

```json
{
    "type": "task_submit",
    "task_id": "uuid",
    "goal": "用户目标",
    "sub_tasks": [...]
}
```

```json
{
    "type": "task_result",
    "task_id": "uuid",
    "status": "completed",
    "sub_results": [...]
}
```

```json
{
    "type": "sub_task",
    "task_id": "uuid",
    "sub_task_id": "1",
    "goal": "打开客厅灯光",
    "from_client_id": "task-scheduler"
}
```

```json
{
    "type": "sub_task_result",
    "task_id": "uuid",
    "sub_task_id": "1",
    "success": true,
    "result": "灯光已打开"
}
```

```json
{
    "type": "task_failed",
    "task_id": "uuid",
    "sub_task_id": "1",
    "error": "Failed after 3 retries",
    "agent_id": "light-agent"
}
```

---

## 5. Prompt Management

### 5.1 Directory Structure

```
{work_dir}/
├── config.json      # LLM and agent configuration
└── prompts/         # Prompt MD files for Dooz Agent
    ├── 00_system_role.md      # Agent role definition (REQUIRED)
    ├── 10_context_agents.md    # Available agents context
    ├── 20_context_history.md   # Conversation history
    └── 30_user_task.md        # User task template
```

**Note:** 
- Files use `.md` extension but content is plain text.
- `work_dir` is the server's working directory (passed via `--workdir` argument or cwd)

### 5.2 Loading Rules

- Files sorted by filename prefix (00, 10, 20...)
- Matching pattern: `{priority}_{name}.md` (e.g., `00_system_role.md`, `10_context_agents.md`)
- Missing required file → raise `FileNotFoundError`
- No fallback to defaults

### 5.3 Context Updates

Runtime context updates replace entire context content in memory:
- Context is held in memory, not written back to files
- Files are loaded once at startup, runtime updates modify memory only

---

## 6. API Endpoints

### 6.1 Agent Info

```
GET /clients
GET /clients/{client_id}
```

### 6.2 Sub-Agent Discovery

Dooz Agent queries available sub-agents via REST API (not file):

```bash
GET /clients?role=sub-agent
```

**Discovery Mechanism:**
1. **Dynamic Query**: Dooz Agent calls `/clients` API whenever it needs to route a task
2. **No Caching**: Always get fresh list to handle agent connect/disconnect
3. **Response Format**:
```json
{
    "clients": [
        {
            "client_id": "light-agent-001",
            "name": "Living Room Light",
            "profile": {
                "device_id": "light-agent-001",
                "name": "Living Room Light",
                "role": "sub-agent",
                "skills": [["light_control", "控制灯光开关和亮度"]]
            }
        }
    ],
    "total": 1
}
```

Response includes device_id, name, profile with skills.

**Empty Sub-Agent Handling:**
- If `/clients?role=sub-agent` returns empty: 
  - Dooz Agent informs user "No sub-agents available"
  - Cannot execute task without sub-agents

---

## 7. Task Execution Flow

### 7.1 Dooz Agent Blocking

When Dooz Agent submits a task to Task Scheduler:
1. Dooz Agent sends `task_submit` message to task-scheduler via WS
2. Dooz Agent enters **blocking state** using async/await
   - Use `asyncio.wait_for()` with 60s timeout
   - Wait for `task_result` message on WS
3. Task Scheduler processes sub-tasks in parallel
4. Task Scheduler sends `task_result` message back to dooz-agent via WS
5. Dooz Agent receives result and continues conversation

**Dooz Agent Timeout:**
- Dooz Agent waits maximum **60 seconds** for Task Scheduler response
- If timeout: return error to user "Task execution timed out"
- User can disconnect WS to cancel (connection closed)

### 7.2 Result Delivery

**Push-based (callback):** Task Scheduler pushes result to Dooz Agent's WS:
```json
{
    "type": "task_result",
    "task_id": "uuid",
    "status": "completed",
    "sub_results": [
        {"sub_task_id": "1", "success": true, "result": "灯光已打开"},
        {"sub_task_id": "2", "success": true, "result": "音乐已播放"}
    ]
}
```

### 7.3 Sub-Agent Lifecycle Handling

| Scenario | Handling |
|----------|----------|
| Sub-agent disconnects mid-task | Task Scheduler waits for timeout, then marks as failed |
| Sub-agent timeout | Sub-agent sends `task_failed` after max retries |
| Task Scheduler crash | Dooz Agent has its own timeout; can resubmit |

### 7.4 Default Timeout

If sub-agent doesn't specify timeout: **30 seconds** default

### 7.5 Retry Strategy

- Each sub-agent defines its own timeout (default: 30 seconds)
- **Default max retries: 3** - sub-agent sends `task_failed` after 3 failed attempts
- Sub-agent sends `task_failed` message after max retries exceeded
- Task Scheduler treats no response as failure after sub-agent's timeout

### 7.6 Failure Format

```json
{
    "type": "task_failed",
    "task_id": "uuid",
    "sub_task_id": "1",
    "error": "Failed after 3 retries: ...",
    "agent_id": "light-agent"
}
```

---

## 8. Authentication

Sub-agents connect with profile containing their device_id and skills. Trust is established by:

1. **Profile validation on WS connection**:
   - Profile JSON is parsed and validated against schema
   - device_id must be unique and non-empty
   - role must be "sub-agent" for sub-agents

2. **device_id used for message routing**:
   - All messages include from_client_id and to_client_id
   - Server routes messages based on device_id

3. **No external auth required**:
   - This is an internal system design (mvp)
   - Network isolation assumed

**Invalid profile handling:**
- If profile JSON is malformed → connection rejected
- If device_id already exists → connection rejected

---

## 9. Implementation Changes

### 9.1 Refactor Required

1. **Remove existing agent module**: 
   - Delete `src/dooz_server/agent/` directory completely
   - Current files: `agent.py`, `task_router.py`, `llm_client.py`, `conversation.py`, `config.py`, `prompt_loader.py`
   - These are replaced by new system_agent implementation

2. **New prompt loading**: MD files instead of current system
3. **New task handling**: Task Scheduler component
4. **WS protocol extension**: New message types for task flow

### 9.2 New Files

- `src/dooz_server/system_agent/` - System agent implementations
- `src/dooz_server/task_scheduler/` - Task distribution and aggregation
- `src/dooz_server/prompts/` - Prompt management
- `prompts/` directory in work directory

### 9.3 Modified Files

- `src/dooz_server/main.py` - Add lifespan for system agents
- `src/dooz_server/router.py` - New message types handling
- `src/dooz_server/schemas.py` - Task-related schemas

---

## 10. Acceptance Criteria

- [ ] Dooz Agent connects via WS and responds to user messages
- [ ] Dooz Agent uses claude-agent-sdk for LLM calls
- [ ] Prompts loaded from MD files, missing file raises error
- [ ] Task submission works via message to task-scheduler
- [ ] Task Scheduler distributes sub-tasks in parallel
- [ ] Sub-task results aggregated and returned to Dooz Agent
- [ ] Dooz Agent blocks on task execution (WS wait)
- [ ] Available sub-agents discovered via `/clients` API
- [ ] All system agents registered via lifespan

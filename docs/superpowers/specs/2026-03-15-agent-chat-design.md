# Agent Chat Feature Specification

> **For agentic workers:** This spec defines the Agent Chat feature for the Dooz WebSocket server. Use this as the reference for implementation planning.

**Goal:** Add an AI agent entry point to the server that can receive user messages, decompose tasks using an LLM, route sub-tasks to available sub-agents/devices, aggregate results, and return to the user.

**Architecture:** Agent acts as a special client that:
1. Receives user messages via WebSocket
2. Queries the client registry for available sub-agents
3. Composes prompts from 3 sections (system, context, user) loaded from work directory
4. Calls external LLM to decompose tasks
5. Routes sub-tasks to appropriate sub-agents
6. Aggregates results and returns to user

**Tech Stack:** Python, FastAPI, WebSocket, OpenAI/Anthropic SDK

---

## 1. Overview

The Agent Chat feature adds an intelligent agent entry point to the Dooz WebSocket server. Users can send high-level tasks to this agent, which uses an LLM to understand intent, decompose into sub-tasks, delegate to available sub-agents/devices, and return aggregated results.

### 1.1 Key Concepts

| Concept | Description |
|---------|-------------|
| **Main Agent** | The AI agent that receives user messages and orchestrates task execution |
| **Sub-agent/Device** | Connected clients that can execute specific tasks (from client registry) |
| **Task Decomposition** | Process of breaking complex user requests into simpler sub-tasks |
| **Prompt Templates** | Modular prompt files loaded from work directory |

### 1.2 User Flow

```
User --(WebSocket message)--> Agent --(query)--> Client Registry
                                                      |
                                                      v
                                              [Available sub-agents]
                                                      |
Agent <--(aggregated results)-- Sub-agents <--(sub-task)-- Agent
                                                      |
                                              [Execute tasks]
```

---

## 2. Configuration

### 2.1 Config File

The server reads configuration from a JSON config file in the work directory.

**Location:** `{work_dir}/config.json`

**Schema:**

```json
{
  "agent": {
    "enabled": true,
    "device_id": "dooz-agent",
    "name": "Dooz Assistant"
  },
  "llm": {
    "provider": "openai",  // or "anthropic"
    "model": "gpt-4o",
    "api_key": "${OPENAI_API_KEY}",  // or use env var
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "prompts": {
    "directory": "prompts",
    "system_pattern": "system_*.txt",
    "context_pattern": "context_*.txt",
    "user_pattern": "user_*.txt"
  },
  "server": {
    "work_directory": "/path/to/workdir"
  }
}
```

### 2.2 Environment Variable Substitution

Config values支持环境变量替换，格式: `${ENV_VAR_NAME}`

---

## 3. Prompt System

### 3.1 Directory Structure

```
{work_dir}/
└── prompts/
    ├── 00_system_role.txt      # Agent base role/instructions
    ├── 01_system_capabilities.txt  # Additional capabilities
    ├── 10_context_agents.txt    # Available agents info
    ├── 20_context_devices.txt   # Available devices info
    ├── 30_context_history.txt   # Conversation history
    └── 50_user_task.txt         # User's current task
```

**Naming Convention:** `{priority}_{section}_{name}.txt`
- Priority: 2-digit number for ordering within section
- Section: `system`, `context`, or `user`

### 3.2 Prompt Sections

| Section | Loaded From | Used For |
|---------|-------------|----------|
| `system_prompt` | `system_*.txt` files (sorted) | Base instructions for the LLM |
| `context_info` | `context_*.txt` files (sorted) | Available agents, devices, conversation history |
| `user_message` | `user_*.txt` files (sorted) | User's actual task/request |

### 3.3 Dynamic Context Files

Some context files are generated at runtime:
- `context_agents.txt` - Current available sub-agents (from client registry)
- `context_history.txt` - Recent conversation history (maintained in memory)

---

## 4. Component Design

### 4.1 New Components

```
dooz_server/src/dooz_server/
├── agent/
│   ├── __init__.py
│   ├── agent.py          # Main Agent class
│   ├── config.py          # Config loading
│   ├── prompt_loader.py   # Prompt file loading
│   ├── llm_client.py      # LLM API client
│   ├── task_router.py     # Task decomposition & routing
│   └── conversation.py    # Conversation history management
```

### 4.2 Agent Class

```python
class Agent:
    """Main agent that handles user messages and orchestrates sub-agents."""
    
    def __init__(self, config: AgentConfig, client_manager: ClientManager):
        self.config = config
        self.client_manager = client_manager
        self.prompt_loader = PromptLoader(config.prompts_config)
        self.llm_client = LLMClient(config.llm_config)
        self.conversation = ConversationManager(max_history=10)
    
    async def handle_message(self, user_id: str, message: str) -> str:
        """Process user message and return agent response."""
        # 1. Build context from available sub-agents
        # 2. Compose prompt (system + context + user)
        # 3. Call LLM for task decomposition
        # 4. Execute sub-tasks via sub-agents
        # 5. Aggregate results
        # 6. Return response to user
```

### 4.3 Task Router

```python
class TaskRouter:
    """Handles task decomposition and routing to sub-agents."""
    
    async def decompose_task(self, prompt: str) -> list[SubTask]:
        """Use LLM to decompose user task into sub-tasks."""
    
    async def route_task(self, sub_task: SubTask, sub_agents: list[ClientInfo]) -> str:
        """Route sub-task to appropriate sub-agent based on skills/capabilities."""
    
    async def execute_sub_task(self, sub_agent_id: str, task: SubTask) -> TaskResult:
        """Execute a sub-task by sending message to sub-agent."""
```

### 4.4 Sub-task Schema

```python
class SubTask(BaseModel):
    """A decomposed sub-task to be executed by a sub-agent."""
    task_id: str
    description: str
    target_agent_id: Optional[str]  # Specific agent, or None for auto-route
    target_capability: Optional[str]  # Required capability for auto-route
    parameters: dict  # Task-specific parameters
    depends_on: list[str]  # Task IDs this depends on


class TaskResult(BaseModel):
    """Result from executing a sub-task."""
    task_id: str
    success: bool
    result: Optional[str]
    error: Optional[str]
```

---

## 5. WebSocket Integration

### 5.1 Agent Registration

The Agent registers itself as a special client on server startup:

```python
# In router.py or new agent_integration.py
def register_agent_device(config: AgentConfig, client_manager: ClientManager):
    """Register the agent as a client with special role."""
    profile = ClientProfile(
        device_id=config.device_id,
        name=config.name,
        role="agent",
        skills=[("task_decomposition", "Can break down complex tasks")]
    )
    client_manager.register_client(
        client_id=config.device_id,
        name=config.name,
        profile=profile,
        connection_type="InternalAgent"
    )
```

### 5.2 Message Handling

When a message is sent TO the agent device:

```python
@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    # ... existing connection logic ...
    
    if device_id == agent_config.device_id:
        # Route to agent handler
        await agent.handle_websocket(websocket, user_id)
    else:
        # Normal client handling
        pass
```

### 5.3 Agent WebSocket Protocol

**Incoming to Agent:**

```json
{
  "type": "agent_message",
  "user_id": "user-123",
  "content": "Turn on the living room lights with welcome pattern"
}
```

**Outgoing from Agent:**

```json
{
  "type": "agent_response",
  "user_id": "user-123",
  "message": "I've decomposed your request and executing tasks...",
  "status": "processing",  // or "completed", "error"
  "sub_tasks": [
    {
      "task_id": "1",
      "description": "Search for welcome light pattern",
      "status": "completed",
      "result": "Found pattern: rainbow-cycle"
    },
    {
      "task_id": "2", 
      "description": "Generate light code",
      "status": "processing"
    }
  ]
}
```

---

## 6. LLM Integration

### 6.1 Supported Providers

| Provider | Config Key | Default Model |
|----------|------------|---------------|
| OpenAI | `openai` | `gpt-4o` |
| Anthropic | `anthropic` | `claude-3-5-sonnet-20241022` |

### 6.2 Request Format

```python
async def call_llm(
    system_prompt: str,
    context_info: str, 
    user_message: str
) -> str:
    """Build and call LLM with the composed prompt."""
```

### 6.3 Response Parsing

The LLM returns a JSON array of sub-tasks:

```json
{
  "tasks": [
    {
      "task_id": "1",
      "description": "Search for welcome light pattern",
      "target_capability": "search",
      "parameters": {"query": "welcome light pattern"}
    },
    {
      "task_id": "2",
      "description": "Generate light animation code",
      "target_capability": "code_generation",
      "depends_on": ["1"],
      "parameters": {"pattern": "rainbow-cycle", "device": "lights"}
    }
  ]
}
```

---

## 7. Error Handling

### 7.1 Error Cases

| Error | Handling |
|-------|----------|
| Config file missing | Log warning, disable agent feature |
| LLM API error | Return error message to user, log details |
| Sub-agent not found | Skip task, continue with others, report in response |
| Sub-agent execution timeout | Retry once, then mark as failed |
| Invalid prompt file | Skip file, log warning |

### 7.2 Logging

```python
logger.info(f"Agent: Received message from {user_id}: {message[:50]}...")
logger.info(f"Agent: Decomposed into {len(tasks)} sub-tasks")
logger.warning(f"Agent: Sub-agent {agent_id} not found, skipping task {task_id}")
logger.error(f"Agent: LLM API error: {error}")
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

- `test_prompt_loader` - Loading and ordering prompt files
- `test_config_loading` - Config file parsing and env var substitution
- `test_llm_client` - Mock LLM responses
- `test_task_router` - Task decomposition logic

### 8.2 Integration Tests

- `test_agent_message_flow` - Full flow from user message to response
- `test_sub_task_routing` - Routing to correct sub-agents
- `test_conversation_history` - Maintaining context across messages

### 8.3 Mock Sub-agents

Create mock clients with different capabilities for testing:

```python
class MockSubAgent:
    def __init__(self, device_id: str, capabilities: list[str]):
        self.device_id = device_id
        self.capabilities = capabilities
```

---

## 9. File Structure Summary

### 9.1 New Files

| File | Purpose |
|------|---------|
| `src/dooz_server/agent/__init__.py` | Package exports |
| `src/dooz_server/agent/config.py` | Config loading and validation |
| `src/dooz_server/agent/prompt_loader.py` | Load prompts from work directory |
| `src/dooz_server/agent/llm_client.py` | LLM API calls |
| `src/dooz_server/agent/task_router.py` | Task decomposition and routing |
| `src/dooz_server/agent/conversation.py` | Conversation history |
| `src/dooz_server/agent/agent.py` | Main Agent class |

### 9.2 Modified Files

| File | Changes |
|------|---------|
| `main.py` | Load work directory, initialize agent |
| `router.py` | Register agent device, handle agent WebSocket |
| `src/dooz_server/__init__.py` | Export Agent class |

### 9.3 New Test Files

| File | Purpose |
|------|---------|
| `tests/agent/test_config.py` | Config loading tests |
| `tests/agent/test_prompt_loader.py` | Prompt loading tests |
| `tests/agent/test_llm_client.py` | LLM client tests |
| `tests/agent/test_task_router.py` | Task routing tests |
| `tests/agent/test_agent_integration.py` | Full integration tests |

---

## 10. Acceptance Criteria

- [ ] Agent can be configured via config file in work directory
- [ ] Prompts are loaded from `{work_dir}/prompts/*.txt` on startup
- [ ] User can send messages to agent via WebSocket
- [ ] Agent queries client registry for available sub-agents
- [ ] Agent calls LLM to decompose tasks with proper prompt composition
- [ ] Sub-tasks are routed to appropriate sub-agents
- [ ] Results are aggregated and returned to user
- [ ] Conversation history is maintained for context
- [ ] Error cases are handled gracefully with user feedback
- [ ] All new code has unit tests
- [ ] Integration tests verify full flow

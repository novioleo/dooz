# Dooz Agent Task Orchestration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement task orchestration system where Dooz Agent handles multi-turn conversation, creates tasks, and blocks until Task Scheduler returns results.

**Architecture:** Two system agents (Dooz Agent + Task Scheduler) run via FastAPI lifespan. Dooz Agent uses claude-agent-sdk for LLM, communicates via WebSocket. Task Scheduler distributes tasks to sub-agents in parallel. Prompts stored as MD files.

**Scope Note:** This plan implements the **server-side infrastructure only**:
- Task Scheduler (task distribution)
- Prompt loader (MD files)
- WebSocket message handling (task messages)
- Lifespan registration for system agents

The **Dooz Agent client** (external WebSocket client using claude-agent-sdk) is OUT OF SCOPE - it's a separate client application that connects to this server.

**Tech Stack:** Python, FastAPI, WebSocket, claude-agent-sdk==0.1.48, Pydantic

---

## File Structure

```
dooz_server/
├── src/dooz_server/
│   ├── __init__.py                 # Modify: remove old exports
│   ├── cli.py                      # Modify: remove device_id from config
│   ├── router.py                   # Modify: add task message types
│   ├── schemas.py                  # Modify: add task schemas
│   ├── agent/                      # DELETE entire directory
│   ├── task_scheduler/             # NEW: Task distribution component
│   │   ├── __init__.py
│   │   └── scheduler.py
│   └── prompts/                    # NEW: Prompt management
│       ├── __init__.py
│       └── loader.py
├── prompts/                        # NEW: Work dir prompts
│   ├── 00_system_role.md
│   ├── 10_context_agents.md
│   ├── 20_context_history.md
│   └── 30_user_task.md
└── tests/
    ├── agent/                      # DELETE old tests
    └── task_scheduler/             # NEW: Scheduler tests
        ├── __init__.py
        └── test_scheduler.py
```

---

## Chunk 1: Core Schemas and Types

### Task 1: Add Task Schemas

**Files:**
- Modify: `dooz_server/src/dooz_server/schemas.py`
- Test: `dooz_server/tests/test_schemas.py`

- [ ] **Step 1: Add task-related Pydantic models to schemas.py**

```python
# Add to schemas.py - Task Schemas

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class SubTask(BaseModel):
    """A sub-task to be executed by a sub-agent."""
    sub_task_id: str = Field(..., description="Unique sub-task identifier")
    agent_id: str = Field(..., description="Target agent device_id")
    goal: str = Field(..., description="What this sub-agent should achieve")
    parameters: dict = Field(default_factory=dict, description="Optional parameters")


class Task(BaseModel):
    """Task structure for sub-agent execution."""
    task_id: str = Field(..., description="Unique task identifier")
    goal: str = Field(..., description="User's final goal description")
    sub_tasks: list[SubTask] = Field(default_factory=list, description="List of sub-tasks")


class SubTaskResult(BaseModel):
    """Result from a sub-task execution."""
    sub_task_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class TaskResult(BaseModel):
    """Aggregated task result."""
    task_id: str
    status: Literal["completed", "failed", "partial"]
    sub_results: list[SubTaskResult]
    completed_at: datetime = Field(default_factory=datetime.now)
```

- [ ] **Step 2: Verify no existing test file, create basic test**

```bash
# Check if test_schemas.py exists
ls dooz_server/tests/test_schemas.py
```

- [ ] **Step 3: Run existing tests to verify no breakage**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/test_schemas.py -v 2>/dev/null || echo "No tests yet"`
Expected: PASS or "No tests yet"

- [ ] **Step 4: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/schemas.py
git commit -m "feat(schemas): add task orchestration schemas"
```

---

### Task 2: Update ClientProfile Schema

**Files:**
- Modify: `dooz_server/src/dooz_server/schemas.py`
- Test: `dooz_server/tests/test_schemas.py`

- [ ] **Step 1: Add system role types**

```python
# Add to schemas.py - Client Role Types

# System agent roles (hardcoded)
SYSTEM_AGENT_ROLES = Literal["dooz", "system", "sub-agent", "user"]
```

- [ ] **Step 2: Add system field to ClientProfile**

```python
class ClientProfile(BaseModel):
    """Profile information for a registered client."""
    model_config = ConfigDict(extra='ignore')
    
    device_id: str = Field(..., min_length=1, description="Unique device identifier (permanent)")
    name: str = Field(..., min_length=1, description="Client display name")
    role: str = Field(..., min_length=1, description="Client role (e.g., agent, user, service)")
    extra_info: Optional[str] = Field(default=None, description="Custom extra information")
    skills: list[tuple[str, str]] = Field(default_factory=list, description="List of (ability_name, ability_description) tuples")
    supports_input: bool = Field(default=False, description="Whether client supports input")
    supports_output: bool = Field(default=False, description="Whether client supports output")
    is_system: bool = Field(default=False, description="Whether this is a system agent")
```

- [ ] **Step 3: Run tests**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/test_schemas.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/schemas.py
git commit -m "feat(schemas): add system role types and is_system field"
```

---

## Chunk 2: Prompt Management (MD Files)

### Task 3: Create Prompt Loader for MD Files

**Files:**
- Create: `dooz_server/src/dooz_server/prompts/__init__.py`
- Create: `dooz_server/src/dooz_server/prompts/loader.py`
- Test: `dooz_server/tests/prompts/test_loader.py`

- [ ] **Step 1: Create test file with failing tests**

```python
# dooz_server/tests/prompts/__init__.py
"""Prompts tests."""

# dooz_server/tests/prompts/test_loader.py
import pytest
from pathlib import Path


class TestPromptLoader:
    """Tests for PromptLoader."""
    
    def test_load_prompts_from_directory(self, tmp_path):
        """Test loading prompt MD files from directory."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        (prompts_dir / "00_system_role.md").write_text("You are a helpful assistant.")
        (prompts_dir / "10_context_agents.md").write_text("Available agents: none")
        
        from dooz_server.prompts.loader import PromptLoader
        loader = PromptLoader(str(prompts_dir))
        
        assert loader.system_prompt == "You are a helpful assistant."
        assert "Available agents" in loader.context_info
    
    def test_missing_directory_raises_error(self, tmp_path):
        """Test missing directory raises FileNotFoundError."""
        from dooz_server.prompts.loader import PromptLoader
        
        with pytest.raises(FileNotFoundError):
            loader = PromptLoader(str(tmp_path / "nonexistent"))
    
    def test_missing_required_file_raises_error(self, tmp_path):
        """Test missing required system_role.md raises error."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        from dooz_server.prompts.loader import PromptLoader
        
        with pytest.raises(FileNotFoundError, match="system_role"):
            loader = PromptLoader(str(prompts_dir))
    
    def test_context_update_in_memory(self, tmp_path):
        """Test context updates modify memory only, not files."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "00_system_role.md").write_text("System")
        
        from dooz_server.prompts.loader import PromptLoader
        loader = PromptLoader(str(prompts_dir))
        
        # Update context
        loader.update_context("context_agents", "Agent A, Agent B")
        
        # Memory should be updated
        assert "Agent A, Agent B" in loader.context_info
        
        # File should NOT be modified
        content = (prompts_dir / "10_context_agents.md").read_text()
        assert "Agent A" not in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/prompts/test_loader.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server.prompts'"

- [ ] **Step 3: Create package init**

```python
# dooz_server/src/dooz_server/prompts/__init__.py
"""Prompt management for Dooz Agent."""

from .loader import PromptLoader

__all__ = ["PromptLoader"]
```

- [ ] **Step 4: Create prompt loader implementation**

```python
# dooz_server/src/dooz_server/prompts/loader.py
"""Prompt loading from work directory (MD files)."""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("dooz_server.prompts")


class PromptLoader:
    """Loads and manages prompt MD files from work directory."""
    
    REQUIRED_FILES = ["system_role"]
    
    def __init__(self, prompts_dir: str):
        """Initialize prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt MD files.
            
        Raises:
            FileNotFoundError: If prompts directory or required files don't exist.
        """
        self.prompts_dir = Path(prompts_dir)
        
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")
        
        self._system_parts: list[tuple[int, str]] = []
        self._context_parts: list[tuple[int, str]] = []
        
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt files from directory."""
        # Load system prompts (*_system_*.md)
        self._system_parts = self._load_matching_files("*_system_*.md")
        
        # Check required files
        for req in self.REQUIRED_FILES:
            found = any(req in str(f) for f in self.prompts_dir.glob("*.md"))
            if not found:
                raise FileNotFoundError(f"Required prompt file not found: {req}.md")
        
        # Load context prompts (*_context_*.md)
        self._context_parts = self._load_matching_files("*_context_*.md")
        
        logger.info(f"Loaded prompts: {len(self._system_parts)} system, "
                   f"{len(self._context_parts)} context")
    
    def _load_matching_files(self, pattern: str) -> list[tuple[int, str]]:
        """Load files matching pattern, return sorted by priority."""
        parts = []
        
        for file_path in self.prompts_dir.glob(pattern):
            try:
                content = file_path.read_text(encoding='utf-8').strip()
                if content:
                    priority = self._extract_priority(file_path.name)
                    parts.append((priority, content))
            except Exception as e:
                logger.warning(f"Failed to load prompt {file_path}: {e}")
        
        parts.sort(key=lambda x: x[0])
        return parts
    
    def _extract_priority(self, filename: str) -> int:
        """Extract priority number from filename (e.g., '00_system_role.md' -> 0)."""
        name = Path(filename).stem
        parts = name.split('_', 1)
        try:
            return int(parts[0])
        except (ValueError, IndexError):
            return 99
    
    @property
    def system_prompt(self) -> str:
        """Get concatenated system prompts."""
        return '\n\n'.join(part[1] for part in self._system_parts)
    
    @property
    def context_info(self) -> str:
        """Get concatenated context prompts."""
        return '\n\n'.join(part[1] for part in self._context_parts)
    
    def update_context(self, context_name: str, content: str):
        """Update context in memory (does not write to file).
        
        Args:
            context_name: Name of context (e.g., "context_agents")
            content: New content
        """
        # Clear existing context with matching name
        self._context_parts = [
            (p, c) for p, c in self._context_parts 
            if context_name not in c
        ]
        
        priority = self._extract_priority(f"10_{context_name}.md")
        self._context_parts.append((priority, content))
        self._context_parts.sort(key=lambda x: x[0])
        
        logger.debug(f"Updated context: {context_name}")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/prompts/test_loader.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/prompts/ dooz_server/tests/prompts/
git commit -m "feat(prompts): add MD file prompt loader"
```

---

## Chunk 3: Task Scheduler Component

### Task 4: Create Task Scheduler

**Files:**
- Create: `dooz_server/src/dooz_server/task_scheduler/__init__.py`
- Create: `dooz_server/src/dooz_server/task_scheduler/scheduler.py`
- Test: `dooz_server/tests/task_scheduler/test_scheduler.py`

- [ ] **Step 1: Create test file with failing tests**

```python
# dooz_server/tests/task_scheduler/test_scheduler.py
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock


class TestTaskScheduler:
    """Tests for TaskScheduler."""
    
    @pytest.mark.asyncio
    async def test_submit_task_distributes_to_sub_agents(self):
        """Test task is distributed to all sub-agents in parallel."""
        from dooz_server.task_scheduler.scheduler import TaskScheduler
        
        mock_ws_manager = Mock()
        mock_ws_manager.send_personal_message = AsyncMock()
        
        scheduler = TaskScheduler(mock_ws_manager)
        
        task = {
            "task_id": "test-123",
            "goal": "打开灯光",
            "sub_tasks": [
                {"sub_task_id": "1", "agent_id": "light-agent", "goal": "打开灯光"}
            ]
        }
        
        # Execute task
        result = await scheduler.submit_task(task)
        
        assert result["task_id"] == "test-123"
        assert "sub_results" in result
    
    @pytest.mark.asyncio
    async def test_task_timeout_returns_failure(self):
        """Test task timeout returns failure result."""
        from dooz_server.task_scheduler.scheduler import TaskScheduler
        
        mock_ws_manager = Mock()
        # Simulate no response (timeout)
        async def mock_send(*args, **kwargs):
            await asyncio.sleep(0.1)  # Small delay
            return None
        
        mock_ws_manager.send_personal_message = mock_send
        
        scheduler = TaskScheduler(mock_ws_manager, default_timeout=0.05)
        
        task = {
            "task_id": "test-timeout",
            "goal": "测试超时",
            "sub_tasks": [
                {"sub_task_id": "1", "agent_id": "light-agent", "goal": "打开灯光"}
            ]
        }
        
        result = await scheduler.submit_task(task)
        
        assert result["status"] in ["failed", "partial"]
    
    @pytest.mark.asyncio
    async def test_multiple_subtasks_parallel(self):
        """Test multiple sub-tasks run in parallel."""
        from dooz_server.task_scheduler.scheduler import TaskScheduler
        
        call_times = []
        
        async def mock_send(client_id, message):
            import time
            call_times.append(time.time())
            await asyncio.sleep(0.1)  # Simulate work
            return None
        
        mock_ws_manager = Mock()
        mock_ws_manager.send_personal_message = mock_send
        
        scheduler = TaskScheduler(mock_ws_manager)
        
        task = {
            "task_id": "test-parallel",
            "goal": "多个任务",
            "sub_tasks": [
                {"sub_task_id": "1", "agent_id": "light-agent", "goal": "任务1"},
                {"sub_task_id": "2", "agent_id": "speaker-agent", "goal": "任务2"},
                {"sub_task_id": "3", "agent_id": "coffee-agent", "goal": "任务3"}
            ]
        }
        
        await scheduler.submit_task(task)
        
        # All should start within small time window (parallel)
        assert len(call_times) >= 2
        time_diff = call_times[-1] - call_times[0]
        assert time_diff < 0.15  # If sequential, would be 0.3+
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/task_scheduler/test_scheduler.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Create package init**

```python
# dooz_server/src/dooz_server/task_scheduler/__init__.py
"""Task Scheduler for distributing tasks to sub-agents."""

from .scheduler import TaskScheduler

__all__ = ["TaskScheduler"]
```

- [ ] **Step 4: Create scheduler implementation**

```python
# dooz_server/src/dooz_server/task_scheduler/scheduler.py
"""Task Scheduler - distributes tasks to sub-agents and aggregates results."""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger("dooz_server.task_scheduler")


class TaskScheduler:
    """Handles task distribution to sub-agents and result aggregation."""
    
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MAX_RETRIES = 3  # per spec Section 7.5
    
    def __init__(self, ws_manager, default_timeout: int = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES):
        """Initialize Task Scheduler.
        
        Args:
            ws_manager: WebSocket connection manager for sending messages
            default_timeout: Default timeout for sub-task execution
            max_retries: Max retry attempts per sub-task (default: 3)
        """
        self.ws_manager = ws_manager
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self._pending_tasks: dict[str, asyncio.Future] = {}
    
    async def submit_task(self, task: dict) -> dict:
        """Submit a task for execution.
        
        Args:
            task: Task dict with task_id, goal, sub_tasks
            
        Returns:
            Task result dict with status and sub_results
        """
        task_id = task.get("task_id", str(uuid.uuid4()))
        sub_tasks = task.get("sub_tasks", [])
        
        logger.info(f"TaskScheduler: Submitting task {task_id} with {len(sub_tasks)} sub-tasks")
        
        if not sub_tasks:
            return {
                "task_id": task_id,
                "status": "completed",
                "sub_results": []
            }
        
        # Create futures for each sub-task
        sub_task_futures = {}
        for subtask in sub_tasks:
            future = asyncio.Future()
            sub_task_futures[subtask["sub_task_id"]] = future
            self._pending_tasks[f"{task_id}:{subtask['sub_task_id']}"] = future
        
        # Send sub-tasks to all sub-agents in parallel
        await self._distribute_subtasks(task_id, sub_tasks)
        
        # Wait for all results with timeout
        results = await self._collect_results(
            task_id, 
            sub_tasks, 
            sub_task_futures,
            timeout=self.default_timeout
        )
        
        # Cleanup
        for key in list(self._pending_tasks.keys()):
            if key.startswith(task_id):
                del self._pending_tasks[key]
        
        # Determine overall status
        success_count = sum(1 for r in results if r.get("success", False))
        if success_count == len(sub_tasks):
            status = "completed"
        elif success_count == 0:
            status = "failed"
        else:
            status = "partial"
        
        return {
            "task_id": task_id,
            "status": status,
            "sub_results": results,
            "completed_at": datetime.now().isoformat()
        }
    
    async def _distribute_subtasks(self, task_id: str, sub_tasks: list[dict]):
        """Send sub-tasks to all sub-agents in parallel."""
        async_tasks = []
        for subtask in sub_tasks:
            agent_id = subtask.get("agent_id")
            message = {
                "type": "sub_task",
                "task_id": task_id,
                "sub_task_id": subtask.get("sub_task_id"),
                "goal": subtask.get("goal"),
                "parameters": subtask.get("parameters", {}),
                "from_client_id": "task-scheduler"
            }
            async_tasks.append(self._send_to_agent(agent_id, message))
        
        # Send all in parallel (don't wait)
        if async_tasks:
            asyncio.create_task(asyncio.gather(*async_tasks, return_exceptions=True))
    
    async def _send_to_agent(self, agent_id: str, message: dict):
        """Send message to specific agent via WS."""
        try:
            await self.ws_manager.send_personal_message(message, agent_id)
            logger.debug(f"Sent message to {agent_id}: {message.get('type')}")
        except Exception as e:
            logger.error(f"Failed to send to {agent_id}: {e}")
    
    async def _collect_results(
        self, 
        task_id: str, 
        sub_tasks: list[dict],
        sub_task_futures: dict[str, asyncio.Future],
        timeout: int
    ) -> list[dict]:
        """Collect results from all sub-tasks with timeout."""
        try:
            # Wait for all futures with timeout
            results = await asyncio.wait_for(
                asyncio.gather(
                    *[f for f in sub_task_futures.values()],
                    return_exceptions=True
                ),
                timeout=timeout
            )
            
            # Convert results to dict format
            output = []
            for subtask, result in zip(sub_tasks, results):
                if isinstance(result, Exception):
                    output.append({
                        "sub_task_id": subtask["sub_task_id"],
                        "success": False,
                        "error": str(result)
                    })
                else:
                    output.append(result)
            
            return output
            
        except asyncio.TimeoutError:
            logger.warning(f"Task {task_id} timed out after {timeout}s")
            
            # Return partial results with timeout status
            output = []
            for subtask in sub_tasks:
                future = sub_task_futures.get(subtask["sub_task_id"])
                if future and future.done() and not future.cancelled():
                    try:
                        output.append(future.result())
                    except Exception as e:
                        output.append({
                            "sub_task_id": subtask["sub_task_id"],
                            "success": False,
                            "error": str(e)
                        })
                else:
                    output.append({
                        "sub_task_id": subtask["sub_task_id"],
                        "success": False,
                        "error": f"Timeout after {timeout}s"
                    })
            
            return output
    
    async def handle_sub_task_result(self, message: dict):
        """Handle result message from sub-agent.
        
        Args:
            message: Result message with task_id, sub_task_id, success, result/error
        """
        task_id = message.get("task_id")
        sub_task_id = message.get("sub_task_id")
        
        key = f"{task_id}:{sub_task_id}"
        future = self._pending_tasks.get(key)
        
        if future:
            result = {
                "sub_task_id": sub_task_id,
                "success": message.get("success", False),
                "result": message.get("result"),
                "error": message.get("error")
            }
            future.set_result(result)
            logger.info(f"Received result for {sub_task_id}: success={result['success']}")
        else:
            logger.warning(f"No pending future for {key}")
```

- [ ] **Step 6: Run tests**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/task_scheduler/test_scheduler.py -v`
Expected: PASS (may need adjustments)

- [ ] **Step 6: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/task_scheduler/ dooz_server/tests/task_scheduler/
git commit -m "feat(task-scheduler): add task distribution component"
```

---

## Chunk 4: Router Updates for Task Messages

### Task 5: Add Task Message Handling and Lifespan

**Files:**
- Modify: `dooz_server/src/dooz_server/router.py`
- Test: `dooz_server/tests/test_router.py`

- [ ] **Step 1: Add task message type constants**

```python
# Add to router.py - Message Types

TASK_MESSAGE_TYPES = {
    "task_submit",      # Dooz Agent -> Task Scheduler
    "task_result",      # Task Scheduler -> Dooz Agent
    "sub_task",         # Task Scheduler -> Sub-Agent
    "sub_task_result",  # Sub-Agent -> Task Scheduler
    "task_failed",      # Sub-Agent -> Task Scheduler
}
```

- [ ] **Step 2: Add TaskScheduler to router globals**

```python
# Add after other globals
_task_scheduler: Optional[Any] = None

def get_task_scheduler():
    global _task_scheduler
    if _task_scheduler is None:
        from dooz_server.task_scheduler import TaskScheduler
        _task_scheduler = TaskScheduler(get_ws_manager())
    return _task_scheduler
```

- [ ] **Step 3: Add lifespan context for system agent registration**

In `cli.py`, update `create_app()`:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for server startup/shutdown."""
    from dooz_server.router import get_client_manager
    client_mgr = get_client_manager()
    
    # Pre-register system agents so they can be discovered
    client_mgr.register_client("dooz-agent", "Dooz Assistant", role="dooz")
    client_mgr.register_client("task-scheduler", "Task Scheduler", role="system")
    
    logger.info("System agents registered: dooz-agent, task-scheduler")
    yield
    logger.info("Server shutting down")

def create_app(work_directory: str = None) -> "FastAPI":
    # ... existing code ...
    app = FastAPI(
        title="Dooz WebSocket Server",
        version="0.1.0",
        lifespan=lifespan  # Add this
    )
```

- [ ] **Step 4: Update websocket_endpoint to handle task messages**

Add after the message_type == "message" block:

```python
elif message_type == "task_submit":
    # Task submission from Dooz Agent
    task_scheduler = get_task_scheduler()
    task_data = message_data.get("task_data", {})
    
    result = await task_scheduler.submit_task(task_data)
    
    # Send result back to dooz-agent
    await ws_mgr.send_personal_message({
        "type": "task_result",
        "task_id": result["task_id"],
        "status": result["status"],
        "sub_results": result["sub_results"],
        "completed_at": result.get("completed_at")
    }, final_device_id)
    
    logger.info(f"Task completed: {result['task_id']} -> {result['status']}")

elif message_type == "sub_task_result":
    # Result from sub-agent
    task_scheduler = get_task_scheduler()
    await task_scheduler.handle_sub_task_result(message_data)

elif message_type == "task_failed":
    # Failure from sub-agent
    task_scheduler = get_task_scheduler()
    await task_scheduler.handle_sub_task_result({
        **message_data,
        "success": False
    })
```

- [ ] **Step 5: Add test for task message handling**

```python
def test_task_message_types_defined():
    """Test task message types are defined."""
    from dooz_server.router import TASK_MESSAGE_TYPES
    
    assert "task_submit" in TASK_MESSAGE_TYPES
    assert "task_result" in TASK_MESSAGE_TYPES
    assert "sub_task" in TASK_MESSAGE_TYPES
    assert "sub_task_result" in TASK_MESSAGE_TYPES
    assert "task_failed" in TASK_MESSAGE_TYPES


def test_task_scheduler_singleton():
    """Test TaskScheduler is created as singleton."""
    from dooz_server.router import get_task_scheduler
    
    scheduler1 = get_task_scheduler()
    scheduler2 = get_task_scheduler()
    
    assert scheduler1 is scheduler2
```

- [ ] **Step 6: Run tests**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/test_router.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/router.py dooz_server/src/dooz_server/cli.py
git commit -m "feat(router): add task message handling and lifespan"
```

---

## Chunk 5: CLI Updates

**Note:** The `/clients?role=sub-agent` API endpoint already exists in router.py (no changes needed).

### Task 6: Update CLI to Remove device_id from Config

**Files:**
- Modify: `dooz_server/src/dooz_server/cli.py`

- [ ] **Step 1: Update DEFAULT_CONFIG to remove agent.device_id**

```python
# Update DEFAULT_CONFIG - remove device_id (it's hardcoded)
DEFAULT_CONFIG = {
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

- [ ] **Step 2: Update init command to create .md files instead of .txt**

```python
# Update init command - create .md files
DEFAULT_SYSTEM_PROMPT = """You are Dooz Assistant...

# Task Format
When you need to execute tasks via sub-agents, respond with:

Direct response: [your response to user]

OR

Tasks:
[
  {"agent_id": "[agent-device-id]", "goal": "[what agent should do]"}
]
"""

# In init() function, update file creation:
system_file = prompts_dir / "00_system_role.md"  # Changed from .txt
# ... other files also .md
```

- [ ] **Step 3: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/cli.py
git commit -m "feat(cli): update config and prompts to use MD files"
```

---
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/router.py
git commit -m "feat(router): add lifespan for system agent registration"
```

---

## Chunk 6: Cleanup Old Agent Module

### Task 7: Remove Old Agent Module

**Files:**
- Modify: `dooz_server/src/dooz_server/router.py` (remove agent imports)
- Modify: `dooz_server/src/dooz_server/cli.py` (remove agent imports)
- Delete: `dooz_server/src/dooz_server/agent/`
- Delete: `dooz_server/tests/agent/`

- [ ] **Step 1: Remove agent imports from router.py**

In `router.py`, remove or comment out:
```python
# REMOVE THESE LINES (no longer needed):
# from .agent import Agent, load_agent_config
# from .agent.config import AgentConfig
```

- [ ] **Step 2: Remove agent imports from cli.py**

In `cli.py`, remove or comment out:
```python
# REMOVE THESE LINES (no longer needed):
# from dooz_server.agent import load_agent_config
# init_agent_router(work_dir) call in create_app()
```

- [ ] **Step 3: Remove old agent directory**

```bash
rm -rf dooz_server/src/dooz_server/agent/
rm -rf dooz_server/tests/agent/
```

- [ ] **Step 4: Update __init__.py if needed**

Check and update `dooz_server/src/dooz_server/__init__.py` to remove old exports.

- [ ] **Step 5: Run tests to verify nothing broke**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest -v`
Expected: Tests should pass (some may need updating)

- [ ] **Step 6: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git rm -rf dooz_server/src/dooz_server/agent/ dooz_server/tests/agent/
git commit -m "refactor: remove old agent module"
```

---

## Chunk 7: Create Sample Prompts

### Task 8: Create Sample Prompt Files

**Files:**
- Create: `prompts/00_system_role.md`
- Create: `prompts/10_context_agents.md`
- Create: `prompts/20_context_history.md`
- Create: `prompts/30_user_task.md`

- [ ] **Step 1: Create system role prompt**

```markdown
# prompts/00_system_role.md

You are Dooz Assistant, an AI agent that helps users interact with smart home devices and other connected services through sub-agents.

Your role is to:
1. Understand user requests through conversation
2. Ask clarifying questions if needed
3. When user intent is clear, create tasks for sub-agents
4. Aggregate results and present to user

## Response Format

When you need sub-agents to execute tasks, respond with:

Direct response: [Your response to the user]

OR

Tasks:
[
  {"agent_id": "light-agent", "goal": "打开客厅灯光"},
  {"agent_id": "speaker-agent", "goal": "播放舒缓音乐"}
]
```

- [ ] **Step 2: Create context templates**

```markdown
# prompts/10_context_agents.md

# Available Sub-Agents

(No agents connected yet - will be populated at runtime)
```

```markdown
# prompts/20_context_history.md

# Conversation History

(No history yet)
```

```markdown
# prompts/30_user_task.md

# User Task Template

When user sends a message, it will appear here.
```

- [ ] **Step 3: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
mkdir -p prompts
git add prompts/
git commit -m "feat(prompts): add sample prompt files"
```

---

## Acceptance Criteria

- [ ] Task schemas added to schemas.py
- [ ] Prompt loader reads .md files, raises FileNotFoundError if missing
- [ ] TaskScheduler distributes sub-tasks in parallel
- [ ] Router handles task_submit, task_result, sub_task messages
- [ ] CLI generates .md prompt files
- [ ] Old agent module removed
- [ ] All tests pass

"""Task scheduler for distributing and coordinating sub-agent tasks."""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("dooz_server.system_agents.task_scheduler")

# Default configuration constants
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3


@dataclass
class Task:
    """Represents a task to be executed by sub-agents."""
    
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    goal: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    timeout: int = DEFAULT_TIMEOUT
    retries: int = 0
    
    @property
    def description(self) -> str:
        """Get task description."""
        return f"Agent {self.agent_id}: {self.goal}"


@dataclass
class TaskResult:
    """Result from task execution."""
    
    task_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None


class TaskScheduler:
    """Schedules and coordinates tasks across sub-agents.
    
    Manages task submission, distribution to connected sub-agents,
    and collection of results.
    """
    
    def __init__(self, ws_manager: Optional[Any] = None):
        """Initialize task scheduler.
        
        Args:
            ws_manager: WebSocket manager for communicating with agents.
        """
        self.ws_manager = ws_manager
        self._pending_tasks: dict[str, Task] = {}
        self._results: dict[str, TaskResult] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._result_events: dict[str, asyncio.Event] = {}
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution.
        
        Args:
            task: Task to submit.
            
        Returns:
            Task ID.
        """
        self._pending_tasks[task.task_id] = task
        self._locks[task.task_id] = asyncio.Lock()
        self._results[task.task_id] = TaskResult(
            task_id=task.task_id,
            success=False,
            result=None,
            error=None,
            agent_id=task.agent_id
        )
        self._result_events[task.task_id] = asyncio.Event()
        
        logger.info(f"Task submitted: {task.task_id} -> {task.agent_id}: {task.goal}")
        
        # Distribute task to sub-agent
        await self._distribute_task(task)
        
        return task.task_id
    
    async def submit_task_and_wait(self, task: Task, timeout: float = DEFAULT_TIMEOUT) -> TaskResult:
        """Submit a task and wait for its result.
        
        Args:
            task: Task to submit.
            timeout: Timeout in seconds.
            
        Returns:
            TaskResult with the result.
        """
        task_id = await self.submit_task(task)
        
        # Wait for the result
        result = await self.wait_for_result(task_id, timeout)
        
        if result is None:
            # Timeout - return failure result
            return TaskResult(
                task_id=task_id,
                success=False,
                error=f"Task timeout after {timeout} seconds"
            )
        
        return result
    
    async def _distribute_task(self, task: Task):
        """Distribute task to the appropriate sub-agent via WebSocket.
        
        Args:
            task: Task to distribute.
        """
        if self.ws_manager is None:
            logger.warning("No WebSocket manager available for task distribution")
            self._results[task.task_id] = TaskResult(
                task_id=task.task_id,
                success=False,
                error="No WebSocket manager available"
            )
            return
        
        # Send task message to the target agent
        message = {
            "type": "sub_task",
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "goal": task.goal,
            "params": task.params
        }
        
        try:
            # Broadcast to all, let the agent filter by agent_id
            await self.ws_manager.broadcast(message)
            logger.debug(f"Task broadcast: {task.task_id}")
        except Exception as e:
            logger.error(f"Failed to distribute task {task.task_id}: {e}")
            self._results[task.task_id] = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e)
            )
    
    async def _distribute_and_collect(
        self,
        task_id: str,
        sub_tasks: list[Task]
    ) -> list[TaskResult]:
        """Execute multiple sub-tasks in parallel and collect results.
        
        Args:
            task_id: Parent task ID.
            sub_tasks: List of sub-tasks to execute.
            
        Returns:
            List of task results.
        """
        results: list[TaskResult] = []
        
        # Execute all sub-tasks in parallel
        task_coroutines = [self.submit_task(task) for task in sub_tasks]
        await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Wait for all results with timeout
        try:
            await asyncio.wait_for(
                self._wait_for_results(task_id),
                timeout=DEFAULT_TIMEOUT * len(sub_tasks)
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for task {task_id} results")
        
        # Collect results
        for task in sub_tasks:
            result = self._results.get(task.task_id)
            if result:
                results.append(result)
        
        return results
    
    async def _wait_for_results(self, task_id: str):
        """Wait for all pending results to complete."""
        while True:
            pending = [tid for tid in self._pending_tasks if tid.startswith(task_id)]
            if not pending:
                break
            await asyncio.sleep(0.1)
    
    async def handle_sub_task_result(self, message: dict[str, Any]):
        """Handle a sub-task result message from an agent.
        
        Args:
            message: Result message containing task_id and result.
        """
        task_id = message.get("task_id")
        if not task_id:
            logger.warning("Received result message without task_id")
            return
        
        success = message.get("success", False)
        result = message.get("result")
        error = message.get("error")
        
        if task_id in self._results:
            self._results[task_id] = TaskResult(
                task_id=task_id,
                success=success,
                result=result,
                error=error,
                agent_id=self._results[task_id].agent_id
            )
            
            # Remove from pending
            self._pending_tasks.pop(task_id, None)
            
            # Signal result is ready
            if task_id in self._result_events:
                self._result_events[task_id].set()
            
            logger.info(f"Task result received: {task_id}, success={success}")
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result for a specific task.
        
        Args:
            task_id: Task ID to查询.
            
        Returns:
            TaskResult if available, None otherwise.
        """
        return self._results.get(task_id)
    
    async def wait_for_result(self, task_id: str, timeout: float) -> Optional[TaskResult]:
        """Wait for a task result with timeout.
        
        Args:
            task_id: Task ID to wait for.
            timeout: Timeout in seconds.
            
        Returns:
            TaskResult if available, None if timeout.
        """
        event = self._result_events.get(task_id)
        if not event:
            return self._results.get(task_id)
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        
        return self._results.get(task_id)
    
    def clear_completed(self):
        """Clear completed tasks and results."""
        completed_ids = [
            tid for tid, result in self._results.items()
            if result.success or result.error
        ]
        for tid in completed_ids:
            self._results.pop(tid, None)
            self._pending_tasks.pop(tid, None)
            self._locks.pop(tid, None)
            self._result_events.pop(tid, None)

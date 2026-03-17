"""Task Scheduler Agent - distributes tasks to sub-agents."""

import asyncio
import logging
import uuid
from typing import Optional

from .base import Agent, AgentConfig, AgentMessage

logger = logging.getLogger("dooz_daemon.agents.scheduler")


class SchedulerAgent(Agent):
    """Task scheduler that distributes tasks to sub-agents."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._pending_tasks: dict[str, dict] = {}
    
    @property
    def subscribe_topics(self) -> list[str]:
        return [
            f"dooz/{self.config.dooz_id}/system/scheduler",
        ]
    
    async def handle_message(self, msg: AgentMessage):
        """Handle task submission messages."""
        if msg.type == "task_submit":
            await self._handle_task_submit(msg)
    
    async def _handle_task_submit(self, msg: AgentMessage):
        """Submit task to sub-agents."""
        task_id = msg.payload.get("task_id", uuid.uuid4().hex)
        goal = msg.payload.get("goal", "")
        sub_tasks = msg.payload.get("sub_tasks", [])
        
        logger.info(f"Received task {task_id} with {len(sub_tasks)} sub-tasks")
        
        # Send each sub-task to its target agent
        results = []
        for sub_task in sub_tasks:
            agent_id = sub_task.get("agent_id")
            sub_task_id = sub_task.get("sub_task_id", uuid.uuid4().hex)
            sub_goal = sub_task.get("goal", goal)
            
            # Publish to agent's task topic
            task_msg = AgentMessage(
                type="task",
                agent_id=self.config.agent_id,
                dooz_id=self.config.dooz_id,
                payload={
                    "task_id": task_id,
                    "sub_task_id": sub_task_id,
                    "goal": sub_goal,
                    "parameters": sub_task.get("parameters", {}),
                },
            )
            
            topic = f"dooz/{self.config.dooz_id}/tasks/{agent_id}"
            await self.publish(topic, task_msg)
            logger.info(f"Dispatched sub-task {sub_task_id} to {agent_id}")
        
        # For now, just acknowledge (Phase 2 - no actual execution yet)
        response = AgentMessage(
            type="task_result",
            agent_id=self.config.agent_id,
            dooz_id=self.config.dooz_id,
            payload={
                "task_id": task_id,
                "status": "dispatched",
                "sub_tasks": len(sub_tasks),
            },
        )
        
        # Send back to orchestrator
        response_topic = f"dooz/{self.config.dooz_id}/system/orchestrator"
        await self.publish(response_topic, response)

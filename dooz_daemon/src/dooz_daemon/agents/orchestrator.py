"""Orchestrator Agent - main AI agent for task execution."""

import logging
import uuid
from typing import Optional

from .base import Agent, AgentConfig, AgentMessage

logger = logging.getLogger("dooz_daemon.agents.orchestrator")


class OrchestratorAgent(Agent):
    """Orchestrator agent - main AI agent that handles user requests."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
    
    @property
    def subscribe_topics(self) -> list[str]:
        return [
            f"dooz/{self.config.dooz_id}/system/orchestrator",
        ]
    
    async def handle_message(self, msg: AgentMessage):
        """Handle user request messages."""
        if msg.type == "user_message":
            await self._handle_user_message(msg)
        elif msg.type == "task_result":
            await self._handle_task_result(msg)
    
    async def _handle_user_message(self, msg: AgentMessage):
        """Process user message - in Phase 2, just echo with task structure."""
        session_id = msg.payload.get("session_id", "unknown")
        content = msg.payload.get("content", "")
        
        logger.info(f"User message in session {session_id}: {content}")
        
        # For Phase 2: Simple response
        # In Phase 3: Use LLM to determine tasks
        
        response = AgentMessage(
            type="response",
            agent_id=self.config.agent_id,
            dooz_id=self.config.dooz_id,
            payload={
                "session_id": session_id,
                "content": f"Received: {content}",
                "task_id": None,  # No task needed in Phase 2
            },
        )
        
        # Send response back via WebSocket (through daemon)
        response_topic = f"dooz/{self.config.dooz_id}/websocket/session/{session_id}"
        await self.publish(response_topic, response)
        logger.info(f"Sent response to session {session_id}")
    
    async def _handle_task_result(self, msg: AgentMessage):
        """Handle task result from scheduler."""
        task_id = msg.payload.get("task_id")
        status = msg.payload.get("status", "unknown")
        
        logger.info(f"Task {task_id} completed with status: {status}")

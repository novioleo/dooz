"""Task decomposition and routing to sub-agents."""
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field

from .llm_client import LLMClient
from ..schemas import ClientInfo

logger = logging.getLogger("dooz_server.agent.task_router")


class SubTask(BaseModel):
    """A decomposed sub-task to be executed by a sub-agent."""
    task_id: str
    description: str
    target_agent_id: Optional[str] = None
    target_capability: Optional[str] = None
    parameters: dict = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class TaskRouter:
    """Handles task decomposition and routing to sub-agents."""
    
    def __init__(self, llm_client: LLMClient, client_manager):
        """Initialize task router."""
        self.llm_client = llm_client
        self.client_manager = client_manager
    
    async def decompose_task(
        self,
        user_message: str,
        system_prompt: str,
        context_info: str
    ) -> list[SubTask]:
        """Use LLM to decompose user task into sub-tasks."""
        try:
            response = await self.llm_client.call(
                system_prompt=system_prompt,
                context_info=context_info,
                user_message=user_message
            )
            
            tasks = self._parse_llm_response(response)
            logger.info(f"Decomposed task into {len(tasks)} sub-tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            return []
    
    def _parse_llm_response(self, response: str) -> list[SubTask]:
        """Parse LLM response into SubTask objects."""
        try:
            data = json.loads(response)
            
            if isinstance(data, dict) and 'tasks' in data:
                tasks_data = data['tasks']
            elif isinstance(data, list):
                tasks_data = data
            else:
                logger.warning(f"Unexpected LLM response format: {response[:100]}")
                return []
            
            tasks = []
            for task_data in tasks_data:
                try:
                    task = SubTask(**task_data)
                    tasks.append(task)
                except Exception as e:
                    logger.warning(f"Failed to parse task {task_data}: {e}")
                    continue
            
            return tasks
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []
    
    def find_agent_for_task(
        self,
        task: SubTask,
        available_agents: list[ClientInfo]
    ) -> Optional[str]:
        """Find appropriate agent for a task based on capabilities."""
        if task.target_agent_id:
            for agent in available_agents:
                if agent.client_id == task.target_agent_id:
                    return task.target_agent_id
            logger.warning(f"Requested agent {task.target_agent_id} not found")
            return None
        
        if task.target_capability:
            for agent in available_agents:
                if agent.profile and agent.profile.skills:
                    for skill_name, _ in agent.profile.skills:
                        if task.target_capability.lower() in skill_name.lower():
                            return agent.client_id
            logger.warning(f"No agent found with capability {task.target_capability}")
        
        if available_agents:
            return available_agents[0].client_id
        
        return None
    
    def get_available_agents(self) -> list[ClientInfo]:
        """Get list of available sub-agents from client registry."""
        all_clients = self.client_manager.get_all_clients()
        return [c for c in all_clients if c.profile and c.profile.role != "agent"]

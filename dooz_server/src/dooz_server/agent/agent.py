"""Main Agent class that orchestrates task handling."""
import logging
from typing import Optional

from .config import AgentConfig
from .prompt_loader import PromptLoader
from .llm_client import LLMClient
from .conversation import ConversationManager
from .task_router import TaskRouter, SubTask

logger = logging.getLogger("dooz_server.agent.agent")


class Agent:
    """Main AI agent that handles user messages and orchestrates sub-agents."""
    
    def __init__(
        self,
        config: AgentConfig,
        client_manager,
        work_directory: str
    ):
        """Initialize the agent."""
        self.config = config
        self.client_manager = client_manager
        self.work_directory = work_directory
        
        prompts_config = config.prompts
        prompts_dir = f"{work_directory}/{prompts_config.directory}"
        
        self.prompt_loader = PromptLoader(
            prompts_dir=prompts_dir,
            system_pattern=prompts_config.system_pattern,
            context_pattern=prompts_config.context_pattern,
            user_pattern=prompts_config.user_pattern
        )
        
        self.llm_client = LLMClient(config.llm)
        self.conversation = ConversationManager(max_history=10)
        self.task_router = TaskRouter(self.llm_client, client_manager)
        
        logger.info(f"Agent initialized: {config.agent.name} ({config.agent.device_id})")
    
    async def handle_message(self, user_id: str, message: str) -> dict:
        """Process user message and return agent response."""
        self.conversation.add_message(user_id, "user", message)
        
        try:
            available_agents = self.task_router.get_available_agents()
            agents_info = self._format_agents_info(available_agents)
            
            self.prompt_loader.update_context("context_agents.txt", agents_info)
            
            history_text = self.conversation.get_history_as_text(user_id)
            self.prompt_loader.update_context("context_history.txt", history_text)
            
            system_prompt = self.prompt_loader.system_prompt
            context_info = self.prompt_loader.context_info
            
            sub_tasks = await self.task_router.decompose_task(
                user_message=message,
                system_prompt=system_prompt,
                context_info=context_info
            )
            
            if not sub_tasks:
                response_text = "I couldn't understand your request. Please try again."
                self.conversation.add_message(user_id, "assistant", response_text)
                return {
                    "type": "agent_response",
                    "status": "error",
                    "message": response_text,
                    "sub_tasks": []
                }
            
            results = await self._execute_sub_tasks(sub_tasks, available_agents)
            
            response_text = self._aggregate_results(results)
            
            self.conversation.add_message(user_id, "assistant", response_text)
            
            return {
                "type": "agent_response",
                "status": "completed",
                "message": response_text,
                "sub_tasks": [
                    {
                        "task_id": r.task_id,
                        "description": r.description,
                        "status": "completed" if r.success else "error",
                        "result": r.result,
                        "error": r.error
                    }
                    for r in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {
                "type": "agent_response",
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "sub_tasks": []
            }
    
    def _format_agents_info(self, agents: list) -> str:
        """Format available agents for context."""
        if not agents:
            return "No available sub-agents currently."
        
        lines = ["Available sub-agents:"]
        for agent in agents:
            name = agent.name or agent.client_id
            role = agent.profile.role if agent.profile else "unknown"
            skills = ""
            if agent.profile and agent.profile.skills:
                skills = ", ".join(s[0] for s in agent.profile.skills)
            lines.append(f"- {name} ({role}): {skills}")
        
        return "\n".join(lines)
    
    async def _execute_sub_tasks(
        self,
        tasks: list[SubTask],
        available_agents: list
    ) -> list:
        """Execute sub-tasks by routing to sub-agents."""
        results = []
        
        for task in tasks:
            target_agent_id = self.task_router.find_agent_for_task(task, available_agents)
            
            if not target_agent_id:
                results.append(TaskResult(
                    task_id=task.task_id,
                    success=False,
                    result=None,
                    error=f"No available agent for task: {task.description}"
                ))
                continue
            
            try:
                logger.info(f"Routing task {task.task_id} to agent {target_agent_id}")
                
                results.append(TaskResult(
                    task_id=task.task_id,
                    success=True,
                    result=f"Routed to {target_agent_id}: {task.description}",
                    error=None
                ))
                
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                results.append(TaskResult(
                    task_id=task.task_id,
                    success=False,
                    result=None,
                    error=str(e)
                ))
        
        return results
    
    def _aggregate_results(self, results: list) -> str:
        """Aggregate task results into response text."""
        if not results:
            return "No tasks were executed."
        
        completed = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if failed:
            return f"Completed {len(completed)} task(s), {len(failed)} failed."
        else:
            return f"Completed {len(completed)} task(s)."


class TaskResult:
    """Result from executing a sub-task."""
    
    def __init__(
        self,
        task_id: str,
        success: bool,
        result: Optional[str],
        error: Optional[str]
    ):
        self.task_id = task_id
        self.success = success
        self.result = result
        self.error = error

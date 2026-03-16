"""Dooz Agent using claude-agent-sdk for LLM interactions."""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

try:
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

from .loader import SystemAgentsLoader
from .task_scheduler import Task, TaskScheduler, TaskResult

logger = logging.getLogger("dooz_server.system_agents.dooz_agent")

# Timeout for waiting task results (seconds)
TASK_RESULT_TIMEOUT = 60


class DoozAgent:
    """Dooz Assistant AI Agent using Claude Agent SDK.
    
    Processes user messages, detects if tasks need to be executed,
    coordinates with sub-agents via task scheduler, and returns
    natural language responses.
    """
    
    def __init__(
        self,
        config: dict[str, Any],
        prompt_loader: SystemAgentsLoader,
        ws_manager: Optional[Any] = None
    ):
        """Initialize Dooz Agent.
        
        Args:
            config: LLM configuration dict with keys:
                - provider: LLM provider (e.g., "anthropic", "openai")
                - model: Model name (e.g., "claude-sonnet-4-5")
                - api_key: API key for the provider
                - base_url: Optional base URL for API endpoint
                - temperature: Optional temperature setting
                - max_tokens: Optional max tokens setting
            prompt_loader: Prompt loader for system prompts.
            ws_manager: Optional WebSocket manager for sub-agent communication.
        """
        self.config = config
        self.prompt_loader = prompt_loader
        self.ws_manager = ws_manager
        
        self._client: Optional[ClaudeSDKClient] = None
        self._task_scheduler = TaskScheduler(ws_manager)
        self._initialized = False
        
        logger.info("DoozAgent initialized")
    
    async def start(self):
        """Initialize the Claude Agent SDK client."""
        if not SDK_AVAILABLE:
            raise RuntimeError("claude-agent-sdk not installed")
        
        if self._initialized:
            return
        
        # Build system prompt from loader
        system_prompt = self.prompt_loader.system_prompt
        context_info = self.prompt_loader.context_info
        
        # Combine system prompt with context
        full_system_prompt = system_prompt
        if context_info:
            full_system_prompt += f"\n\n{context_info}"
        
        # Get model configuration
        provider = self.config.get("provider", "anthropic")
        model = self.config.get("model", "claude-sonnet-4-5")
        api_key = self.config.get("api_key", "")
        base_url = self.config.get("base_url")
        temperature = self.config.get("temperature", 0.7)
        max_tokens = self.config.get("max_tokens", 4096)
        
        # Configure options
        options = ClaudeAgentOptions(
            model=model,
            system_prompt=full_system_prompt,
            permission_mode="default",
            max_turns=10,
            max_budget_usd=1.0,
            # Only allow Read tool for message processing
            allowed_tools=["Read"] if provider != "anthropic" else [],
            include_partial_messages=True,
        )
        
        # Initialize client
        self._client = ClaudeSDKClient(options=options)
        self._initialized = True
        
        logger.info(f"DoozAgent started with model: {model}")
    
    async def process_message(
        self,
        message: str,
        ws_manager: Optional[Any] = None
    ) -> str:
        """Process a user message and return agent response.
        
        Args:
            message: User message to process.
            ws_manager: Optional WebSocket manager override.
            
        Returns:
            Natural language response from the agent.
        """
        if not self._initialized:
            await self.start()
        
        # Update context with latest info
        self._update_context()
        
        # Query the LLM
        response = await self._query_llm(message)
        
        # Check if response contains tasks
        if self._contains_task(response):
            # Execute tasks and get results
            result_text = await self._execute_task(response, ws_manager)
            return result_text
        
        # Return direct response
        return self._extract_direct_response(response)
    
    def _update_context(self):
        """Update prompt context with current state."""
        # TODO: Implement context update from client manager
        # This is a placeholder - would integrate with actual client manager
        pass
    
    async def _query_llm(self, message: str) -> str:
        """Query the LLM with a message.
        
        Args:
            message: User message.
            
        Returns:
            LLM response text.
        """
        if self._client is None:
            return "Agent not initialized"
        
        try:
            # Query the model
            response = await self._client.query(message)
            
            # Collect full response
            full_response = ""
            async for msg in self._client.receive_response():
                if hasattr(msg, 'content'):
                    if isinstance(msg.content, str):
                        full_response += msg.content
                    elif hasattr(msg.content, 'text'):
                        full_response += msg.content.text
                elif hasattr(msg, 'text'):
                    full_response += msg.text
            
            return full_response if full_response else response
            
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return f"Error: {str(e)}"
    
    def _contains_task(self, message: str) -> bool:
        """Check if the message contains task definitions.
        
        Args:
            message: Response message to check.
            
        Returns:
            True if message contains task definitions.
        """
        # Check for "Tasks:" or "Tasks\n" pattern followed by JSON
        task_pattern = r'(?:^|\n)Tasks:\s*\n'
        return bool(re.search(task_pattern, message, re.MULTILINE))
    
    def _extract_direct_response(self, message: str) -> str:
        """Extract direct response from LLM message.
        
        Args:
            message: LLM response message.
            
        Returns:
            Extracted direct response text.
        """
        # Remove "Direct response:" prefix if present
        match = re.match(r'^Direct response:\s*', message)
        if match:
            return message[match.end():]
        
        # Remove any task section
        lines = message.split('\n')
        result_lines = []
        in_tasks = False
        
        for line in lines:
            if re.match(r'^Tasks:\s*$', line):
                in_tasks = True
                continue
            if in_tasks and line.strip() == ']':
                in_tasks = False
                continue
            if not in_tasks:
                result_lines.append(line)
        
        return '\n'.join(result_lines).strip()
    
    def _parse_tasks(self, message: str) -> list[Task]:
        """Parse tasks from LLM response.
        
        Args:
            message: LLM response containing task definitions.
            
        Returns:
            List of parsed Task objects.
        """
        tasks: list[Task] = []
        
        # Extract JSON array after "Tasks:"
        match = re.search(r'Tasks:\s*\n(\[[\s\S]*\])\s*$', message, re.MULTILINE)
        if not match:
            return tasks
        
        try:
            task_data = json.loads(match.group(1))
            
            for item in task_data:
                if isinstance(item, dict):
                    task = Task(
                        agent_id=item.get("agent_id", ""),
                        goal=item.get("goal", "")
                    )
                    tasks.append(task)
                    
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse tasks: {e}")
        
        return tasks
    
    async def _execute_task(
        self,
        message: str,
        ws_manager: Optional[Any] = None
    ) -> str:
        """Execute tasks found in the LLM response.
        
        Args:
            message: LLM response containing tasks.
            ws_manager: Optional WebSocket manager override.
            
        Returns:
            Formatted task execution results.
        """
        tasks = self._parse_tasks(message)
        if not tasks:
            return "No tasks to execute."
        
        # Use provided ws_manager or fallback to instance ws_manager
        scheduler_ws = ws_manager or self.ws_manager
        if scheduler_ws and self._task_scheduler.ws_manager is None:
            self._task_scheduler.ws_manager = scheduler_ws
        
        # Submit all tasks
        task_ids: list[str] = []
        for task in tasks:
            task_id = await self._task_scheduler.submit_task(task)
            task_ids.append(task_id)
        
        # Wait for results with timeout
        try:
            results = await asyncio.wait_for(
                self._collect_results(task_ids),
                timeout=TASK_RESULT_TIMEOUT
            )
        except asyncio.TimeoutError:
            return f"Task execution timed out after {TASK_RESULT_TIMEOUT}s"
        
        # Format and return results
        return self._format_task_result(results)
    
    async def _collect_results(self, task_ids: list[str]) -> list[TaskResult]:
        """Collect results from all submitted tasks.
        
        Args:
            task_ids: List of task IDs to collect.
            
        Returns:
            List of task results.
        """
        results: list[TaskResult] = []
        
        # Wait for each task result using asyncio.Event
        for task_id in task_ids:
            result = await self._task_scheduler.wait_for_result(
                task_id, 
                timeout=TASK_RESULT_TIMEOUT
            )
            if result:
                results.append(result)
            else:
                # Timeout for this task
                results.append(TaskResult(
                    task_id=task_id,
                    success=False,
                    error="Task execution timeout"
                ))
        
        return results
    
    def _format_task_result(self, results: list[TaskResult]) -> str:
        """Format task results into natural language.
        
        Args:
            results: List of task results.
            
        Returns:
            Formatted result text.
        """
        if not results:
            return "No tasks were executed."
        
        completed = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        parts: list[str] = []
        
        if completed:
            parts.append(f"Completed {len(completed)} task(s):")
            for r in completed:
                if r.result:
                    parts.append(f"- {r.result}")
        
        if failed:
            parts.append(f"\nFailed {len(failed)} task(s):")
            for r in failed:
                if r.error:
                    parts.append(f"- {r.error}")
        
        return '\n'.join(parts)
    
    async def handle_task_result(self, message: dict[str, Any]):
        """Handle incoming task result from sub-agent.
        
        Args:
            message: Task result message.
        """
        await self._task_scheduler.handle_sub_task_result(message)
    
    async def close(self):
        """Close the agent and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._initialized = False
        logger.info("DoozAgent closed")

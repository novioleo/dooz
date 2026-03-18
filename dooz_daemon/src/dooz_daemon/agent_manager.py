"""Agent process management."""

import asyncio
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dooz_daemon.schemas.agent import AgentDefinition

logger = logging.getLogger("dooz_daemon.agent_manager")


@dataclass
class AgentProcess:
    """Represents a running agent process."""
    agent_id: str
    name: str
    dooz_id: str
    mqtt_topic: str
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None


class AgentProcessManager:
    """Manages agent processes for a single Dooz."""
    
    def __init__(
        self,
        dooz_id: str,
        definitions_dir: Path | str | None = None,
    ):
        self.dooz_id = dooz_id
        self.definitions_dir = Path(definitions_dir) if definitions_dir else None
        self.processes: dict[str, AgentProcess] = {}
        self._running = False
    
    def spawn_agent(
        self,
        agent_id: str,
        name: str,
        mqtt_topic: str,
        config: Optional[dict] = None,
    ) -> AgentProcess:
        """Spawn a new agent process."""
        if agent_id in self.processes:
            logger.warning(f"Agent {agent_id} already running")
            return self.processes[agent_id]
        
        # Build MQTT topic
        full_topic = f"dooz/{self.dooz_id}/agents/{mqtt_topic}"
        
        # Create agent process
        agent_process = AgentProcess(
            agent_id=agent_id,
            name=name,
            dooz_id=self.dooz_id,
            mqtt_topic=full_topic,
        )
        
        # TODO: Actually spawn the process
        # For now, just track it in memory
        self.processes[agent_id] = agent_process
        logger.info(f"Spawned agent: {agent_id} ({name})")
        
        return agent_process
    
    def spawn_agents_from_definitions(
        self,
        agents: list[AgentDefinition],
    ) -> list[AgentProcess]:
        """Spawn agent processes from agent definitions."""
        spawned = []
        
        for agent_def in agents:
            if agent_def.role != "sub-agent":
                logger.info(f"Skipping system agent: {agent_def.agent_id}")
                continue
            
            process = self.spawn_agent(
                agent_id=agent_def.agent_id,
                name=agent_def.name,
                mqtt_topic=agent_def.mqtt.topic,
                config=agent_def.config,
            )
            spawned.append(process)
        
        return spawned
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a running agent process."""
        if agent_id not in self.processes:
            logger.warning(f"Agent {agent_id} not found")
            return False
        
        agent = self.processes[agent_id]
        
        if agent.process:
            agent.process.terminate()
            try:
                agent.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                agent.process.kill()
        
        del self.processes[agent_id]
        logger.info(f"Stopped agent: {agent_id}")
        
        return True
    
    async def stop_all(self):
        """Stop all agent processes."""
        agent_ids = list(self.processes.keys())
        
        for agent_id in agent_ids:
            await self.stop_agent(agent_id)
        
        logger.info(f"Stopped all agents for dooz: {self.dooz_id}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentProcess]:
        """Get an agent process by ID."""
        return self.processes.get(agent_id)
    
    def get_all_agents(self) -> list[AgentProcess]:
        """Get all agent processes."""
        return list(self.processes.values())

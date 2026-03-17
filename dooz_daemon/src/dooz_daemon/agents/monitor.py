"""Monitor Agent - tracks heartbeat from sub-agents."""

import time
import logging
from typing import Optional

from .base import Agent, AgentConfig, AgentMessage

logger = logging.getLogger("dooz_daemon.agents.monitor")


class MonitorAgent(Agent):
    """Monitor agent that tracks online sub-agents via heartbeat."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._agents: dict[str, dict] = {}  # agent_id -> {last_seen, status, capabilities}
        self._offline_threshold = 30  # seconds
    
    @property
    def subscribe_topics(self) -> list[str]:
        return [
            f"dooz/{self.config.dooz_id}/agents/+/heartbeat",
            f"dooz/{self.config.dooz_id}/system/monitor",
        ]
    
    async def handle_message(self, msg: AgentMessage):
        """Handle heartbeat and query messages."""
        if msg.type == "heartbeat":
            await self._handle_heartbeat(msg)
        elif msg.type == "query_agents":
            await self._handle_query(msg)
    
    async def _handle_heartbeat(self, msg: AgentMessage):
        """Update agent's last_seen timestamp."""
        agent_id = msg.payload.get("agent_id")
        if not agent_id:
            return
        
        capabilities = msg.payload.get("capabilities", [])
        
        self._agents[agent_id] = {
            "last_seen": time.time(),
            "status": "online",
            "capabilities": capabilities,
            "name": msg.payload.get("name", agent_id),
        }
        logger.debug(f"Heartbeat from {agent_id}")
    
    async def _handle_query(self, msg: AgentMessage):
        """Respond with list of online agents."""
        request_id = msg.payload.get("request_id", "unknown")
        from_dooz = msg.payload.get("from_dooz", self.config.dooz_id)
        
        # Filter online agents
        now = time.time()
        online_agents = []
        
        for agent_id, info in self._agents.items():
            if now - info["last_seen"] < self._offline_threshold:
                online_agents.append({
                    "agent_id": agent_id,
                    "name": info.get("name", agent_id),
                    "capabilities": info.get("capabilities", []),
                })
        
        # Publish response
        response = AgentMessage(
            type="agent_list",
            agent_id=self.config.agent_id,
            dooz_id=self.config.dooz_id,
            request_id=request_id,
            payload={"agents": online_agents},
        )
        
        response_topic = f"dooz/{from_dooz}/system/monitor/response/{request_id}"
        await self.publish(response_topic, response)
        logger.info(f"Responded with {len(online_agents)} agents")

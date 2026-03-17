"""Base agent class."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from ..mqtt_client import MqttClient, MqttMessage

logger = logging.getLogger("dooz_daemon.agents")


class AgentConfig:
    """Configuration for an agent."""
    
    def __init__(
        self,
        agent_id: str,
        dooz_id: str,
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
    ):
        self.agent_id = agent_id
        self.dooz_id = dooz_id
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
    
    @property
    def topic(self) -> str:
        """Get the agent's MQTT topic."""
        return f"dooz/{self.dooz_id}/agents/{self.agent_id}"


class AgentMessage:
    """Message format for agent communication."""
    
    def __init__(
        self,
        type: str,
        agent_id: str,
        dooz_id: str,
        payload: Optional[dict[str, Any]] = None,
        **extra,
    ):
        self.type = type
        self.agent_id = agent_id
        self.dooz_id = dooz_id
        self.payload = payload or {}
        self.extra = extra
    
    @classmethod
    def from_mqtt(cls, msg: MqttMessage) -> "AgentMessage":
        """Parse from MQTT message."""
        data = msg.data
        return cls(
            type=data.get("type", ""),
            agent_id=data.get("agent_id", ""),
            dooz_id=data.get("dooz_id", ""),
            payload=data.get("payload", {}),
            **{k: v for k, v in data.items() 
               if k not in ("type", "agent_id", "dooz_id", "payload")},
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        result = {
            "type": self.type,
            "agent_id": self.agent_id,
            "dooz_id": self.dooz_id,
            "payload": self.payload,
        }
        result.update(self.extra)
        return result
    
    def to_json(self) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict())


class Agent(ABC):
    """Base class for dooz agents."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._mqtt: Optional[MqttClient] = None
        self._running = False
    
    @property
    @abstractmethod
    def subscribe_topics(self) -> list[str]:
        """List of topics to subscribe to."""
        pass
    
    async def start(self):
        """Start the agent."""
        logger.info(f"Starting agent {self.config.agent_id}")
        
        self._mqtt = MqttClient(
            broker=self.config.mqtt_broker,
            port=self.config.mqtt_port,
            client_id=f"{self.config.dooz_id}_{self.config.agent_id}",
            on_message=self._on_message,
        )
        
        if not await self._mqtt.connect():
            logger.error(f"Failed to connect MQTT for {self.config.agent_id}")
            return
        
        # Subscribe to topics
        for topic in self.subscribe_topics:
            await self._mqtt.subscribe(topic)
        
        self._running = True
        logger.info(f"Agent {self.config.agent_id} started")
        
        # Keep running
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info(f"Agent {self.config.agent_id} cancelled")
    
    async def stop(self):
        """Stop the agent."""
        logger.info(f"Stopping agent {self.config.agent_id}")
        self._running = False
        
        if self._mqtt:
            await self._mqtt.disconnect()
    
    async def publish(self, topic: str, message: AgentMessage):
        """Publish message to MQTT."""
        if self._mqtt:
            await self._mqtt.publish(topic, message.to_dict())
    
    def _on_message(self, msg: MqttMessage):
        """Handle incoming MQTT message."""
        try:
            agent_msg = AgentMessage.from_mqtt(msg)
            asyncio.create_task(self.handle_message(agent_msg))
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    @abstractmethod
    async def handle_message(self, msg: AgentMessage):
        """Handle incoming message. Override in subclass."""
        pass

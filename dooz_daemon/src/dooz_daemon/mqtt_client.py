"""MQTT client for dooz daemon."""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt

logger = logging.getLogger("dooz_daemon.mqtt")


class MqttMessage:
    """MQTT message wrapper."""
    
    def __init__(
        self,
        topic: str,
        payload: str,
        qos: int = 0,
        retain: bool = False,
    ):
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain
    
    @property
    def data(self) -> dict[str, Any]:
        """Parse payload as JSON."""
        try:
            return json.loads(self.payload)
        except json.JSONDecodeError:
            return {"raw": self.payload}
    
    def __repr__(self) -> str:
        return f"MqttMessage(topic={self.topic}, payload={self.payload[:50]}...)"


class MqttClient:
    """Async MQTT client wrapper."""
    
    def __init__(
        self,
        broker: str,
        port: int,
        client_id: str,
        on_message: Optional[Callable[[MqttMessage], None]] = None,
    ):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.on_message = on_message
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._loop: Optional[asyncio.Task] = None
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected."""
        if rc == 0:
            self._connected = True
            logger.info(f"Connected to MQTT broker {self.broker}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received."""
        if self.on_message:
            message = MqttMessage(
                topic=msg.topic,
                payload=msg.payload.decode("utf-8"),
                qos=msg.qos,
                retain=msg.retain,
            )
            self.on_message(message)
    
    async def connect(self) -> bool:
        """Connect to MQTT broker."""
        self._client = mqtt.Client(client_id=self.client_id)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        
        try:
            self._client.connect(self.broker, self.port, keepalive=60)
            self._client.loop_start()
            
            # Wait for connection
            for _ in range(50):  # 5 seconds max
                if self._connected:
                    return True
                await asyncio.sleep(0.1)
            
            logger.error("MQTT connection timeout")
            return False
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("Disconnected from MQTT broker")
    
    async def subscribe(self, topic: str, qos: int = 1) -> bool:
        """Subscribe to a topic."""
        if not self._connected:
            logger.error("Not connected to MQTT broker")
            return False
        
        result = self._client.subscribe(topic, qos)
        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Subscribed to topic: {topic}")
            return True
        else:
            logger.error(f"Failed to subscribe to {topic}")
            return False
    
    async def publish(self, topic: str, payload: str | dict, qos: int = 1) -> bool:
        """Publish to a topic."""
        if not self._connected:
            logger.error("Not connected to MQTT broker")
            return False
        
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        
        result = self._client.publish(topic, payload, qos)
        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published to {topic}: {payload[:50]}...")
            return True
        else:
            logger.error(f"Failed to publish to {topic}")
            return False

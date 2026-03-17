"""Dooz daemon main module."""

import asyncio
import logging
from typing import Any, Optional

from .config import DaemonConfig
from .mqtt_client import MqttClient, MqttMessage
from .websocket_server import WebSocketServer, WsMessage, WebSocketServerProtocol

logger = logging.getLogger("dooz_daemon")


class DoozDaemon:
    """Main daemon process for dooz."""
    
    def __init__(self, config: DaemonConfig):
        self.config = config
        self._running = False
        self._mqtt_client: Optional[MqttClient] = None
        self._ws_server: Optional[WebSocketServer] = None
    
    async def _handle_ws_message(
        self,
        message: WsMessage,
        client: WebSocketServerProtocol,
    ) -> dict[str, Any]:
        """Handle WebSocket message from CLI."""
        logger.info(f"Received message: {message.type} from {message.session_id}")
        
        # Echo back for now (Phase 1 - no agent logic yet)
        if message.type == "user_message":
            return {
                "type": "response",
                "session_id": message.session_id,
                "content": f"Echo: {message.content}",
            }
        elif message.type == "ping":
            return {"type": "pong", "session_id": message.session_id}
        else:
            return {
                "type": "error",
                "session_id": message.session_id,
                "message": f"Unknown message type: {message.type}",
            }
    
    async def start(self):
        """Start the daemon."""
        logger.info("Starting dooz daemon...")
        
        # Start MQTT client
        self._mqtt_client = MqttClient(
            broker=self.config.mqtt.broker,
            port=self.config.mqtt.port,
            client_id=self.config.mqtt.client_id,
        )
        
        if not await self._mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker")
            return
        
        # Start WebSocket server
        self._ws_server = WebSocketServer(
            host=self.config.host,
            port=self.config.port,
            message_handler=self._handle_ws_message,
        )
        await self._ws_server.start()
        
        self._running = True
        logger.info("Dooz daemon started successfully")
        
        # Keep running
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Daemon cancelled")
    
    async def stop(self):
        """Stop the daemon."""
        logger.info("Stopping dooz daemon...")
        self._running = False
        
        if self._ws_server:
            await self._ws_server.stop()
        
        if self._mqtt_client:
            await self._mqtt_client.disconnect()
        
        logger.info("Dooz daemon stopped")

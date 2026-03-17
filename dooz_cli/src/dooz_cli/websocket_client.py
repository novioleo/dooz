"""WebSocket client for dooz CLI."""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger("dooz_cli")


class CliClient:
    """WebSocket client for CLI."""
    
    def __init__(
        self,
        uri: str = "ws://localhost:8765",
        on_message: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        self.uri = uri
        self.on_message = on_message
        self._ws: Optional[WebSocketClientProtocol] = None
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """Connect to daemon."""
        try:
            self._ws = await websockets.connect(self.uri)
            logger.info(f"Connected to {self.uri}")
            self._running = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from daemon."""
        self._running = False
        if self._ws:
            await self._ws.close()
            logger.info("Disconnected from daemon")
    
    async def send(self, message: dict[str, Any]) -> bool:
        """Send message to daemon."""
        if not self._ws:
            logger.error("Not connected")
            return False
        
        try:
            await self._ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def _receive_loop(self):
        """Receive messages from daemon."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    if self.on_message:
                        self.on_message(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        finally:
            self._running = False
    
    async def start_receiving(self):
        """Start receiving messages."""
        self._receive_task = asyncio.create_task(self._receive_loop())
    
    async def stop_receiving(self):
        """Stop receiving messages."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
    
    @property
    def is_connected(self) -> bool:
        return self._ws is not None and self._running

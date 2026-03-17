"""Dooz CLI main interface."""

import asyncio
import logging
import uuid
from typing import Optional

from .websocket_client import CliClient

logger = logging.getLogger("dooz_cli")


class DoozCLI:
    """Dooz command-line interface."""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.client: Optional[CliClient] = None
        self.session_id = str(uuid.uuid4())
        self._running = False
    
    async def _handle_message(self, data: dict):
        """Handle message from daemon."""
        msg_type = data.get("type", "")
        
        if msg_type == "response":
            print(f"\n[data] {data.get('content', '')}")
        elif msg_type == "error":
            print(f"\n[error] {data.get('message', 'Unknown error')}")
        elif msg_type == "pong":
            print("\n[pong] Daemon is alive")
        else:
            print(f"\n[{msg_type}] {data}")
        
        if self._running:
            print("> ", end="", flush=True)
    
    async def connect(self) -> bool:
        """Connect to daemon."""
        self.client = CliClient(self.uri, on_message=self._handle_message)
        return await self.client.connect()
    
    async def disconnect(self):
        """Disconnect from daemon."""
        if self.client:
            await self.client.disconnect()
    
    async def send_message(self, content: str, dooz_id: Optional[str] = None):
        """Send user message to daemon."""
        if not self.client:
            logger.error("Not connected to daemon")
            return
        
        message = {
            "type": "user_message",
            "session_id": self.session_id,
            "content": content,
        }
        
        if dooz_id:
            message["dooz_id"] = dooz_id
        
        await self.client.send(message)
    
    async def ping(self) -> bool:
        """Ping daemon."""
        if not self.client:
            return False
        
        return await self.client.send({
            "type": "ping",
            "session_id": self.session_id,
        })

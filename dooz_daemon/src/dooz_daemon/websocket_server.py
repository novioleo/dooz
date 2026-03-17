"""WebSocket server for dooz daemon."""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger("dooz_daemon.ws")


class WsMessage:
    """WebSocket message."""
    
    def __init__(
        self,
        type: str,
        session_id: str,
        content: Optional[str] = None,
        dooz_id: Optional[str] = None,
        **kwargs,
    ):
        self.type = type
        self.session_id = session_id
        self.content = content
        self.dooz_id = dooz_id
        self.extra = kwargs
    
    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "WsMessage":
        """Parse from JSON."""
        return cls(
            type=data.get("type", ""),
            session_id=data.get("session_id", ""),
            content=data.get("content"),
            dooz_id=data.get("dooz_id"),
            **{k: v for k, v in data.items() 
               if k not in ("type", "session_id", "content", "dooz_id")},
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        result = {"type": self.type, "session_id": self.session_id}
        if self.content is not None:
            result["content"] = self.content
        if self.dooz_id is not None:
            result["dooz_id"] = self.dooz_id
        result.update(self.extra)
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class WebSocketServer:
    """WebSocket server for CLI connections."""
    
    def __init__(
        self,
        host: str,
        port: int,
        message_handler: Callable[[WsMessage, WebSocketServerProtocol], Any],
    ):
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self._server: Optional[websockets.Server] = None
        self._clients: set[WebSocketServerProtocol] = set()
    
    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """Handle a client connection."""
        self._clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    ws_msg = WsMessage.from_json(data)
                    
                    # Process message
                    response = await self.message_handler(ws_msg, websocket)
                    
                    # Send response if any
                    if response:
                        if isinstance(response, WsMessage):
                            await websocket.send(response.to_json())
                        elif isinstance(response, dict):
                            await websocket.send(json.dumps(response))
                        elif isinstance(response, str):
                            await websocket.send(response)
                            
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {websocket.remote_address}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            self._clients.discard(websocket)
    
    async def start(self):
        """Start the WebSocket server."""
        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
        )
        logger.info(f"WebSocket server started on {self.host}:{self.port}")
    
    async def stop(self):
        """Stop the WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def broadcast(self, message: WsMessage | dict):
        """Broadcast message to all clients."""
        if isinstance(message, WsMessage):
            msg_str = message.to_json()
        else:
            msg_str = json.dumps(message)
        
        if self._clients:
            await asyncio.gather(
                *[client.send(msg_str) for client in self._clients],
                return_exceptions=True,
            )

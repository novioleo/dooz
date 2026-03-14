# dooz_server/test_clients/client_base.py
"""Base client class for WebSocket communication."""
import asyncio
import websockets
import json
from typing import Optional


class WebSocketClient:
    """Base WebSocket client with message handling."""
    
    def __init__(self, client_id: str, name: str, server_url: str = "ws://localhost:8000"):
        self.client_id = client_id
        self.name = name
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
    
    async def connect(self):
        """Connect to the WebSocket server."""
        uri = f"{self.server_url}/ws/{self.client_id}"
        self.websocket = await websockets.connect(uri)
        print(f"[{self.name}] Connected as {self.client_id}")
    
    async def send(self, message: dict):
        """Send a JSON message."""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
    
    async def receive(self) -> dict:
        """Receive a JSON message."""
        if self.websocket:
            data = await self.websocket.recv()
            return json.loads(data)
        return {}
    
    async def handle_message(self, message: dict):
        """Handle incoming message - override in subclass."""
        msg_type = message.get("type")
        print(f"[{self.name}] Received: {message}")
        
        if msg_type == "message":
            print(f"  >> Message from {message.get('from_client_id')}: {message.get('content')}")
        elif msg_type == "message_sent":
            success = message.get("success")
            print(f"  >> Message send result: {success}")
        elif msg_type == "pending_delivered":
            print(f"  >> Received {message.get('count')} pending messages")
        elif msg_type == "message_expired":
            print(f"  >> Message expired! To: {message.get('to_client_id')}, Content: {message.get('content')}")
        elif msg_type == "heartbeat_ack":
            print(f"  >> Heartbeat acknowledged")
    
    async def listen(self):
        """Listen for incoming messages."""
        self.running = True
        try:
            while self.running:
                message = await self.receive()
                if message:
                    await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.name}] Connection closed")
    
    async def send_heartbeat(self):
        """Send periodic heartbeat."""
        while self.running:
            await asyncio.sleep(10)
            await self.send({"type": "heartbeat"})
    
    async def close(self):
        """Close the connection."""
        self.running = False
        if self.websocket:
            await self.websocket.close()

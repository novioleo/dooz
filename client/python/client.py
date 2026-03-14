"""dooz Python Client."""

import asyncio
import json
import logging
import httpx
import websockets
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Client:
    def __init__(self, config: dict):
        self.config = config
        device = config.get("device", {})
        self.device_id = device.get("id")
        self.wisdom = device.get("wisdom", 50)
        self.output = device.get("output", False)
        self.skills = {s.get("name"): s for s in device.get("skills", [])}
        
        server = config.get("server", {})
        self.server_url = server.get("url", "http://localhost:8000")
        self.tenant_id = server.get("tenant_id")
        self.client_id = server.get("auth", {}).get("client_id")
        self.client_secret = server.get("auth", {}).get("client_secret")
        
        self._ws = None
        self._token = None
        self._handlers = {}
    
    async def connect(self) -> bool:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{self.server_url}/auth/token",
                data={"username": self.client_id, "password": self.client_secret}
            )
            if resp.status_code != 200:
                logger.error("Auth failed")
                return False
            self._token = resp.json()["access_token"]
        
        ws_url = f"{self.server_url.replace('http', 'ws')}/ws/tenant/{self.tenant_id}?token={self._token}"
        self._ws = await websockets.connect(ws_url)
        
        await self.send({
            "msg_type": "device/announce",
            "device": {
                "device_id": self.device_id,
                "name": self.config.get("device", {}).get("name"),
                "wisdom": self.wisdom,
                "output": self.output,
                "skills": list(self.skills.keys())
            }
        })
        
        logger.info(f"Connected: {self.device_id}")
        return True
    
    async def disconnect(self):
        if self._ws:
            await self._ws.close()
    
    def on(self, msg_type: str, handler):
        self._handlers[msg_type] = handler
    
    async def send(self, msg: dict):
        await self._ws.send(json.dumps(msg))
    
    async def loop(self):
        try:
            async for msg in self._ws:
                data = json.loads(msg)
                msg_type = data.get("msg_type", "")
                if msg_type in self._handlers:
                    self._handlers[msg_type](data)
        except Exception as e:
            logger.error(f"Connection error: {e}")
    
    async def send_request(self, text: str):
        import uuid
        await self.send({
            "msg_type": "task/request",
            "request_id": str(uuid.uuid4()),
            "text": text,
            "requester_id": self.device_id,
        })

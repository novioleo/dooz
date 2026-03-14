# dooz_server/src/dooz_server/router.py
"""FastAPI router with WebSocket endpoint for message server."""
import json
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Annotated, Optional

from .client_manager import ClientManager
from .message_handler import MessageHandler
from .message_queue import MessageQueue
from .schemas import ClientListResponse, MessageRequest, MessageResponse
from .heartbeat import HeartbeatMonitor

logger = logging.getLogger("dooz_server")

router = APIRouter()

# Global singletons
_client_manager: Optional[ClientManager] = None
_message_handler: Optional[MessageHandler] = None
_heartbeat_monitor: Optional[HeartbeatMonitor] = None
ws_manager = None


def get_client_manager() -> ClientManager:
    global _client_manager
    if _client_manager is None:
        _client_manager = ClientManager()
    return _client_manager


def get_message_handler() -> MessageHandler:
    global _message_handler
    if _message_handler is None:
        _message_handler = MessageHandler(get_client_manager(), MessageQueue())
    return _message_handler


def get_heartbeat_monitor() -> HeartbeatMonitor:
    global _heartbeat_monitor
    if _heartbeat_monitor is None:
        _heartbeat_monitor = HeartbeatMonitor(timeout_seconds=30)
    return _heartbeat_monitor


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized")
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


def get_ws_manager() -> ConnectionManager:
    global ws_manager
    if ws_manager is None:
        ws_manager = ConnectionManager()
    return ws_manager


# HTTP Endpoints

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    client_manager = get_client_manager()
    client_count = len(client_manager.get_all_clients())
    logger.info(f"Health check: OK (connected clients: {client_count})")
    return {
        "status": "ok",
        "connected_clients": client_count
    }


@router.get("/clients", response_model=ClientListResponse)
async def list_clients(
    client_manager: Annotated[ClientManager, Depends(get_client_manager)]
):
    """List all connected clients."""
    clients = client_manager.get_all_clients()
    logger.info(f"Client list requested: {len(clients)} clients")
    return ClientListResponse(clients=clients, total=len(clients))


@router.get("/clients/{client_id}")
async def get_client(
    client_id: str,
    client_manager: Annotated[ClientManager, Depends(get_client_manager)]
):
    """Get specific client information."""
    client_info = client_manager.get_client_info(client_id)
    if not client_info:
        logger.warning(f"Client info requested for non-existent client: {client_id}")
        raise HTTPException(status_code=404, detail="Client not found")
    return client_info


@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    from_client_id: str,  # Would come from WebSocket auth in production
    message_handler: Annotated[MessageHandler, Depends(get_message_handler)]
):
    """Send a message to another client."""
    success, msg, msg_id = message_handler.send_message(
        from_client_id=from_client_id,
        to_client_id=request.to_client_id,
        content=request.content,
        ttl_seconds=request.ttl_seconds or 3600
    )
    
    if not success:
        error_code = "recipient_not_found" if "not found" in msg.lower() else "recipient_offline"
        logger.warning(f"Message send failed: {msg} (from={from_client_id}, to={request.to_client_id})")
        return MessageResponse(
            success=False,
            message=msg,
            error_code=error_code
        )
    
    logger.info(f"HTTP message sent: from={from_client_id}, to={request.to_client_id}, msg_id={msg_id}")
    return MessageResponse(
        success=True,
        message=msg,
        message_id=msg_id,
        from_client_id=from_client_id
    )


@router.get("/messages/pending/{client_id}")
async def get_pending_messages(
    client_id: str,
    message_handler: Annotated[MessageHandler, Depends(get_message_handler)]
):
    """Get pending messages for a client."""
    messages = message_handler.get_pending_messages(client_id)
    logger.info(f"Pending messages requested for {client_id}: {len(messages)} messages")
    return {
        "messages": [
            {
                "message_id": m.message_id,
                "from_client_id": m.from_client_id,
                "content": m.content,
                "created_at": m.created_at,
                "expires_at": m.expires_at
            }
            for m in messages
        ],
        "total": len(messages)
    }


@router.post("/messages/check-expired")
async def check_expired_messages(
    message_handler: Annotated[MessageHandler, Depends(get_message_handler)]
):
    """Check for expired messages and notify senders."""
    expired = message_handler.check_expired_messages()
    logger.info(f"Expired messages check: {len(expired)} messages expired")
    return {
        "expired_count": len(expired),
        "messages": expired
    }


# WebSocket Endpoint

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for client connections with heartbeat support."""
    ws_mgr = get_ws_manager()
    await ws_mgr.connect(client_id, websocket)
    
    # Register with client manager (auto-register if not exists)
    client_manager = get_client_manager()
    logger.info(f"WebSocket: Checking client {client_id}, existing: {client_manager.get_client_info(client_id)}")
    existing_client = client_manager.get_client_info(client_id)
    if not existing_client:
        # Auto-register new client with name derived from client_id
        client_name = client_id.split('-')[0].capitalize() if '-' in client_id else client_id
        registered_id = client_manager.register_client(client_id, client_name, "WebSocket")
        logger.info(f"WebSocket: Registered new client {registered_id}, now exists: {client_manager.get_client_info(client_id)}")
    client_manager.add_connection(client_id, websocket)
    
    # Record initial heartbeat
    heartbeat_monitor = get_heartbeat_monitor()
    await heartbeat_monitor.record_heartbeat(client_id)
    
    logger.info(f"WebSocket connection established: client_id={client_id}")
    
    # Deliver any pending offline messages
    message_handler = get_message_handler()
    pending_count = message_handler.deliver_pending_messages(client_id)
    if pending_count > 0:
        await ws_mgr.send_personal_message({
            "type": "pending_delivered",
            "count": pending_count
        }, client_id)
        logger.info(f"Delivered {pending_count} pending messages to {client_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "message":
                # Send message to another client
                message_handler = get_message_handler()
                to_client = message_data.get("to_client_id")
                content = message_data.get("content")
                ttl_seconds = message_data.get("ttl_seconds", 3600)
                
                success, msg, msg_id = message_handler.send_message(
                    from_client_id=client_id,
                    to_client_id=to_client,
                    content=content,
                    ttl_seconds=ttl_seconds
                )
                
                # Send confirmation back to sender
                await ws_mgr.send_personal_message({
                    "type": "message_sent",
                    "success": success,
                    "message": msg,
                    "message_id": msg_id,
                    "to_client_id": to_client
                }, client_id)
                
                logger.info(f"WS message: {client_id} -> {to_client}: {content[:30]}...")
            
            elif message_type == "ping":
                # Record heartbeat and respond
                await heartbeat_monitor.record_heartbeat(client_id)
                await ws_mgr.send_personal_message({
                    "type": "pong"
                }, client_id)
                logger.debug(f"Heartbeat ping from {client_id}")
            
            elif message_type == "heartbeat":
                # Explicit heartbeat from client
                await heartbeat_monitor.record_heartbeat(client_id)
                await ws_mgr.send_personal_message({
                    "type": "heartbeat_ack",
                    "server_time": asyncio.get_event_loop().time()
                }, client_id)
                logger.debug(f"Heartbeat from {client_id}")
                
    except WebSocketDisconnect:
        ws_mgr.disconnect(client_id)
        heartbeat_monitor.remove_client(client_id)
        client_manager.remove_connection(client_id)
        logger.info(f"WebSocket disconnected: client_id={client_id}")

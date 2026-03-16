"""FastAPI router with WebSocket endpoint for message server."""
import json
import asyncio
import logging
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Annotated, Optional, Any

from .client_manager import ClientManager
from .message_handler import MessageHandler
from .message_queue import MessageQueue
from .schemas import ClientListResponse, ClientProfile, MessageRequest, MessageResponse
from .heartbeat import HeartbeatMonitor

logger = logging.getLogger("dooz_server")

router = APIRouter()

# Message Types
MESSAGE_TYPES = {
    "message", "message_sent", "ping", "pong", "heartbeat", "heartbeat_ack",
    "pending_delivered", "agent_connected", "agent_response"
}

# Task Message Types
TASK_MESSAGE_TYPES = {
    "task_submit",      # Dooz Agent -> Task Scheduler
    "task_result",      # Task Scheduler -> Dooz Agent
    "sub_task",         # Task Scheduler -> Sub-Agent
    "sub_task_result",  # Sub-Agent -> Task Scheduler
    "task_failed",      # Sub-Agent -> Task Scheduler
}

_client_manager: Optional[ClientManager] = None
_message_handler: Optional[MessageHandler] = None
_heartbeat_monitor: Optional[HeartbeatMonitor] = None
_task_scheduler: Optional[Any] = None
ws_manager = None


def get_task_scheduler() -> "TaskScheduler":
    global _task_scheduler
    if _task_scheduler is None:
        from dooz_server.system_agents.task_scheduler import TaskScheduler
        _task_scheduler = TaskScheduler(get_ws_manager())
    return _task_scheduler


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
    client_manager: Annotated[ClientManager, Depends(get_client_manager)],
    role: Optional[str] = None,
):
    """List all connected clients, optionally filtered by role."""
    clients = client_manager.get_all_clients()
    
    if role:
        clients = [
            c for c in clients 
            if c.profile and c.profile.role.lower() == role.lower()
        ]
    
    logger.info(f"Client list requested: {len(clients)} clients (role filter: {role})")
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
    from_client_id: str,
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


async def handle_websocket_message(
    ws_mgr: ConnectionManager,
    from_client_id: str,
    to_client_id: str,
    content: str,
    ttl_seconds: int,
    log_prefix: str,
) -> tuple[bool, str, Optional[str]]:
    """Send a message via message_handler and send response via WebSocket."""
    message_handler = get_message_handler()
    success, msg, msg_id = message_handler.send_message(
        from_client_id=from_client_id,
        to_client_id=to_client_id,
        content=content,
        ttl_seconds=ttl_seconds
    )
    
    await ws_mgr.send_personal_message({
        "type": "message_sent",
        "success": success,
        "message": msg,
        "message_id": msg_id,
        "to_client_id": to_client_id
    }, from_client_id)
    
    logger.info(f"{log_prefix}: {from_client_id} -> {to_client_id}: {content[:30]}...")
    return success, msg, msg_id


@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str, profile: Optional[str] = None):
    """WebSocket endpoint for client connections with heartbeat support and optional profile."""
    ws_mgr = get_ws_manager()
    await ws_mgr.connect(device_id, websocket)
    
    client_profile = None
    profile_device_id = None
    if profile:
        try:
            profile_data = json.loads(urllib.parse.unquote(profile))
            client_profile = ClientProfile(**profile_data)
            profile_device_id = client_profile.device_id
        except Exception as e:
            logger.warning(f"Failed to parse profile for {device_id}: {e}")
    
    final_device_id = profile_device_id if profile_device_id == device_id else device_id
    
    client_manager = get_client_manager()
    logger.info(f"WebSocket: Checking device {final_device_id}, existing: {client_manager.get_client_info(final_device_id)}")
    existing_client = client_manager.get_client_info(final_device_id)
    if not existing_client:
        client_name = client_profile.name if client_profile else (final_device_id.split('-')[0].capitalize() if '-' in final_device_id else final_device_id)
        registered_id = client_manager.register_client(final_device_id, client_name, client_profile, "WebSocket")
        logger.info(f"WebSocket: Registered new client {registered_id}, now exists: {client_manager.get_client_info(final_device_id)}")
    client_manager.add_connection(final_device_id, websocket)
    
    heartbeat_monitor = get_heartbeat_monitor()
    await heartbeat_monitor.record_heartbeat(final_device_id)
    
    logger.info(f"WebSocket connection established: device_id={final_device_id}")
    
    message_handler = get_message_handler()
    pending_count = message_handler.deliver_pending_messages(final_device_id)
    if pending_count > 0:
        await ws_mgr.send_personal_message({
            "type": "pending_delivered",
            "count": pending_count
        }, final_device_id)
        logger.info(f"Delivered {pending_count} pending messages to {final_device_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "message":
                to_client = message_data.get("to_client_id")
                content = message_data.get("content")
                ttl_seconds = message_data.get("ttl_seconds", 3600)
                await handle_websocket_message(
                    ws_mgr, final_device_id, to_client, content, ttl_seconds, "WS message"
                )
            
            elif message_type == "ping":
                await heartbeat_monitor.record_heartbeat(final_device_id)
                await ws_mgr.send_personal_message({
                    "type": "pong"
                }, final_device_id)
                logger.debug(f"Heartbeat ping from {final_device_id}")
            
            elif message_type == "heartbeat":
                await heartbeat_monitor.record_heartbeat(final_device_id)
                await ws_mgr.send_personal_message({
                    "type": "heartbeat_ack",
                    "server_time": asyncio.get_event_loop().time()
                }, final_device_id)
                logger.debug(f"Heartbeat from {final_device_id}")
            
            elif message_type == "task_submit":
                # Task submission from Dooz Agent
                task_scheduler = get_task_scheduler()
                task_data = message_data.get("task_data", {})
                
                from dooz_server.system_agents.task_scheduler import Task
                task = Task(
                    agent_id=task_data.get("agent_id", ""),
                    goal=task_data.get("goal", ""),
                    params=task_data.get("params", {})
                )
                
                # Wait for task result and send back to dooz-agent
                result = await task_scheduler.submit_task_and_wait(task)
                
                await ws_mgr.send_personal_message({
                    "type": "task_result",
                    "task_id": result.task_id,
                    "status": "completed" if result.success else "failed",
                    "success": result.success,
                    "result": result.result,
                    "error": result.error
                }, final_device_id)
                
                logger.info(f"Task completed: {result.task_id} success={result.success}")
            
            elif message_type == "sub_task":
                # Route sub-task to target sub-agent
                target_agent = message_data.get("to_client_id") or message_data.get("agent_id")
                if target_agent:
                    await ws_mgr.send_personal_message(message_data, target_agent)
                    logger.info(f"Sub-task routed to {target_agent}: {message_data.get('task_id')}")
            
            elif message_type == "sub_task_result":
                # Result from sub-agent
                task_scheduler = get_task_scheduler()
                await task_scheduler.handle_sub_task_result(message_data)
                logger.info(f"Sub-task result received: {message_data.get('task_id')}")
            
            elif message_type == "task_failed":
                # Failure from sub-agent
                task_scheduler = get_task_scheduler()
                await task_scheduler.handle_sub_task_result({
                    **message_data,
                    "success": False
                })
                logger.info(f"Task failed: {message_data.get('task_id')}")
                
    except WebSocketDisconnect:
        ws_mgr.disconnect(final_device_id)
        heartbeat_monitor.remove_client(final_device_id)
        client_manager.remove_connection(final_device_id)
        logger.info(f"WebSocket disconnected: device_id={final_device_id}")

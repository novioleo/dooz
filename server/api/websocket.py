"""WebSocket API."""

import json
import logging
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.transport.bus import bus
from server.core.protocol import TopicPrefix

logger = logging.getLogger(__name__)

router = APIRouter()

_clients: Dict[str, WebSocket] = {}


@router.websocket("/tenant/{tenant_id}")
async def ws_endpoint(ws: WebSocket, tenant_id: str):
    logger.info(f"WebSocket connection request: tenant={tenant_id}")
    
    token = ws.query_params.get("token")
    logger.info(f"Token: {token[:20] if token else None}...")
    
    if not token:
        await ws.close(code=4001, reason="Missing token")
        return
    
    # 验证 token (必须在 accept 之前)
    try:
        from server.api.auth import verify_token
        payload = verify_token(token)
        client_id = payload.get("sub")
        logger.info(f"Client verified: {client_id}")
        
        if payload.get("tenant_id") != tenant_id:
            await ws.close(code=4003, reason="Tenant mismatch")
            return
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        await ws.close(code=4002, reason=f"Invalid token: {e}")
        return
    
    # 接受连接
    await ws.accept()
    logger.info(f"WebSocket accepted for {client_id}")
    _clients[client_id] = ws
    
    # 创建回调
    def make_callback(ws_client_id: str):
        async def callback(message: dict):
            executor_id = message.get("executor_id", "")
            if executor_id and executor_id != ws_client_id:
                return
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
        return callback
    
    topics = [
        TopicPrefix.task_dispatch(tenant_id),
        TopicPrefix.task_response(tenant_id),
        TopicPrefix.task_notify(tenant_id),
        TopicPrefix.device_announce(tenant_id),
        TopicPrefix.device_offline(tenant_id),
    ]
    callbacks = {}
    for topic in topics:
        cb = make_callback(client_id)
        callbacks[topic] = cb
        bus.subscribe(topic, cb)
    
    logger.info(f"Subscribed to topics: {topics}")
    
    topics_map = {
        "device/announce": TopicPrefix.device_announce(tenant_id),
        "device/heartbeat": TopicPrefix.device_heartbeat(tenant_id),
        "device/offline": TopicPrefix.device_offline(tenant_id),
        "task/request": TopicPrefix.task_request(tenant_id),
        "task/dispatch": TopicPrefix.task_dispatch(tenant_id),
        "task/response": TopicPrefix.task_response(tenant_id),
    }
    
    try:
        while True:
            # 使用 recv() 而不是 async for
            data = await ws.receive_text()
            msg = json.loads(data)
            msg_type = msg.get("msg_type", "")
            logger.info(f"Received: {msg_type}")
            
            topic = topics_map.get(msg_type)
            if topic:
                bus.publish(topic, msg)
                
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    finally:
        for topic, cb in callbacks.items():
            bus.unsubscribe(topic, cb)
        _clients.pop(client_id, None)

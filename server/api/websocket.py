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
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4001)
        return
    
    try:
        from server.api.auth import verify_token
        payload = verify_token(token)
        client_id = payload.get("sub")
        if payload.get("tenant_id") != tenant_id:
            await ws.close(code=4003)
            return
    except:
        await ws.close(code=4002)
        return
    
    await ws.accept()
    _clients[client_id] = ws
    
    def make_callback(ws_client_id: str):
        async def callback(message: dict):
            executor_id = message.get("executor_id", "")
            if executor_id and executor_id != ws_client_id:
                return
            try:
                await ws.send_json(message)
            except Exception:
                pass
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
    
    try:
        async for msg in ws:
            data = json.loads(msg)
            msg_type = data.get("msg_type", "")
            
            topics_map = {
                "device/announce": TopicPrefix.device_announce(tenant_id),
                "device/heartbeat": TopicPrefix.device_heartbeat(tenant_id),
                "device/offline": TopicPrefix.device_offline(tenant_id),
                "task/request": TopicPrefix.task_request(tenant_id),
                "task/dispatch": TopicPrefix.task_dispatch(tenant_id),
                "task/response": TopicPrefix.task_response(tenant_id),
            }
            
            topic = topics_map.get(msg_type)
            if topic:
                bus.publish(topic, data)
                
    except WebSocketDisconnect:
        pass
    finally:
        for topic, cb in callbacks.items():
            bus.unsubscribe(topic, cb)
        _clients.pop(client_id, None)

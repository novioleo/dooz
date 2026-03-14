"""LLM API."""

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_tenant_manager = None


def set_tenant_manager(mgr):
    global _tenant_manager
    _tenant_manager = mgr


class ChatRequest(BaseModel):
    messages: list


class ChatResponse(BaseModel):
    content: str


@router.post("/{tenant_id}/chat", response_model=ChatResponse)
async def chat(tenant_id: str, req: ChatRequest, token: str = None):
    from server.api.auth import verify_token
    try:
        client = verify_token(token) if token else None
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if not client or client.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403)
    
    tenant = _tenant_manager.get(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404)
    
    headers = {"Authorization": f"Bearer {tenant.llm_provider.api_key}"}
    payload = {
        "model": tenant.llm_provider.model,
        "messages": req.messages,
    }
    
    async with httpx.AsyncClient(timeout=60.0) as http:
        resp = await http.post(tenant.llm_provider.url, headers=headers, json=payload)
        resp.raise_for_status()
        result = resp.json()
        return ChatResponse(content=result["choices"][0]["message"]["content"])

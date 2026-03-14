"""Tenant API."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

_tenant_manager = None


def set_tenant_manager(mgr):
    global _tenant_manager
    _tenant_manager = mgr


class CreateRequest(BaseModel):
    name: str
    llm_url: str
    llm_api_key: str
    llm_model: str = "gpt-4"


@router.post("/create")
async def create_tenant(req: CreateRequest):
    tenant = _tenant_manager.create(req.name, req.llm_url, req.llm_api_key, req.llm_model)
    return {
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "client_id": tenant.client_id,
        "client_secret": tenant.client_secret,
        "llm_provider": {
            "url": tenant.llm_provider.url,
            "model": tenant.llm_provider.model,
        }
    }

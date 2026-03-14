"""租户管理器."""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LLMProvider:
    url: str
    api_key: str
    model: str = "gpt-4"


@dataclass
class Tenant:
    tenant_id: str
    name: str
    llm_provider: LLMProvider
    client_id: str = ""
    client_secret: str = ""


class TenantManager:
    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
    
    def create(self, name: str, llm_url: str, llm_key: str, model: str = "gpt-4") -> Tenant:
        tid = f"tenant-{uuid.uuid4().hex[:8]}"
        client_id = f"client-{uuid.uuid4().hex[:8]}"
        client_secret = uuid.uuid4().hex[:16]
        
        tenant = Tenant(
            tenant_id=tid,
            name=name,
            llm_provider=LLMProvider(llm_url, llm_key, model),
            client_id=client_id,
            client_secret=client_secret,
        )
        self._tenants[tid] = tenant
        return tenant
    
    def get(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)
    
    def verify_client(self, client_id: str, client_secret: str) -> Optional[Tenant]:
        for t in self._tenants.values():
            if t.client_id == client_id and t.client_secret == client_secret:
                return t
        return None


# 全局实例
tenant_manager = TenantManager()

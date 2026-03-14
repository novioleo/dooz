# dooz_server/src/dooz_server/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClientInfo(BaseModel):
    """Information about a connected client."""
    client_id: str
    name: str
    connected_at: str


class MessageRequest(BaseModel):
    """Request to send a message to another client."""
    to_client_id: str = Field(..., description="Target client ID")
    content: str = Field(..., min_length=1, description="Message content")
    ttl_seconds: Optional[int] = Field(default=3600, description="Message TTL in seconds (0 = no expiry)")


class MessageResponse(BaseModel):
    """Response after sending a message."""
    success: bool
    message: str
    message_id: Optional[str] = None
    from_client_id: Optional[str] = None
    error_code: Optional[str] = None


class ClientListResponse(BaseModel):
    """Response containing list of connected clients."""
    clients: list[ClientInfo]
    total: int


class PendingMessagesResponse(BaseModel):
    """Response containing pending messages for a client."""
    messages: list[dict]
    total: int

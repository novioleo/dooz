# dooz_server/src/dooz_server/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ClientProfile(BaseModel):
    """Profile information for a registered client."""
    model_config = ConfigDict(extra='ignore')
    
    name: str = Field(..., min_length=1, description="Client display name")
    role: str = Field(..., min_length=1, description="Client role (e.g., agent, user, service)")
    extra_info: Optional[str] = Field(default=None, description="Custom extra information")
    skills: list[tuple[str, str]] = Field(default_factory=list, description="List of (ability_name, ability_description) tuples")
    supports_input: bool = Field(default=False, description="Whether client supports input")
    supports_output: bool = Field(default=False, description="Whether client supports output")


class ClientInfo(BaseModel):
    """Information about a connected client."""
    client_id: str
    name: str
    connected_at: str
    profile: Optional[ClientProfile] = Field(default=None, description="Client profile information")


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

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal
from datetime import datetime


# System agent roles (hardcoded)
SYSTEM_AGENT_ROLES = Literal["dooz", "system", "sub-agent", "user"]


class ClientProfile(BaseModel):
    """Profile information for a registered client."""
    model_config = ConfigDict(extra='ignore')
    
    device_id: str = Field(..., min_length=1, description="Unique device identifier (permanent)")
    name: str = Field(..., min_length=1, description="Client display name")
    role: str = Field(..., min_length=1, description="Client role (e.g., agent, user, service)")
    extra_info: Optional[str] = Field(default=None, description="Custom extra information")
    skills: list[tuple[str, str]] = Field(default_factory=list, description="List of (ability_name, ability_description) tuples")
    supports_input: bool = Field(default=False, description="Whether client supports input")
    supports_output: bool = Field(default=False, description="Whether client supports output")
    is_system: bool = Field(default=False, description="Whether this is a system agent")

    @field_validator('device_id', 'name', 'role', mode='before')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v


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


# =======================
# Task Orchestration Schemas
# =======================


class SubTask(BaseModel):
    """A sub-task to be executed by a sub-agent."""
    sub_task_id: str = Field(..., description="Unique sub-task identifier")
    agent_id: str = Field(..., description="Target agent device_id")
    goal: str = Field(..., description="What this sub-agent should achieve")
    parameters: dict = Field(default_factory=dict, description="Optional parameters")


class Task(BaseModel):
    """Task structure for sub-agent execution."""
    task_id: str = Field(..., description="Unique task identifier")
    goal: str = Field(..., description="User's final goal description")
    sub_tasks: list[SubTask] = Field(default_factory=list, description="List of sub-tasks")


class SubTaskResult(BaseModel):
    """Result from a sub-task execution."""
    sub_task_id: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class TaskResult(BaseModel):
    """Aggregated task result."""
    task_id: str
    status: Literal["completed", "failed", "partial"]
    sub_results: list[SubTaskResult]
    completed_at: datetime = Field(default_factory=datetime.now)

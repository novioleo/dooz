"""Agent definition schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class Skill(BaseModel):
    """Skill definition for an agent."""
    name: str = Field(..., description="Skill name")
    description: str = Field(default="", description="Skill description")


class AgentMqttConfig(BaseModel):
    """MQTT configuration for an agent."""
    topic: str = Field(..., description="MQTT topic (relative to dooz/{dooz_id}/agents/)")
    subscribe: list[str] = Field(
        default_factory=list,
        description="Topics to subscribe to"
    )
    publish: list[str] = Field(
        default_factory=list,
        description="Topics to publish to"
    )


class AgentDefinition(BaseModel):
    """Agent definition loaded from YAML."""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Agent description")
    role: str = Field(default="sub-agent", description="Agent role (sub-agent)")
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of capabilities this agent provides"
    )
    skills: list[Skill] = Field(
        default_factory=list,
        description="Skills this agent possesses"
    )
    mqtt: AgentMqttConfig = Field(..., description="MQTT configuration")
    config: dict = Field(
        default_factory=dict,
        description="Additional agent-specific configuration"
    )
    
    model_config = {"extra": "ignore"}

"""Dooz definition schemas."""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DoozMqttConfig(BaseModel):
    """MQTT configuration for a Dooz."""
    topic_prefix: str = Field(
        default="dooz/{dooz_id}",
        description="MQTT topic prefix (dooz_id will be substituted)"
    )


class DoozDefinition(BaseModel):
    """Dooz definition loaded from YAML."""
    dooz_id: str = Field(
        ...,
        description="Unique identifier, format: dooz_{level}_{index}"
    )
    name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Dooz description")
    role: str = Field(
        default="dooz",
        description="dooz: single dooz; dooz-group: contains nested dooz"
    )
    agents: list[str] = Field(
        default_factory=list,
        description="Referenced agent_id list"
    )
    nested_dooz: list[str] = Field(
        default_factory=list,
        description="Nested dooz_id list"
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Capabilities this dooz provides"
    )
    mqtt: DoozMqttConfig = Field(
        default_factory=DoozMqttConfig,
        description="MQTT configuration"
    )
    config: dict = Field(
        default_factory=dict,
        description="Additional dooz-specific configuration"
    )
    
    model_config = {"extra": "ignore"}
    
    @field_validator("dooz_id")
    @classmethod
    def validate_dooz_id(cls, v: str) -> str:
        """Validate dooz_id format: dooz_{level}_{index}."""
        pattern = r"^dooz_\d+_\d+$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid dooz_id format: {v}. Expected format: dooz_{{level}}_{{index}}"
            )
        return v

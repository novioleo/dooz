"""Configuration loading for Agent feature."""
import json
import os
import re
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("dooz_server.agent.config")


class AgentSettings(BaseModel):
    """Agent configuration settings."""
    enabled: bool = Field(default=False)
    device_id: str = Field(default="dooz-agent")
    name: str = Field(default="Dooz Assistant")


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o")
    api_key: str = Field(default="")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4096)
    timeout_seconds: int = Field(default=30)


class PromptsConfig(BaseModel):
    """Prompts directory configuration."""
    directory: str = Field(default="prompts")
    system_pattern: str = Field(default="system_*.txt")
    context_pattern: str = Field(default="context_*.txt")
    user_pattern: str = Field(default="user_*.txt")


class AgentConfig(BaseModel):
    """Main agent configuration."""
    agent: AgentSettings = Field(default_factory=AgentSettings)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)


def _substitute_env_vars(value: str) -> str:
    """Substitute ${ENV_VAR} patterns with environment variables."""
    pattern = r'\$\{([^}]+)\}'
    
    def replacer(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))
    
    return re.sub(pattern, replacer, value)


def _process_config_value(value):
    """Recursively process config values for env var substitution."""
    if isinstance(value, str):
        return _substitute_env_vars(value)
    elif isinstance(value, dict):
        return {k: _process_config_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_process_config_value(item) for item in value]
    return value


def load_agent_config(config_path: str) -> Optional[AgentConfig]:
    """Load agent configuration from JSON file."""
    path = Path(config_path)
    
    if not path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return None
    
    try:
        with open(path, 'r') as f:
            raw_data = json.load(f)
        
        processed_data = _process_config_value(raw_data)
        config = AgentConfig(**processed_data)
        logger.info(f"Loaded agent config from {config_path}")
        return config
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None

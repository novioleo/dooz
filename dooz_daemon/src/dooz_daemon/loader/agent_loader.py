"""Agent definition loader."""

import logging
from pathlib import Path
from typing import Optional

import yaml

from dooz_daemon.schemas.agent import AgentDefinition

logger = logging.getLogger("dooz_daemon.loader")


class AgentLoader:
    """Loads agent definitions from YAML files."""
    
    def __init__(self, definitions_dir: Path | str):
        self.definitions_dir = Path(definitions_dir)
    
    def load_file(self, file_path: Path) -> Optional[AgentDefinition]:
        """Load a single agent definition from YAML file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "agent" not in data:
                logger.warning(f"No 'agent' key in {file_path}")
                return None
            
            return AgentDefinition(**data["agent"])
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    def load_all(self) -> list[AgentDefinition]:
        """Load all agent definitions from the definitions directory."""
        agents = []
        
        if not self.definitions_dir.exists():
            logger.warning(f"Definitions directory does not exist: {self.definitions_dir}")
            return agents
        
        for file_path in self.definitions_dir.glob("*.yaml"):
            agent = self.load_file(file_path)
            if agent:
                agents.append(agent)
                logger.info(f"Loaded agent: {agent.agent_id}")
        
        return agents
    
    def load(self, agent_id: str) -> Optional[AgentDefinition]:
        """Load a specific agent by ID."""
        file_path = self.definitions_dir / f"{agent_id}.yaml"
        
        if not file_path.exists():
            logger.warning(f"Agent file not found: {file_path}")
            return None
        
        return self.load_file(file_path)

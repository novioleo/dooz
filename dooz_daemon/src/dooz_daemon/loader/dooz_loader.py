"""Dooz definition loader."""

import logging
from pathlib import Path
from typing import Optional

import yaml

from dooz_daemon.schemas.dooz import DoozDefinition

logger = logging.getLogger("dooz_daemon.loader")


class DoozLoader:
    """Loads dooz definitions from YAML files."""
    
    def __init__(self, definitions_dir: Path | str):
        self.definitions_dir = Path(definitions_dir)
    
    def load_file(self, file_path: Path) -> Optional[DoozDefinition]:
        """Load a single dooz definition from YAML file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not data or "dooz" not in data:
                logger.warning(f"No 'dooz' key in {file_path}")
                return None
            
            return DoozDefinition(**data["dooz"])
            
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    def load_all(self) -> list[DoozDefinition]:
        """Load all dooz definitions from the definitions directory."""
        dooz_list = []
        
        if not self.definitions_dir.exists():
            logger.warning(f"Definitions directory does not exist: {self.definitions_dir}")
            return dooz_list
        
        for file_path in self.definitions_dir.glob("*.yaml"):
            dooz = self.load_file(file_path)
            if dooz:
                dooz_list.append(dooz)
                logger.info(f"Loaded dooz: {dooz.dooz_id}")
        
        return dooz_list
    
    def load(self, dooz_id: str) -> Optional[DoozDefinition]:
        """Load a specific dooz by ID."""
        file_path = self.definitions_dir / f"{dooz_id}.yaml"
        
        if not file_path.exists():
            logger.warning(f"Dooz file not found: {file_path}")
            return None
        
        return self.load_file(file_path)

"""Prompt loading from work directory."""
import logging
import os
from pathlib import Path
from typing import Optional
from fnmatch import fnmatch

logger = logging.getLogger("dooz_server.agent.prompt_loader")


class PromptLoader:
    """Loads and manages prompt templates from work directory."""
    
    def __init__(
        self,
        prompts_dir: str,
        system_pattern: str = "*_system*.txt",
        context_pattern: str = "*_context*.txt",
        user_pattern: str = "*_user*.txt"
    ):
        """Initialize prompt loader."""
        self.prompts_dir = Path(prompts_dir)
        self.system_pattern = system_pattern
        self.context_pattern = context_pattern
        self.user_pattern = user_pattern
        
        self._system_parts: list[tuple[int, str]] = []
        self._context_parts: list[tuple[int, str]] = []
        self._user_parts: list[tuple[int, str]] = []
        
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt files from directory."""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return
        
        self._system_parts = self._load_prompt_files(self.system_pattern)
        self._context_parts = self._load_prompt_files(self.context_pattern)
        self._user_parts = self._load_prompt_files(self.user_pattern)
        
        logger.info(f"Loaded prompts: {len(self._system_parts)} system, "
                   f"{len(self._context_parts)} context, {len(self._user_parts)} user")
    
    def _load_prompt_files(self, pattern: str) -> list[tuple[int, str]]:
        """Load prompt files matching pattern, return sorted by priority."""
        parts = []
        
        for file_path in self.prompts_dir.glob(pattern):
            try:
                content = file_path.read_text(encoding='utf-8').strip()
                if content:
                    priority = self._extract_priority(file_path.name)
                    parts.append((priority, content))
            except Exception as e:
                logger.warning(f"Failed to load prompt {file_path}: {e}")
        
        parts.sort(key=lambda x: x[0])
        return parts
    
    def _extract_priority(self, filename: str) -> int:
        """Extract priority number from filename."""
        name = Path(filename).stem
        parts = name.split('_', 1)
        try:
            return int(parts[0])
        except (ValueError, IndexError):
            return 99
    
    @property
    def system_prompt(self) -> str:
        return '\n'.join(part[1] for part in self._system_parts)
    
    @property
    def context_info(self) -> str:
        return '\n'.join(part[1] for part in self._context_parts)
    
    @property
    def user_message_template(self) -> str:
        return '\n'.join(part[1] for part in self._user_parts)
    
    def update_context(self, file_name: str, content: str):
        """Update a context prompt at runtime."""
        self._context_parts = []
        priority = self._extract_priority(file_name)
        self._context_parts.append((priority, content))
        self._context_parts.sort(key=lambda x: x[0])
        logger.debug(f"Updated context: {file_name}")
    
    def build_prompt(self, user_message: str) -> tuple[str, str, str]:
        """Build complete prompt for LLM."""
        return (self.system_prompt, self.context_info, user_message)

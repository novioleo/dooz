"""Prompt loading for system agents from markdown files."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("dooz_server.system_agents.loader")


class SystemAgentsLoader:
    """Loads and manages prompt templates from markdown files.
    
    Loads prompt files from the prompts directory with naming pattern:
    - 00_*.md - System role prompts (required)
    - 10_*.md - Context about agents
    - 20_*.md - Context about conversation history
    
    Files are sorted by priority number prefix and concatenated.
    """
    
    def __init__(self, base_dir: str):
        """Initialize prompt loader.
        
        Args:
            base_dir: Base directory containing the prompts subdirectory.
        """
        self.base_dir = Path(base_dir)
        self.prompts_dir = self.base_dir / "prompts"
        
        self._system_parts: list[tuple[int, str]] = []
        self._context_parts: list[tuple[int, str]] = []
        
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt files from prompts directory."""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return
        
        # Load system role prompts (00_*.md) - required
        self._system_parts = self._load_prompt_files("00_*.md")
        
        # Check if system role file exists (required by spec)
        system_role_files = list(self.prompts_dir.glob("00_system_role.md"))
        if not system_role_files:
            raise FileNotFoundError(
                f"Missing required file: 00_system_role.md in {self.prompts_dir}"
            )
        
        # Load context prompts (10_*.md, 20_*.md)
        self._context_parts = self._load_prompt_files("1[0-9]_*.md")
        self._context_parts.extend(self._load_prompt_files("2[0-9]_*.md"))
        
        logger.info(
            f"Loaded prompts: {len(self._system_parts)} system, "
            f"{len(self._context_parts)} context"
        )
    
    def _load_prompt_files(self, pattern: str) -> list[tuple[int, str]]:
        """Load prompt files matching pattern, return sorted by priority.
        
        Args:
            pattern: Glob pattern to match files.
            
        Returns:
            List of (priority, content) tuples sorted by priority.
        """
        parts: list[tuple[int, str]] = []
        
        for file_path in sorted(self.prompts_dir.glob(pattern)):
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
        """Extract priority number from filename.
        
        Args:
            filename: Name of the prompt file.
            
        Returns:
            Priority number extracted from filename prefix.
        """
        name = Path(filename).stem
        # Extract leading number (e.g., "00_system_role" -> 0)
        parts = name.split('_', 1)
        try:
            return int(parts[0])
        except (ValueError, IndexError):
            return 99
    
    @property
    def system_prompt(self) -> str:
        """Get concatenated system prompt from all system prompt files.
        
        Returns:
            System prompt text, or empty string if no files loaded.
        """
        if not self._system_parts:
            return ""
        return '\n\n'.join(part[1] for part in self._system_parts)
    
    @property
    def context_info(self) -> str:
        """Get concatenated context info from all context prompt files.
        
        Returns:
            Context info text, or empty string if no files loaded.
        """
        if not self._context_parts:
            return ""
        return '\n\n'.join(part[1] for part in self._context_parts)
    
    def update_context(self, file_prefix: str, content: str):
        """Update a context prompt at runtime.
        
        Args:
            file_prefix: Prefix to identify the context file (e.g., "10").
            content: New content for the context.
        """
        # Remove existing entry with same prefix
        self._context_parts = [
            (p, c) for p, c in self._context_parts if p // 10 != int(file_prefix) // 10
        ]
        
        priority = self._extract_priority(f"{file_prefix}_context.md")
        self._context_parts.append((priority, content))
        self._context_parts.sort(key=lambda x: x[0])
        logger.debug(f"Updated context: {file_prefix}")
    
    def build_prompt(self, user_message: str) -> tuple[str, str, str]:
        """Build complete prompt for LLM.
        
        Args:
            user_message: The user's message to include.
            
        Returns:
            Tuple of (system_prompt, context_info, user_message).
        """
        return (self.system_prompt, self.context_info, user_message)

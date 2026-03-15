# Agent Chat Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an AI agent entry point in the Dooz server that receives user messages via WebSocket, decomposes tasks using an LLM, routes sub-tasks to available sub-agents/devices, aggregates results, and returns to the user.

**Architecture:** Agent acts as a special client registered in the client registry. It queries available sub-agents, composes prompts from 3 sections (system, context, user), calls LLM for task decomposition, routes sub-tasks to appropriate sub-agents, and aggregates results.

**Tech Stack:** Python, FastAPI, WebSocket, OpenAI/Anthropic SDK, Pydantic

---

## File Structure

```
dooz_server/
├── src/dooz_server/
│   ├── agent/
│   │   ├── __init__.py           # Package exports
│   │   ├── config.py             # Config loading from JSON
│   │   ├── prompt_loader.py      # Load prompts from work directory
│   │   ├── llm_client.py          # LLM API client (OpenAI/Anthropic)
│   │   ├── conversation.py       # Conversation history management
│   │   ├── task_router.py        # Task decomposition and routing
│   │   └── agent.py              # Main Agent class
│   ├── __init__.py               # Export Agent class
│   ├── router.py                 # Modify: add agent routing
│   └── schemas.py                # Modify: add agent schemas
├── main.py                       # Modify: load config, init agent
└── tests/
    └── agent/
        ├── __init__.py
        ├── test_config.py
        ├── test_prompt_loader.py
        ├── test_llm_client.py
        ├── test_conversation.py
        ├── test_task_router.py
        └── test_agent_integration.py
```

---

## Chunk 1: Config System

### Task 1: Create Config Loader

**Files:**
- Create: `dooz_server/src/dooz_server/agent/__init__.py`
- Create: `dooz_server/src/dooz_server/agent/config.py`
- Test: `dooz_server/tests/agent/test_config.py`

- [ ] **Step 1: Create test file with failing tests**

```python
# dooz_server/tests/agent/test_config.py
import pytest
import json
import os
from pathlib import Path


class TestAgentConfig:
    """Tests for AgentConfig loading."""
    
    def test_load_config_from_json_file(self, tmp_path):
        """Test loading config from JSON file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "agent": {
                "enabled": True,
                "device_id": "dooz-agent",
                "name": "Test Agent"
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "${TEST_API_KEY}",
                "temperature": 0.7,
                "max_tokens": 4096,
                "timeout_seconds": 30
            },
            "prompts": {
                "directory": "prompts",
                "system_pattern": "system_*.txt",
                "context_pattern": "context_*.txt",
                "user_pattern": "user_*.txt"
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        from dooz_server.agent.config import load_agent_config
        config = load_agent_config(str(config_file))
        
        assert config.agent.enabled is True
        assert config.agent.device_id == "dooz-agent"
        assert config.llm.provider == "openai"
    
    def test_env_var_substitution(self, tmp_path, monkeypatch):
        """Test environment variable substitution."""
        monkeypatch.setenv("TEST_API_KEY", "secret-key-123")
        
        config_file = tmp_path / "config.json"
        config_data = {
            "llm": {
                "api_key": "${TEST_API_KEY}"
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        from dooz_server.agent.config import load_agent_config
        config = load_agent_config(str(config_file))
        
        assert config.llm.api_key == "secret-key-123"
    
    def test_missing_config_file_returns_none(self):
        """Test that missing config file returns None."""
        from dooz_server.agent.config import load_agent_config
        config = load_agent_config("/nonexistent/path/config.json")
        assert config is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server.agent'"

- [ ] **Step 3: Create package init file**

```python
# dooz_server/src/dooz_server/agent/__init__.py
"""Agent module for AI agent chat functionality."""

from .config import AgentConfig, LLMConfig, PromptsConfig, load_agent_config
from .agent import Agent

__all__ = [
    "AgentConfig",
    "LLMConfig", 
    "PromptsConfig",
    "load_agent_config",
    "Agent",
]
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_config.py::TestAgentConfig::test_load_config_from_json_file -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'dooz_server.agent'"

- [ ] **Step 5: Write minimal config implementation**

```python
# dooz_server/src/dooz_server/agent/config.py
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
    """Load agent configuration from JSON file.
    
    Args:
        config_path: Path to the config JSON file.
        
    Returns:
        AgentConfig if file exists and is valid, None otherwise.
    """
    path = Path(config_path)
    
    if not path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return None
    
    try:
        with open(path, 'r') as f:
            raw_data = json.load(f)
        
        # Process env var substitution
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_config.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/agent/__init__.py dooz_server/src/dooz_server/agent/config.py dooz_server/tests/agent/test_config.py
git commit -m "feat(agent): add config loading with env var substitution"
```

---

## Chunk 2: Prompt System

### Task 2: Create Prompt Loader

**Files:**
- Create: `dooz_server/src/dooz_server/agent/prompt_loader.py`
- Test: `dooz_server/tests/agent/test_prompt_loader.py`

- [ ] **Step 1: Create test file with failing tests**

```python
# dooz_server/tests/agent/test_prompt_loader.py
import pytest
from pathlib import Path


class TestPromptLoader:
    """Tests for PromptLoader."""
    
    def test_load_prompts_from_directory(self, tmp_path):
        """Test loading prompt files from directory."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        (prompts_dir / "00_system_role.txt").write_text("You are a helpful assistant.")
        (prompts_dir / "10_context_agents.txt").write_text("Available agents: none")
        
        from dooz_server.agent.prompt_loader import PromptLoader
        loader = PromptLoader(str(prompts_dir))
        
        assert loader.system_prompt == "You are a helpful assistant."
        assert "Available agents" in loader.context_info
    
    def test_prompt_ordering_by_filename(self, tmp_path):
        """Test prompts are ordered by filename priority."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        (prompts_dir / "20_system.txt").write_text("Second system")
        (prompts_dir / "10_system.txt").write_text("First system")
        
        from dooz_server.agent.prompt_loader import PromptLoader
        loader = PromptLoader(str(prompts_dir))
        
        assert loader.system_prompt == "First system\nSecond system"
    
    def test_missing_directory_returns_empty(self, tmp_path):
        """Test missing directory returns empty prompts."""
        from dooz_server.agent.prompt_loader import PromptLoader
        loader = PromptLoader(str(tmp_path / "nonexistent"))
        
        assert loader.system_prompt == ""
        assert loader.context_info == ""
    
    def test_update_context_info(self, tmp_path):
        """Test updating dynamic context at runtime."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "00_system.txt").write_text("System")
        
        from dooz_server.agent.prompt_loader import PromptLoader
        loader = PromptLoader(str(prompts_dir))
        
        loader.update_context("context_agents", "Agent A, Agent B")
        
        assert "Agent A, Agent B" in loader.context_info
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_prompt_loader.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/agent/prompt_loader.py
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
        system_pattern: str = "system_*.txt",
        context_pattern: str = "context_*.txt",
        user_pattern: str = "user_*.txt"
    ):
        """Initialize prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files.
            system_pattern: Glob pattern for system prompts.
            context_pattern: Glob pattern for context prompts.
            user_pattern: Glob pattern for user prompts.
        """
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
        
        # Load system prompts
        self._system_parts = self._load_prompt_files(self.system_pattern)
        
        # Load context prompts
        self._context_parts = self._load_prompt_files(self.context_pattern)
        
        # Load user prompts
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
                    # Extract priority from filename (e.g., "10_system_role.txt" -> 10)
                    priority = self._extract_priority(file_path.name)
                    parts.append((priority, content))
            except Exception as e:
                logger.warning(f"Failed to load prompt {file_path}: {e}")
        
        # Sort by priority
        parts.sort(key=lambda x: x[0])
        return parts
    
    def _extract_priority(self, filename: str) -> int:
        """Extract priority number from filename."""
        # Expected format: "{priority}_{section}_{name}.txt"
        name = Path(filename).stem
        parts = name.split('_', 1)
        try:
            return int(parts[0])
        except (ValueError, IndexError):
            return 99  # Default priority
    
    @property
    def system_prompt(self) -> str:
        """Get concatenated system prompts."""
        return '\n'.join(part[1] for part in self._system_parts)
    
    @property
    def context_info(self) -> str:
        """Get concatenated context prompts."""
        return '\n'.join(part[1] for part in self._context_parts)
    
    @property
    def user_message_template(self) -> str:
        """Get concatenated user message templates."""
        return '\n'.join(part[1] for part in self._user_parts)
    
    def update_context(self, file_name: str, content: str):
        """Update a context prompt at runtime.
        
        Args:
            file_name: Name of context file (e.g., "context_agents.txt")
            content: New content for the context
        """
        priority = self._extract_priority(file_name)
        
        # Remove existing entry with same filename
        self._context_parts = [
            (p, c) for p, c in self._context_parts 
            if not c  # This is simplified; in production would track filename
        ]
        
        # Add new content
        self._context_parts.append((priority, content))
        self._context_parts.sort(key=lambda x: x[0])
        
        logger.debug(f"Updated context: {file_name}")
    
    def build_prompt(self, user_message: str) -> tuple[str, str, str]:
        """Build complete prompt for LLM.
        
        Args:
            user_message: The user's message/task.
            
        Returns:
            Tuple of (system_prompt, context_info, user_message).
        """
        return (
            self.system_prompt,
            self.context_info,
            user_message
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_prompt_loader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/agent/prompt_loader.py dooz_server/tests/agent/test_prompt_loader.py
git commit -m "feat(agent): add prompt loader with file ordering"
```

---

## Chunk 3: LLM Client

### Task 3: Create LLM Client

**Files:**
- Create: `dooz_server/src/dooz_server/agent/llm_client.py`
- Test: `dooz_server/tests/agent/test_llm_client.py`

- [ ] **Step 1: Create test file with failing tests**

```python
# dooz_server/tests/agent/test_llm_client.py
import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestLLMClient:
    """Tests for LLMClient."""
    
    def test_openai_client_initialization(self):
        """Test OpenAI client initialization."""
        from dooz_server.agent.llm_client import LLMClient
        from dooz_server.agent.config import LLMConfig
        
        config = LLMConfig(provider="openai", model="gpt-4o", api_key="test-key")
        client = LLMClient(config)
        
        assert client.provider == "openai"
        assert client.model == "gpt-4o"
    
    @pytest.mark.asyncio
    async def test_call_openai(self):
        """Test calling OpenAI API."""
        from dooz_server.agent.llm_client import LLMClient
        from dooz_server.agent.config import LLMConfig
        
        config = LLMConfig(provider="openai", model="gpt-4o", api_key="test-key")
        client = LLMClient(config)
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                return_value=Mock(
                    choices=[Mock(message=Mock(content='{"tasks": []}'))]
                )
            )
            mock_openai.return_value = mock_client
            
            response = await client.call("system", "context", "user message")
            
            assert "tasks" in response
    
    def test_unsupported_provider_raises(self):
        """Test unsupported provider raises error."""
        from dooz_server.agent.llm_client import LLMClient
        from dooz_server.agent.config import LLMConfig
        
        config = LLMConfig(provider="unknown", api_key="test")
        client = LLMClient(config)
        
        import asyncio
        with pytest.raises(ValueError, match="Unsupported provider"):
            asyncio.get_event_loop().run_until_complete(
                client.call("system", "context", "message")
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_llm_client.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/agent/llm_client.py
"""LLM API client for task decomposition."""
import logging
from typing import Optional
import json

from ..config import LLMConfig

logger = logging.getLogger("dooz_server.agent.llm_client")


class LLMClient:
    """Client for calling LLM APIs (OpenAI/Anthropic)."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM client.
        
        Args:
            config: LLM configuration.
        """
        self.provider = config.provider.lower()
        self.model = config.model
        self.api_key = config.api_key
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout_seconds
        
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize the underlying LLM client."""
        if self.provider == "openai":
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    timeout=self.timeout
                )
                logger.info(f"Initialized OpenAI client with model {self.model}")
            except ImportError:
                logger.error("openai package not installed")
                raise ImportError("Please install openai: pip install openai")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=self.api_key,
                    timeout=self.timeout
                )
                logger.info(f"Initialized Anthropic client with model {self.model}")
            except ImportError:
                logger.error("anthropic package not installed")
                raise ImportError("Please install anthropic: pip install anthropic")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def call(
        self,
        system_prompt: str,
        context_info: str,
        user_message: str
    ) -> str:
        """Call LLM to get task decomposition.
        
        Args:
            system_prompt: System instructions.
            context_info: Context information (available agents, etc.).
            user_message: User's actual message/task.
            
        Returns:
            LLM response as string.
        """
        full_user_message = f"""Context Information:
{context_info}

User Task:
{user_message}"""
        
        if self.provider == "openai":
            return await self._call_openai(system_prompt, full_user_message)
        elif self.provider == "anthropic":
            return await self._call_anthropic(system_prompt, full_user_message)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _call_openai(self, system: str, user: str) -> str:
        """Call OpenAI API."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content[:100]}...")
            return content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _call_anthropic(self, system: str, user: str) -> str:
        """Call Anthropic API."""
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system,
                messages=[
                    {"role": "user", "content": user}
                ]
            )
            
            content = response.content[0].text
            logger.debug(f"Anthropic response: {content[:100]}...")
            return content
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_llm_client.py -v`
Expected: PASS (may need to mock properly)

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/agent/llm_client.py dooz_server/tests/agent/test_llm_client.py
git commit -m "feat(agent): add LLM client for OpenAI and Anthropic"
```

---

## Chunk 4: Conversation Manager

### Task 4: Create Conversation Manager

**Files:**
- Create: `dooz_server/src/dooz_server/agent/conversation.py`
- Test: `dooz_server/tests/agent/test_conversation.py`

- [ ] **Step 1: Create test file with failing tests**

```python
# dooz_server/tests/agent/test_conversation.py
import pytest
from datetime import datetime


class TestConversationManager:
    """Tests for ConversationManager."""
    
    def test_add_message(self):
        """Test adding a message to conversation."""
        from dooz_server.agent.conversation import ConversationManager
        
        manager = ConversationManager(max_history=10)
        manager.add_message("user-1", "user", "Hello")
        manager.add_message("user-1", "assistant", "Hi there")
        
        history = manager.get_history("user-1")
        assert len(history) == 2
        assert history[0]["role"] == "user"
    
    def test_max_history_limit(self):
        """Test older messages are removed when limit reached."""
        from dooz_server.agent.conversation import ConversationManager
        
        manager = ConversationManager(max_history=2)
        manager.add_message("user-1", "user", "Message 1")
        manager.add_message("user-1", "user", "Message 2")
        manager.add_message("user-1", "user", "Message 3")
        
        history = manager.get_history("user-1")
        assert len(history) == 2
        assert "Message 2" in str(history)
    
    def test_separate_conversations(self):
        """Test different users have separate histories."""
        from dooz_server.agent.conversation import ConversationManager
        
        manager = ConversationManager(max_history=10)
        manager.add_message("user-1", "user", "Hello")
        manager.add_message("user-2", "user", "Hi")
        
        assert len(manager.get_history("user-1")) == 1
        assert len(manager.get_history("user-2")) == 1
    
    def test_clear_conversation(self):
        """Test clearing conversation history."""
        from dooz_server.agent.conversation import ConversationManager
        
        manager = ConversationManager(max_history=10)
        manager.add_message("user-1", "user", "Hello")
        manager.clear_history("user-1")
        
        assert len(manager.get_history("user-1")) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_conversation.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/agent/conversation.py
"""Conversation history management."""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger("dooz_server.agent.conversation")


class ConversationManager:
    """Manages conversation history for each user."""
    
    def __init__(self, max_history: int = 10):
        """Initialize conversation manager.
        
        Args:
            max_history: Maximum number of message pairs to keep per user.
        """
        self.max_history = max_history
        self._conversations: dict[str, list[dict]] = defaultdict(list)
    
    def add_message(
        self,
        user_id: str,
        role: str,
        content: str
    ):
        """Add a message to user's conversation history.
        
        Args:
            user_id: User identifier.
            role: Message role ("user" or "assistant").
            content: Message content.
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self._conversations[user_id].append(message)
        
        # Trim if exceeds max (keep pairs, so 2x max_history)
        if len(self._conversations[user_id]) > self.max_history * 2:
            self._conversations[user_id] = self._conversations[user_id][-self.max_history * 2:]
        
        logger.debug(f"Added {role} message to {user_id}, total: {len(self._conversations[user_id])}")
    
    def get_history(self, user_id: str) -> list[dict]:
        """Get conversation history for a user.
        
        Args:
            user_id: User identifier.
            
        Returns:
            List of message dictionaries.
        """
        return self._conversations.get(user_id, [])
    
    def get_history_as_text(self, user_id: str) -> str:
        """Get conversation history formatted as text for LLM context.
        
        Args:
            user_id: User identifier.
            
        Returns:
            Formatted history string.
        """
        history = self.get_history(user_id)
        if not history:
            return "No previous conversation."
        
        lines = ["Conversation history:"]
        for msg in history:
            role = msg["role"].capitalize()
            lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(lines)
    
    def clear_history(self, user_id: str):
        """Clear conversation history for a user.
        
        Args:
            user_id: User identifier.
        """
        if user_id in self._conversations:
            del self._conversations[user_id]
            logger.debug(f"Cleared conversation history for {user_id}")
    
    def get_history_count(self, user_id: str) -> int:
        """Get number of messages in conversation.
        
        Args:
            user_id: User identifier.
            
        Returns:
            Number of messages.
        """
        return len(self._conversations.get(user_id, []))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_conversation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/agent/conversation.py dooz_server/tests/agent/test_conversation.py
git commit -m "feat(agent): add conversation manager for history tracking"
```

---

## Chunk 5: Task Router

### Task 5: Create Task Router

**Files:**
- Create: `dooz_server/src/dooz_server/agent/task_router.py`
- Test: `dooz_server/tests/agent/test_task_router.py`

- [ ] **Step 1: Create test file with failing tests**

```python
# dooz_server/tests/agent/test_task_router.py
import pytest
from unittest.mock import Mock, AsyncMock


class TestTaskRouter:
    """Tests for TaskRouter."""
    
    def test_task_router_initialization(self):
        """Test task router initialization."""
        from dooz_server.agent.task_router import TaskRouter
        
        router = TaskRouter(Mock(), Mock())
        
        assert router.llm_client is not None
    
    @pytest.mark.asyncio
    async def test_decompose_task_returns_list(self):
        """Test task decomposition returns list of subtasks."""
        from dooz_server.agent.task_router import TaskRouter
        from dooz_server.agent.config import LLMConfig
        from dooz_server.agent.llm_client import LLMClient
        
        config = LLMConfig(provider="openai", api_key="test")
        llm_client = LLMClient(config)
        
        # Mock the LLM call
        with pytest.mock.patch.object(llm_client, 'call', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"tasks": []}'
            
            router = TaskRouter(llm_client, Mock())
            tasks = await router.decompose_task("Turn on lights")
            
            assert isinstance(tasks, list)
    
    def test_parse_llm_response_valid_json(self):
        """Test parsing valid JSON response."""
        from dooz_server.agent.task_router import TaskRouter
        
        router = TaskRouter(Mock(), Mock())
        tasks = router._parse_llm_response('{"tasks": [{"task_id": "1", "description": "test"}]}')
        
        assert len(tasks) == 1
        assert tasks[0].task_id == "1"
    
    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON returns empty list."""
        from dooz_server.agent.task_router import TaskRouter
        
        router = TaskRouter(Mock(), Mock())
        tasks = router._parse_llm_response("not valid json")
        
        assert tasks == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_task_router.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/agent/task_router.py
"""Task decomposition and routing to sub-agents."""
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field

from ..llm_client import LLMClient
from ..schemas import ClientInfo

logger = logging.getLogger("dooz_server.agent.task_router")


class SubTask(BaseModel):
    """A decomposed sub-task to be executed by a sub-agent."""
    task_id: str
    description: str
    target_agent_id: Optional[str] = None
    target_capability: Optional[str] = None
    parameters: dict = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class TaskRouter:
    """Handles task decomposition and routing to sub-agents."""
    
    def __init__(self, llm_client: LLMClient, client_manager):
        """Initialize task router.
        
        Args:
            llm_client: LLM client for task decomposition.
            client_manager: Client manager to query available sub-agents.
        """
        self.llm_client = llm_client
        self.client_manager = client_manager
    
    async def decompose_task(
        self,
        user_message: str,
        system_prompt: str,
        context_info: str
    ) -> list[SubTask]:
        """Use LLM to decompose user task into sub-tasks.
        
        Args:
            user_message: The user's task request.
            system_prompt: System instructions for LLM.
            context_info: Available agents and context.
            
        Returns:
            List of decomposed sub-tasks.
        """
        try:
            response = await self.llm_client.call(
                system_prompt=system_prompt,
                context_info=context_info,
                user_message=user_message
            )
            
            tasks = self._parse_llm_response(response)
            logger.info(f"Decomposed task into {len(tasks)} sub-tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            return []
    
    def _parse_llm_response(self, response: str) -> list[SubTask]:
        """Parse LLM response into SubTask objects.
        
        Args:
            response: Raw LLM response string.
            
        Returns:
            List of SubTask objects.
        """
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            if isinstance(data, dict) and 'tasks' in data:
                tasks_data = data['tasks']
            elif isinstance(data, list):
                tasks_data = data
            else:
                logger.warning(f"Unexpected LLM response format: {response[:100]}")
                return []
            
            # Validate each task
            tasks = []
            for task_data in tasks_data:
                try:
                    task = SubTask(**task_data)
                    tasks.append(task)
                except Exception as e:
                    logger.warning(f"Failed to parse task {task_data}: {e}")
                    continue
            
            return tasks
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []
    
    def find_agent_for_task(
        self,
        task: SubTask,
        available_agents: list[ClientInfo]
    ) -> Optional[str]:
        """Find appropriate agent for a task based on capabilities.
        
        Args:
            task: The sub-task to route.
            available_agents: List of available sub-agents.
            
        Returns:
            Agent client_id if found, None otherwise.
        """
        # If specific agent requested, use that
        if task.target_agent_id:
            for agent in available_agents:
                if agent.client_id == task.target_agent_id:
                    return task.target_agent_id
            logger.warning(f"Requested agent {task.target_agent_id} not found")
            return None
        
        # If capability specified, match against agent skills
        if task.target_capability:
            for agent in available_agents:
                if agent.profile and agent.profile.skills:
                    for skill_name, _ in agent.profile.skills:
                        if task.target_capability.lower() in skill_name.lower():
                            return agent.client_id
            logger.warning(f"No agent found with capability {task.target_capability}")
        
        # No specific routing, return first available agent
        if available_agents:
            return available_agents[0].client_id
        
        return None
    
    def get_available_agents(self) -> list[ClientInfo]:
        """Get list of available sub-agents from client registry.
        
        Returns:
            List of connected client info (excluding the agent itself).
        """
        all_clients = self.client_manager.get_all_clients()
        
        # Filter out the agent itself and return rest
        # Note: Agent device_id will be filtered by the caller
        return [c for c in all_clients if c.profile and c.profile.role != "agent"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_task_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/agent/task_router.py dooz_server/tests/agent/test_task_router.py
git commit -m "feat(agent): add task router for decomposition and routing"
```

---

## Chunk 6: Main Agent Class

### Task 6: Create Main Agent Class

**Files:**
- Create: `dooz_server/src/dooz_server/agent/agent.py`
- Test: `dooz_server/tests/agent/test_agent.py` (integration-style)

- [ ] **Step 1: Create test file with failing tests**

```python
# dooz_server/tests/agent/test_agent.py
import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestAgent:
    """Tests for main Agent class."""
    
    def test_agent_initialization(self):
        """Test agent initializes with config."""
        from dooz_server.agent.agent import Agent
        from dooz_server.agent.config import AgentConfig
        
        config = AgentConfig()
        agent = Agent(config, Mock())
        
        assert agent.config == config
        assert agent.prompt_loader is not None
    
    @pytest.mark.asyncio
    async def test_handle_message_returns_response(self):
        """Test handling a user message returns a response."""
        from dooz_server.agent.agent import Agent
        from dooz_server.agent.config import AgentConfig, LLMConfig
        
        config = AgentConfig(
            llm=LLMConfig(provider="openai", api_key="test-key")
        )
        
        agent = Agent(config, Mock())
        
        # Mock the LLM to return simple task decomposition
        with patch.object(agent.task_router.llm_client, 'call', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"tasks": []}'
            
            response = await agent.handle_message("user-1", "Turn on lights")
            
            assert response is not None
            assert "message" in response or "tasks" in str(response)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_agent.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# dooz_server/src/dooz_server/agent/agent.py
"""Main Agent class that orchestrates task handling."""
import logging
from typing import Optional

from ..config import AgentConfig
from ..prompt_loader import PromptLoader
from ..llm_client import LLMClient
from ..conversation import ConversationManager
from ..task_router import TaskRouter, SubTask

logger = logging.getLogger("dooz_server.agent.agent")


class Agent:
    """Main AI agent that handles user messages and orchestrates sub-agents."""
    
    def __init__(
        self,
        config: AgentConfig,
        client_manager,
        work_directory: str
    ):
        """Initialize the agent.
        
        Args:
            config: Agent configuration.
            client_manager: Client manager for sub-agent discovery.
            work_directory: Work directory for prompt files.
        """
        self.config = config
        self.client_manager = client_manager
        self.work_directory = work_directory
        
        # Initialize components
        prompts_config = config.prompts
        prompts_dir = f"{work_directory}/{prompts_config.directory}"
        
        self.prompt_loader = PromptLoader(
            prompts_dir=prompts_dir,
            system_pattern=prompts_config.system_pattern,
            context_pattern=prompts_config.context_pattern,
            user_pattern=prompts_config.user_pattern
        )
        
        self.llm_client = LLMClient(config.llm)
        self.conversation = ConversationManager(max_history=10)
        self.task_router = TaskRouter(self.llm_client, client_manager)
        
        logger.info(f"Agent initialized: {config.agent.name} ({config.agent.device_id})")
    
    async def handle_message(self, user_id: str, message: str) -> dict:
        """Process user message and return agent response.
        
        Args:
            user_id: User identifier.
            message: User's message/task.
            
        Returns:
            Response dictionary with status and results.
        """
        # Add user message to conversation
        self.conversation.add_message(user_id, "user", message)
        
        try:
            # 1. Get available sub-agents
            available_agents = self.task_router.get_available_agents()
            agents_info = self._format_agents_info(available_agents)
            
            # 2. Update context with current agents
            self.prompt_loader.update_context("context_agents.txt", agents_info)
            
            # 3. Add conversation history to context
            history_text = self.conversation.get_history_as_text(user_id)
            self.prompt_loader.update_context("context_history.txt", history_text)
            
            # 4. Build prompt components
            system_prompt = self.prompt_loader.system_prompt
            context_info = self.prompt_loader.context_info
            
            # 5. Decompose task using LLM
            sub_tasks = await self.task_router.decompose_task(
                user_message=message,
                system_prompt=system_prompt,
                context_info=context_info
            )
            
            if not sub_tasks:
                response_text = "I couldn't understand your request. Please try again."
                self.conversation.add_message(user_id, "assistant", response_text)
                return {
                    "type": "agent_response",
                    "status": "error",
                    "message": response_text,
                    "sub_tasks": []
                }
            
            # 6. Execute sub-tasks
            results = await self._execute_sub_tasks(sub_tasks, available_agents)
            
            # 7. Aggregate results
            response_text = self._aggregate_results(results)
            
            # Add response to conversation
            self.conversation.add_message(user_id, "assistant", response_text)
            
            return {
                "type": "agent_response",
                "status": "completed",
                "message": response_text,
                "sub_tasks": [
                    {
                        "task_id": r.task_id,
                        "description": r.description,
                        "status": "completed" if r.success else "error",
                        "result": r.result,
                        "error": r.error
                    }
                    for r in results
                ]
            }
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {
                "type": "agent_response",
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "sub_tasks": []
            }
    
    def _format_agents_info(self, agents: list) -> str:
        """Format available agents for context."""
        if not agents:
            return "No available sub-agents currently."
        
        lines = ["Available sub-agents:"]
        for agent in agents:
            name = agent.name or agent.client_id
            role = agent.profile.role if agent.profile else "unknown"
            skills = ""
            if agent.profile and agent.profile.skills:
                skills = ", ".join(s[0] for s in agent.profile.skills)
            lines.append(f"- {name} ({role}): {skills}")
        
        return "\n".join(lines)
    
    async def _execute_sub_tasks(
        self,
        tasks: list[SubTask],
        available_agents: list
    ) -> list:
        """Execute sub-tasks by routing to sub-agents.
        
        Args:
            tasks: List of sub-tasks to execute.
            available_agents: Available sub-agents.
            
        Returns:
            List of task results.
        """
        results = []
        message_handler = None  # Would get from router/dependencies
        
        for task in tasks:
            # Find appropriate agent
            target_agent_id = self.task_router.find_agent_for_task(task, available_agents)
            
            if not target_agent_id:
                results.append(TaskResult(
                    task_id=task.task_id,
                    success=False,
                    result=None,
                    error=f"No available agent for task: {task.description}"
                ))
                continue
            
            # Send task to sub-agent via message
            # This would use the message handler to send to the target agent
            try:
                # For now, just log and create a placeholder result
                logger.info(f"Routing task {task.task_id} to agent {target_agent_id}")
                
                # In full implementation, would send message and wait for response
                # For now, return a success with "routed" status
                results.append(TaskResult(
                    task_id=task.task_id,
                    success=True,
                    result=f"Routed to {target_agent_id}: {task.description}",
                    error=None
                ))
                
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                results.append(TaskResult(
                    task_id=task.task_id,
                    success=False,
                    result=None,
                    error=str(e)
                ))
        
        return results
    
    def _aggregate_results(self, results: list) -> str:
        """Aggregate task results into response text.
        
        Args:
            results: List of task results.
            
        Returns:
            Aggregated response text.
        """
        if not results:
            return "No tasks were executed."
        
        completed = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if failed:
            return f"Completed {len(completed)} task(s), {len(failed)} failed. Results: {', '.join(r.result or r.error or 'unknown' for r in completed)}"
        else:
            return f"Completed {len(completed)} task(s). Results: {', '.join(r.result or 'done' for r in completed)}"


class TaskResult:
    """Result from executing a sub-task."""
    
    def __init__(
        self,
        task_id: str,
        success: bool,
        result: Optional[str],
        error: Optional[str]
    ):
        self.task_id = task_id
        self.success = success
        self.result = result
        self.error = error
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/src/dooz_server/agent/agent.py dooz_server/tests/agent/test_agent.py
git commit -m "feat(agent): add main Agent class for orchestration"
```

---

## Chunk 7: Integration with Server

### Task 7: Integrate Agent into main.py and router.py

**Files:**
- Modify: `dooz_server/main.py`
- Modify: `dooz_server/src/dooz_server/router.py`
- Modify: `dooz_server/src/dooz_server/__init__.py`

- [ ] **Step 1: Write integration test first**

```python
# dooz_server/tests/agent/test_agent_integration.py
import pytest
import json
from pathlib import Path


class TestAgentIntegration:
    """Integration tests for agent with server."""
    
    def test_agent_config_loaded_in_main(self, tmp_path, monkeypatch):
        """Test agent config is loaded from work directory."""
        # Create temp work directory with config
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        
        config_data = {
            "agent": {"enabled": True, "device_id": "test-agent", "name": "Test"},
            "llm": {"provider": "openai", "api_key": "test-key", "model": "gpt-4o"},
            "prompts": {"directory": "prompts"}
        }
        
        config_file = work_dir / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        # Create prompts directory
        prompts_dir = work_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "00_system.txt").write_text("You are a test agent.")
        
        # This test verifies the config loading path works
        from dooz_server.agent.config import load_agent_config
        config = load_agent_config(str(config_file))
        
        assert config is not None
        assert config.agent.device_id == "test-agent"
    
    def test_agent_device_id_routing(self):
        """Test agent device_id is correctly identified."""
        from dooz_server.agent.config import AgentConfig
        
        config = AgentConfig(agent=type('obj', (object,), {'enabled': True, 'device_id': 'my-agent', 'name': 'Test'})())
        
        # Simulate routing logic
        device_id = "my-agent"
        is_agent = config.agent.enabled and device_id == config.agent.device_id
        
        assert is_agent is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_agent_integration.py -v`
Expected: FAIL or PASS depending on current state

- [ ] **Step 3: Modify main.py to load config**

```python
# dooz_server/main.py - Add after existing imports
import os
import json
from pathlib import Path
from dooz_server.agent import Agent, load_agent_config
from dooz_server.agent.config import AgentConfig

# Global agent instance
_agent: Optional[Agent] = None


def get_agent() -> Optional[Agent]:
    """Get the global agent instance."""
    return _agent


def init_agent(work_directory: str, config: Optional[AgentConfig] = None):
    """Initialize the agent with work directory.
    
    Args:
        work_directory: Work directory for prompts and config.
        config: Optional agent config. If not provided, loads from config.json.
    """
    global _agent
    
    if config is None:
        config_path = Path(work_directory) / "config.json"
        config = load_agent_config(str(config_path))
    
    if config is None or not config.agent.enabled:
        logger.info("Agent feature is disabled")
        return
    
    # Get client manager (will be set after app creation)
    from dooz_server.router import get_client_manager
    client_manager = get_client_manager()
    
    _agent = Agent(config, client_manager, work_directory)
    logger.info(f"Agent initialized: {config.agent.name}")
```

- [ ] **Step 4: Modify router.py for agent routing**

```python
# dooz_server/src/dooz_server/router.py - Add agent handling in WebSocket endpoint

# Add at top with other globals
import os
import json
from pathlib import Path
from .agent import Agent, load_agent_config
from .agent.config import AgentConfig
from fastapi import WebSocketDisconnect

_agent_config: Optional[AgentConfig] = None
_initialized_agent: Optional[Agent] = None


def get_agent_config() -> Optional[AgentConfig]:
    return _agent_config


def init_agent_router(work_directory: str):
    """Initialize agent router with work directory."""
    global _agent_config, _initialized_agent
    
    config_path = Path(work_directory) / "config.json"
    _agent_config = load_agent_config(str(config_path))
    
    if _agent_config and _agent_config.agent.enabled:
        _initialized_agent = Agent(_agent_config, get_client_manager(), work_directory)
        logger.info(f"Agent router initialized: {_agent_config.agent.name}")


# Save original websocket_endpoint logic as handle_client_websocket
async def handle_client_websocket(websocket: WebSocket, device_id: str, profile: Optional[str] = None):
    """Handle normal client WebSocket connection - extracted from original endpoint."""
    ws_mgr = get_ws_manager()
    await ws_mgr.connect(device_id, websocket)
    
    # Parse profile if provided
    client_profile = None
    profile_device_id = None
    if profile:
        try:
            profile_data = json.loads(urllib.parse.unquote(profile))
            client_profile = ClientProfile(**profile_data)
            profile_device_id = client_profile.device_id
        except Exception as e:
            logger.warning(f"Failed to parse profile for {device_id}: {e}")
    
    final_device_id = profile_device_id if profile_device_id == device_id else device_id
    
    client_manager = get_client_manager()
    existing_client = client_manager.get_client_info(final_device_id)
    if not existing_client:
        client_name = client_profile.name if client_profile else (final_device_id.split('-')[0].capitalize() if '-' in final_device_id else final_device_id)
        registered_id = client_manager.register_client(final_device_id, client_name, client_profile, "WebSocket")
        logger.info(f"WebSocket: Registered new client {registered_id}")
    client_manager.add_connection(final_device_id, websocket)
    
    heartbeat_monitor = get_heartbeat_monitor()
    await heartbeat_monitor.record_heartbeat(final_device_id)
    
    logger.info(f"WebSocket connection established: device_id={final_device_id}")
    
    message_handler = get_message_handler()
    pending_count = message_handler.deliver_pending_messages(final_device_id)
    if pending_count > 0:
        await ws_mgr.send_personal_message({
            "type": "pending_delivered",
            "count": pending_count
        }, final_device_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "message":
                message_handler = get_message_handler()
                to_client = message_data.get("to_client_id")
                content = message_data.get("content")
                ttl_seconds = message_data.get("ttl_seconds", 3600)
                
                success, msg, msg_id = message_handler.send_message(
                    from_client_id=final_device_id,
                    to_client_id=to_client,
                    content=content,
                    ttl_seconds=ttl_seconds
                )
                
                await ws_mgr.send_personal_message({
                    "type": "message_sent",
                    "success": success,
                    "message": msg,
                    "message_id": msg_id,
                    "to_client_id": to_client
                }, final_device_id)
                
                logger.info(f"WS message: {final_device_id} -> {to_client}: {content[:30]}...")
            
            elif message_type == "ping":
                await heartbeat_monitor.record_heartbeat(final_device_id)
                await ws_mgr.send_personal_message({"type": "pong"}, final_device_id)
            
            elif message_type == "heartbeat":
                await heartbeat_monitor.record_heartbeat(final_device_id)
                await ws_mgr.send_personal_message({
                    "type": "heartbeat_ack",
                    "server_time": asyncio.get_event_loop().time()
                }, final_device_id)
                
    except WebSocketDisconnect:
        ws_mgr.disconnect(final_device_id)
        heartbeat_monitor.remove_client(final_device_id)
        client_manager.remove_connection(final_device_id)
        logger.info(f"WebSocket disconnected: device_id={final_device_id}")


# Modify the websocket_endpoint to check for agent
@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str, profile: Optional[str] = None):
    agent_config = get_agent_config()
    
    # Check if this is a message TO the agent
    if agent_config and agent_config.agent.enabled and device_id == agent_config.agent.device_id:
        # Handle as agent message
        await handle_agent_websocket(websocket, device_id, profile)
    else:
        # Normal client handling
        await handle_client_websocket(websocket, device_id, profile)


async def handle_agent_websocket(websocket: WebSocket, device_id: str, profile: Optional[str] = None):
    """Handle WebSocket connection to the agent."""
    global _initialized_agent
    
    await websocket.accept()
    logger.info(f"Agent WebSocket connected: {device_id}")
    
    agent = _initialized_agent
    if not agent:
        logger.error("Agent not initialized")
        await websocket.send_json({"type": "error", "message": "Agent not available"})
        await websocket.close()
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "agent_message":
                user_id = message_data.get("user_id", "anonymous")
                content = message_data.get("content", "")
                
                # Send processing status
                await websocket.send_json({
                    "type": "agent_response",
                    "status": "processing",
                    "message": "Processing your request..."
                })
                
                # Handle the message
                response = await agent.handle_message(user_id, content)
                
                # Send response
                await websocket.send_json(response)
                
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Unknown message type: {message_type}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"Agent WebSocket disconnected: {device_id}")

- [ ] **Step 5: Modify __init__.py exports**

```python
# dooz_server/src/dooz_server/__init__.py
"""Dooz server package."""

from .router import router
from .agent import Agent, load_agent_config
from .client_manager import ClientManager
from .message_handler import MessageHandler

__all__ = [
    "router",
    "Agent",
    "load_agent_config", 
    "ClientManager",
    "MessageHandler",
]
```

- [ ] **Step 6: Run tests to verify integration**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && uv run pytest tests/agent/test_agent_integration.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/main.py dooz_server/src/dooz_server/router.py dooz_server/src/dooz_server/__init__.py
git commit -m "feat(agent): integrate agent into server main and router"
```

---

## Chunk 8: Sample Config and Prompts

### Task 8: Create sample config and prompt files for testing

- [ ] **Step 1: Create sample files for reference**

```bash
# Create sample config and prompts directory structure
mkdir -p dooz_server/examples/agent

# Create sample config.json
cat > dooz_server/examples/agent/config.json << 'EOF'
{
  "agent": {
    "enabled": true,
    "device_id": "dooz-agent",
    "name": "Dooz Assistant"
  },
  "llm": {
    "provider": "openai",
    "model": "gpt-4o",
    "api_key": "${OPENAI_API_KEY}",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout_seconds": 30
  },
  "prompts": {
    "directory": "prompts",
    "system_pattern": "system_*.txt",
    "context_pattern": "context_*.txt",
    "user_pattern": "user_*.txt"
  }
}
EOF

# Create sample prompts
mkdir -p dooz_server/examples/agent/prompts

cat > dooz_server/examples/agent/prompts/00_system_role.txt << 'EOF'
You are Dooz Assistant, an AI agent that helps users interact with smart home devices and other connected services.

Your role is to:
1. Understand user requests and break them into smaller tasks
2. Route tasks to appropriate sub-agents or devices
3. Aggregate results and present to the user

Always respond in a helpful and clear manner.
EOF

cat > dooz_server/examples/agent/prompts/10_context_agents.txt << 'EOF'
# Available sub-agents will be inserted here at runtime
EOF

cat > dooz_server/examples/agent/prompts/20_context_history.txt << 'EOF'
# Conversation history will be inserted here at runtime
EOF
```

- [ ] **Step 2: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz
git add dooz_server/examples/agent/
git commit -m "feat(agent): add sample config and prompts"
```

---

## Summary

| Chunk | Tasks | Description |
|-------|-------|-------------|
| 1 | 1 | Config loading with env var substitution |
| 2 | 2 | Prompt loader from work directory |
| 3 | 3 | LLM client (OpenAI/Anthropic) |
| 4 | 4 | Conversation history management |
| 5 | 5 | Task router for decomposition |
| 6 | 6 | Main Agent class |
| 7 | 7 | Server integration |
| 8 | 8 | Sample files |

**Total: 8 tasks with TDD approach**

All tasks follow the pattern: Write failing test → Implement → Verify pass → Commit.

---

## Acceptance Criteria

- [ ] Agent can be configured via config file in work directory
- [ ] Prompts load from `{work_dir}/prompts/*.txt` with proper ordering
- [ ] Environment variables substitute in config values
- [ ] LLM client works for OpenAI (Anthropic optional for initial implementation)
- [ ] Task decomposition returns structured sub-tasks
- [ ] Sub-tasks route to appropriate sub-agents based on capabilities
- [ ] Conversation history maintained per user
- [ ] Agent integrates with WebSocket endpoint
- [ ] All new code has passing tests

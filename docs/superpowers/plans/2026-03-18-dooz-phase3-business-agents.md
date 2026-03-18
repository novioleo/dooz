# Phase 3: Business Agents (YAML Loading) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement YAML-based agent definition loading and agent process spawning. Allow custom sub-agents to be defined in YAML and loaded by the daemon at startup.

**Architecture:** 
- YAML schemas for Agent and Dooz definitions
- Loaders that parse and validate YAML files
- AgentProcessSpawner that creates sub-agent processes
- Integration with existing MQTT client for agent communication
- Sample definitions in `dooz_daemon/definitions/` directory

**Tech Stack:** Python, PyYAML, Pydantic, asyncio, subprocess

---

## Chunk 1: YAML Schemas

### Task 1.1: Define Pydantic Models for Agent and Dooz Schemas

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/schemas/agent.py`
- Create: `dooz_daemon/src/dooz_daemon/schemas/__init__.py`
- Test: `dooz_daemon/tests/test_agent_schema.py`

- [ ] **Step 1: Write failing test for AgentDefinition**

```python
# tests/test_agent_schema.py
import pytest
from pydantic import ValidationError
from dooz_daemon.schemas.agent import AgentDefinition, AgentMqttConfig, Skill


def test_agent_definition_valid():
    """Test valid agent definition."""
    agent = AgentDefinition(
        agent_id="light-agent",
        name="灯光控制",
        description="控制家中灯光",
        role="sub-agent",
        capabilities=["light_on", "light_off"],
        mqtt=AgentMqttConfig(
            topic="light-control",
            subscribe=["tasks/light-agent"],
        ),
    )
    assert agent.agent_id == "light-agent"
    assert agent.role == "sub-agent"
    assert "light_on" in agent.capabilities


def test_agent_definition_defaults():
    """Test default values."""
    agent = AgentDefinition(
        agent_id="test-agent",
        name="测试",
        mqtt=AgentMqttConfig(topic="test"),
    )
    assert agent.role == "sub-agent"
    assert agent.capabilities == []
    assert agent.skills == []


def test_agent_mqtt_config():
    """Test MQTT config."""
    mqtt = AgentMqttConfig(
        topic="light",
        subscribe=["tasks/light"],
        publish=["results/light"],
    )
    assert mqtt.topic == "light"
    assert "tasks/light" in mqtt.subscribe
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_agent_schema.py -v`
Expected: FAIL - ModuleNotFoundError: No module named 'dooz_daemon.schemas'

- [ ] **Step 3: Create schemas package with AgentDefinition**

```python
# dooz_daemon/src/dooz_daemon/schemas/__init__.py
"""Schemas for YAML definitions."""

from .agent import AgentDefinition, AgentMqttConfig, Skill
from .dooz import DoozDefinition, DoozMqttConfig

__all__ = [
    "AgentDefinition",
    "AgentMqttConfig", 
    "Skill",
    "DoozDefinition",
    "DoozMqttConfig",
]
```

```python
# dooz_daemon/src/dooz_daemon/schemas/agent.py
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
```

- [ ] **Step 4: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_agent_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/schemas/ dooz_daemon/tests/test_agent_schema.py
git commit -m "feat: add agent definition schemas"
```

---

### Task 1.2: Define Pydantic Models for Dooz Schema

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/schemas/dooz.py`
- Test: `dooz_daemon/tests/test_dooz_schema.py`

- [ ] **Step 1: Write failing test for DoozDefinition**

```python
# tests/test_dooz_schema.py
import pytest
from pydantic import ValidationError
from dooz_daemon.schemas.dooz import DoozDefinition, DoozMqttConfig


def test_dooz_definition_valid():
    """Test valid dooz definition."""
    dooz = DoozDefinition(
        dooz_id="dooz_1_1",
        name="智能家居",
        description="控制家中智能设备",
        role="dooz-group",
        agents=["light-agent", "speaker-agent"],
        nested_dooz=["dooz_2_1"],
        mqtt=DoozMqttConfig(topic_prefix="dooz/dooz_1_1"),
    )
    assert dooz.dooz_id == "dooz_1_1"
    assert dooz.role == "dooz-group"
    assert "light-agent" in dooz.agents
    assert "dooz_2_1" in dooz.nested_dooz


def test_dooz_id_format():
    """Test dooz_id format validation."""
    with pytest.raises(ValidationError):
        DoozDefinition(
            dooz_id="invalid",
            name="测试",
            mqtt=DoozMqttConfig(),
        )


def test_dooz_defaults():
    """Test default values."""
    dooz = DoozDefinition(
        dooz_id="dooz_1_1",
        name="测试",
        mqtt=DoozMqttConfig(),
    )
    assert dooz.role == "dooz"
    assert dooz.agents == []
    assert dooz.nested_dooz == []
    assert dooz.capabilities == []
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_dooz_schema.py -v`
Expected: FAIL - No module named 'dooz_daemon.schemas.dooz'

- [ ] **Step 3: Create DoozDefinition schema**

```python
# dooz_daemon/src/dooz_daemon/schemas/dooz.py
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
```

- [ ] **Step 4: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_dooz_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/schemas/dooz.py dooz_daemon/tests/test_dooz_schema.py
git commit -m "feat: add dooz definition schemas"
```

---

## Chunk 2: YAML Loaders

### Task 2.1: Agent YAML Loader

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/loader/agent_loader.py`
- Create: `dooz_daemon/src/dooz_daemon/loader/__init__.py`
- Test: `dooz_daemon/tests/test_agent_loader.py`

- [ ] **Step 1: Write failing test for AgentLoader**

```python
# tests/test_agent_loader.py
import pytest
import tempfile
import os
from pathlib import Path
from dooz_daemon.loader.agent_loader import AgentLoader


def test_load_agent_from_yaml(tmp_path):
    """Test loading agent definition from YAML file."""
    yaml_content = """
agent:
  agent_id: "light-agent"
  name: "灯光控制"
  description: "控制家中灯光"
  role: "sub-agent"
  capabilities:
    - light_on
    - light_off
  mqtt:
    topic: "light-control"
    subscribe:
      - "tasks/light-agent"
"""
    # Write YAML file
    agent_file = tmp_path / "light-agent.yaml"
    agent_file.write_text(yaml_content)
    
    # Load
    loader = AgentLoader(tmp_path)
    agents = loader.load_all()
    
    assert len(agents) == 1
    assert agents[0].agent_id == "light-agent"
    assert "light_on" in agents[0].capabilities


def test_load_multiple_agents(tmp_path):
    """Test loading multiple agent files."""
    # Write two YAML files
    (tmp_path / "light-agent.yaml").write_text("""
agent:
  agent_id: "light-agent"
  name: "灯光"
  mqtt:
    topic: "light"
    subscribe: ["tasks/light"]
""")
    (tmp_path / "speaker-agent.yaml").write_text("""
agent:
  agent_id: "speaker-agent"
  name: "音箱"
  mqtt:
    topic: "speaker"
    subscribe: ["tasks/speaker"]
""")
    
    loader = AgentLoader(tmp_path)
    agents = loader.load_all()
    
    assert len(agents) == 2
    agent_ids = {a.agent_id for a in agents}
    assert "light-agent" in agent_ids
    assert "speaker-agent" in agent_ids


def test_load_invalid_yaml(tmp_path):
    """Test handling invalid YAML."""
    (tmp_path / "invalid.yaml").write_text("invalid: yaml: content:")
    
    loader = AgentLoader(tmp_path)
    agents = loader.load_all()
    
    # Should skip invalid files
    assert len(agents) == 0
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_agent_loader.py -v`
Expected: FAIL - ModuleNotFoundError: No module named 'dooz_daemon.loader'

- [ ] **Step 3: Create AgentLoader**

```python
# dooz_daemon/src/dooz_daemon/loader/__init__.py
"""YAML loaders for agent and dooz definitions."""

from .agent_loader import AgentLoader
from .dooz_loader import DoozLoader

__all__ = ["AgentLoader", "DoozLoader"]
```

```python
# dooz_daemon/src/dooz_daemon/loader/agent_loader.py
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
```

- [ ] **Step 4: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_agent_loader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/loader/agent_loader.py dooz_daemon/tests/test_agent_loader.py
git commit -m "feat: add agent YAML loader"
```

---

### Task 2.2: Dooz YAML Loader

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/loader/dooz_loader.py`
- Test: `dooz_daemon/tests/test_dooz_loader.py`

- [ ] **Step 1: Write failing test for DoozLoader**

```python
# tests/test_dooz_loader.py
import pytest
import tempfile
from pathlib import Path
from dooz_daemon.loader.dooz_loader import DoozLoader


def test_load_dooz_from_yaml(tmp_path):
    """Test loading dooz definition from YAML file."""
    yaml_content = """
dooz:
  dooz_id: "dooz_1_1"
  name: "智能家居"
  description: "控制家中智能设备"
  role: "dooz-group"
  agents:
    - light-agent
    - speaker-agent
  nested_dooz:
    - dooz_2_1
  mqtt:
    topic_prefix: "dooz/dooz_1_1"
"""
    dooz_file = tmp_path / "dooz_1_1.yaml"
    dooz_file.write_text(yaml_content)
    
    loader = DoozLoader(tmp_path)
    dooz_list = loader.load_all()
    
    assert len(dooz_list) == 1
    assert dooz_list[0].dooz_id == "dooz_1_1"
    assert dooz_list[0].role == "dooz-group"


def test_load_top_level_dooz_only(tmp_path):
    """Test that loader only loads top-level dooz."""
    # Create nested dooz file
    (tmp_path / "dooz_2_1.yaml").write_text("""
dooz:
  dooz_id: "dooz_2_1"
  name: "嵌套Dooz"
  mqtt:
    topic_prefix: "dooz/dooz_2_1"
""")
    
    loader = DoozLoader(tmp_path)
    dooz_list = loader.load_all()
    
    # Should only load files that start with dooz_
    assert len(dooz_list) == 1
    assert dooz_list[0].dooz_id == "dooz_2_1"
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_dooz_loader.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: Create DoozLoader**

```python
# dooz_daemon/src/dooz_daemon/loader/dooz_loader.py
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
```

- [ ] **Step 4: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_dooz_loader.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/loader/dooz_loader.py dooz_daemon/tests/test_dooz_loader.py
git commit -m "feat: add dooz YAML loader"
```

---

## Chunk 3: Agent Process Spawner

### Task 3.1: Agent Process Spawner

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/agent_manager.py`
- Test: `dooz_daemon/tests/test_agent_manager.py`

- [ ] **Step 1: Write failing test for AgentProcessSpawner**

```python
# tests/test_agent_manager.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from dooz_daemon.agent_manager import AgentProcess, AgentProcessManager


def test_agent_process_creation():
    """Test creating an AgentProcess."""
    process = AgentProcess(
        agent_id="light-agent",
        name="灯光控制",
        dooz_id="dooz_1_1",
        mqtt_topic="dooz/dooz_1_1/agents/light-control",
    )
    assert process.agent_id == "light-agent"
    assert process.dooz_id == "dooz_1_1"


def test_agent_process_manager_init():
    """Test initializing AgentProcessManager."""
    manager = AgentProcessManager(
        dooz_id="dooz_1_1",
        definitions_dir=Path("/tmp/defs"),
    )
    assert manager.dooz_id == "dooz_1_1"
    assert len(manager.processes) == 0


@pytest.mark.asyncio
async def test_spawn_agent_process():
    """Test spawning an agent process."""
    manager = AgentProcessManager(
        dooz_id="dooz_1_1",
        definitions_dir=Path("/tmp/defs"),
    )
    
    # Mock subprocess.Popen
    with patch("subprocess.Popen") as mock_popen:
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        process = await manager.spawn_agent(
            agent_id="light-agent",
            name="灯光",
            mqtt_topic="light",
        )
        
        assert process is not None
        mock_popen.assert_called_once()
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_agent_manager.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: Create AgentProcess and AgentProcessManager**

```python
# dooz_daemon/src/dooz_daemon/agent_manager.py
"""Agent process management."""

import asyncio
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dooz_daemon.schemas.agent import AgentDefinition

logger = logging.getLogger("dooz_daemon.agent_manager")


@dataclass
class AgentProcess:
    """Represents a running agent process."""
    agent_id: str
    name: str
    dooz_id: str
    mqtt_topic: str
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None


class AgentProcessManager:
    """Manages agent processes for a single Dooz."""
    
    def __init__(
        self,
        dooz_id: str,
        definitions_dir: Path | str | None = None,
    ):
        self.dooz_id = dooz_id
        self.definitions_dir = Path(definitions_dir) if definitions_dir else None
        self.processes: dict[str, AgentProcess] = {}
        self._running = False
    
    async def spawn_agent(
        self,
        agent_id: str,
        name: str,
        mqtt_topic: str,
        config: Optional[dict] = None,
    ) -> AgentProcess:
        """Spawn a new agent process."""
        if agent_id in self.processes:
            logger.warning(f"Agent {agent_id} already running")
            return self.processes[agent_id]
        
        # Build MQTT topic
        full_topic = f"dooz/{self.dooz_id}/agents/{mqtt_topic}"
        
        # Create agent process
        agent_process = AgentProcess(
            agent_id=agent_id,
            name=name,
            dooz_id=self.dooz_id,
            mqtt_topic=full_topic,
        )
        
        # TODO: Actually spawn the process
        # For now, just track it in memory
        self.processes[agent_id] = agent_process
        logger.info(f"Spawned agent: {agent_id} ({name})")
        
        return agent_process
    
    async def spawn_agents_from_definitions(
        self,
        agents: list[AgentDefinition],
    ) -> list[AgentProcess]:
        """Spawn agent processes from agent definitions."""
        spawned = []
        
        for agent_def in agents:
            if agent_def.role != "sub-agent":
                logger.info(f"Skipping system agent: {agent_def.agent_id}")
                continue
            
            process = await self.spawn_agent(
                agent_id=agent_def.agent_id,
                name=agent_def.name,
                mqtt_topic=agent_def.mqtt.topic,
                config=agent_def.config,
            )
            spawned.append(process)
        
        return spawned
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a running agent process."""
        if agent_id not in self.processes:
            logger.warning(f"Agent {agent_id} not found")
            return False
        
        agent = self.processes[agent_id]
        
        if agent.process:
            agent.process.terminate()
            try:
                agent.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                agent.process.kill()
        
        del self.processes[agent_id]
        logger.info(f"Stopped agent: {agent_id}")
        
        return True
    
    async def stop_all(self):
        """Stop all agent processes."""
        agent_ids = list(self.processes.keys())
        
        for agent_id in agent_ids:
            await self.stop_agent(agent_id)
        
        logger.info(f"Stopped all agents for dooz: {self.dooz_id}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentProcess]:
        """Get an agent process by ID."""
        return self.processes.get(agent_id)
    
    def get_all_agents(self) -> list[AgentProcess]:
        """Get all agent processes."""
        return list(self.processes.values())
```

- [ ] **Step 4: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_agent_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/agent_manager.py dooz_daemon/tests/test_agent_manager.py
git commit -m "feat: add agent process manager"
```

---

## Chunk 4: Sample Definitions & Integration

### Task 4.1: Create Sample Agent Definitions

**Files:**
- Create: `dooz_daemon/definitions/agents/light-agent.yaml`
- Create: `dooz_daemon/definitions/agents/speaker-agent.yaml`
- Create: `dooz_daemon/definitions/agents/sensor-agent.yaml`

- [ ] **Step 1: Create sample light-agent definition**

```yaml
# definitions/agents/light-agent.yaml
agent:
  agent_id: "light-agent"
  name: "灯光控制"
  description: "控制家中灯光开关和亮度"
  role: "sub-agent"
  capabilities:
    - light_on
    - light_off
    - light_brightness
  skills:
    - name: "light_control"
      description: "控制灯光开关和亮度"
  mqtt:
    topic: "light-control"
    subscribe:
      - "tasks/light-agent"
    publish:
      - "results/light-agent"
  config:
    device_type: "smart_light"
    brand: "xiaomi"
```

- [ ] **Step 2: Create sample speaker-agent definition**

```yaml
# definitions/agents/speaker-agent.yaml
agent:
  agent_id: "speaker-agent"
  name: "音箱控制"
  description: "控制家中音箱播放音乐"
  role: "sub-agent"
  capabilities:
    - play_music
    - pause_music
    - set_volume
  skills:
    - name: "audio_control"
      description: "控制音箱播放"
  mqtt:
    topic: "speaker-control"
    subscribe:
      - "tasks/speaker-agent"
    publish:
      - "results/speaker-agent"
  config:
    device_type: "smart_speaker"
    brand: "xiaomi"
```

- [ ] **Step 3: Create sample sensor-agent definition**

```yaml
# definitions/agents/sensor-agent.yaml
agent:
  agent_id: "sensor-agent"
  name: "传感器"
  description: "读取家中传感器数据"
  role: "sub-agent"
  capabilities:
    - get_temperature
    - get_humidity
    - get_motion
  skills:
    - name: "sensor_reading"
      description: "读取传感器数据"
  mqtt:
    topic: "sensor-reading"
    subscribe:
      - "tasks/sensor-agent"
    publish:
      - "results/sensor-agent"
  config:
    device_type: "sensor_hub"
```

- [ ] **Step 4: Commit**

```bash
git add dooz_daemon/definitions/agents/
git commit -m "feat: add sample agent definitions"
```

---

### Task 4.2: Create Sample Dooz Definitions

**Files:**
- Create: `dooz_daemon/definitions/dooz/dooz_1_1.yaml`
- Create: `dooz_daemon/definitions/dooz/dooz_2_1.yaml`

- [ ] **Step 1: Create top-level dooz definition**

```yaml
# definitions/dooz/dooz_1_1.yaml
dooz:
  dooz_id: "dooz_1_1"
  name: "智能家居"
  description: "控制家中智能设备"
  role: "dooz-group"
  agents:
    - light-agent
    - speaker-agent
  nested_dooz:
    - dooz_2_1
  capabilities:
    - smart_home_control
  mqtt:
    topic_prefix: "dooz/dooz_1_1"
  config:
    auto_discover: true
```

- [ ] **Step 2: Create nested dooz definition**

```yaml
# definitions/dooz/dooz_2_1.yaml
dooz:
  dooz_id: "dooz_2_1"
  name: "安全监控"
  description: "家庭安全监控系统"
  role: "dooz"
  agents:
    - sensor-agent
  nested_dooz: []
  capabilities:
    - security_monitoring
  mqtt:
    topic_prefix: "dooz/dooz_2_1"
  config:
    alert_enabled: true
```

- [ ] **Step 3: Commit**

```bash
git add dooz_daemon/definitions/dooz/
git commit -m "feat: add sample dooz definitions"
```

---

### Task 4.3: Integrate Loaders into Daemon

**Files:**
- Modify: `dooz_daemon/src/dooz_daemon/daemon.py`
- Modify: `dooz_daemon/src/dooz_daemon/config.py`

- [ ] **Step 1: Update config to include definitions directory**

```python
# Add to config.py
class DaemonConfig(BaseModel):
    # ... existing fields ...
    definitions_dir: Path = Field(
        default=Path("./definitions"),
        description="Directory containing dooz and agent definitions"
    )
```

- [ ] **Step 2: Update daemon to load definitions on startup**

```python
# In daemon.py, add to DoozDaemon class:
from .loader import AgentLoader, DoozLoader
from .agent_manager import AgentProcessManager

class DoozDaemon:
    def __init__(self, config: DaemonConfig):
        # ... existing init ...
        self._dooz_loaders: dict[str, DoozLoader] = {}
        self._agent_loaders: dict[str, AgentLoader] = {}
        self._agent_managers: dict[str, AgentProcessManager] = {}
    
    async def _load_definitions(self):
        """Load dooz and agent definitions."""
        definitions_dir = self.config.definitions_dir
        
        # Load dooz definitions
        dooz_dir = definitions_dir / "dooz"
        if dooz_dir.exists():
            dooz_loader = DoozLoader(dooz_dir)
            dooz_list = dooz_loader.load_all()
            
            for dooz_def in dooz_list:
                # Create agent loader for this dooz
                agent_dir = definitions_dir / "agents"
                agent_loader = AgentLoader(agent_dir)
                
                self._dooz_loaders[dooz_def.dooz_id] = dooz_loader
                self._agent_loaders[dooz_def.dooz_id] = agent_loader
                
                # Create agent manager
                manager = AgentProcessManager(
                    dooz_id=dooz_def.dooz_id,
                    definitions_dir=agent_dir,
                )
                self._agent_managers[dooz_def.dooz_id] = manager
                
                logger.info(f"Loaded dooz: {dooz_def.dooz_id}")
        
        logger.info(f"Loaded {len(self._agent_managers)} dooz instances")
```

- [ ] **Step 3: Update daemon start to call _load_definitions**

```python
# In daemon.py, update start method:
async def start(self):
    logger.info("Starting dooz daemon...")
    
    # Load definitions first
    await self._load_definitions()
    
    # ... rest of start method
```

- [ ] **Step 4: Run tests**

Run: `cd dooz_daemon && uv run pytest tests/ -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/daemon.py dooz_daemon/src/dooz_daemon/config.py
git commit -m "feat: integrate YAML loaders into daemon"
```

---

## Summary

After completing Phase 3, you will have:
- [x] Pydantic schemas for Agent and Dooz definitions
- [x] YAML loaders for agents and dooz
- [x] Agent process manager
- [x] Sample YAML definitions
- [x] Integration with daemon startup

**Next Phase:** Implement Clarification Agent for CLI (Phase 4).

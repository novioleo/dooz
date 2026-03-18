"""Tests for agent loader."""

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

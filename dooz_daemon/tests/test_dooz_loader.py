"""Tests for dooz loader."""

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

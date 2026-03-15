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

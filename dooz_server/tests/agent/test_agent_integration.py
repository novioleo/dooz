import pytest
import json
from pathlib import Path


class TestAgentIntegration:
    """Integration tests for agent with server."""
    
    def test_agent_config_loaded(self, tmp_path):
        """Test agent config loading."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        
        config_data = {
            "agent": {"enabled": True, "device_id": "test-agent", "name": "Test"},
            "llm": {"provider": "openai", "api_key": "test-key", "model": "gpt-4o"},
            "prompts": {"directory": "prompts"}
        }
        
        config_file = work_dir / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        prompts_dir = work_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "00_system.txt").write_text("You are a test agent.")
        
        from dooz_server.agent.config import load_agent_config
        config = load_agent_config(str(config_file))
        
        assert config is not None
        assert config.agent.device_id == "test-agent"
    
    def test_agent_device_id_routing(self):
        """Test agent device_id routing logic."""
        from dooz_server.agent.config import AgentConfig, AgentSettings
        
        settings = AgentSettings(enabled=True, device_id="my-agent", name="Test")
        config = AgentConfig(agent=settings)
        
        assert config.agent.enabled is True
        assert config.agent.device_id == "my-agent"

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch


class TestAgent:
    """Tests for main Agent class."""
    
    def test_agent_initialization(self):
        """Test agent initializes with config."""
        from dooz_server.agent.agent import Agent
        from dooz_server.agent.config import AgentConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            (prompts_dir / "00_system.txt").write_text("You are a test agent.")
            
            config = AgentConfig()
            agent = Agent(config, Mock(), tmpdir)
            
            assert agent.config == config
            assert agent.prompt_loader is not None
    
    @pytest.mark.asyncio
    async def test_handle_message_returns_response(self):
        """Test handling a user message returns a response."""
        from dooz_server.agent.agent import Agent
        from dooz_server.agent.config import AgentConfig, LLMConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            (prompts_dir / "00_system.txt").write_text("You are a test agent.")
            
            config = AgentConfig(
                llm=LLMConfig(provider="openai", api_key="test-key")
            )
            
            agent = Agent(config, Mock(), tmpdir)
            
            with patch.object(agent.task_router.llm_client, 'call', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = '{"tasks": []}'
                
                response = await agent.handle_message("user-1", "Turn on lights")
                
                assert response is not None
                assert "message" in response or "tasks" in str(response)

import pytest
import sys
from unittest.mock import Mock, AsyncMock, patch


class TestLLMClient:
    """Tests for LLMClient."""
    
    def test_openai_client_initialization(self):
        """Test OpenAI client initialization."""
        from dooz_server.agent.llm_client import LLMClient
        from dooz_server.agent.config import LLMConfig
        
        with patch.dict(sys.modules, {'openai': Mock(AsyncOpenAI=AsyncMock())}):
            config = LLMConfig(provider="openai", model="gpt-4o", api_key="test-key")
            client = LLMClient(config)
        
        assert client.provider == "openai"
        assert client.model == "gpt-4o"
    
    @pytest.mark.asyncio
    async def test_call_openai(self):
        """Test calling OpenAI API."""
        from dooz_server.agent.llm_client import LLMClient
        from dooz_server.agent.config import LLMConfig
        
        mock_openai_module = Mock()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=Mock(
                choices=[Mock(message=Mock(content='{"tasks": []}'))]
            )
        )
        mock_openai_module.AsyncOpenAI = Mock(return_value=mock_client)
        
        with patch.dict(sys.modules, {'openai': mock_openai_module}):
            config = LLMConfig(provider="openai", model="gpt-4o", api_key="test-key")
            client = LLMClient(config)
            response = await client.call("system", "context", "user message")
        
        assert "tasks" in response
    
    def test_unsupported_provider_raises(self):
        """Test unsupported provider raises error."""
        from dooz_server.agent.llm_client import LLMClient
        from dooz_server.agent.config import LLMConfig
        
        config = LLMConfig(provider="unknown", api_key="test")
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient(config)

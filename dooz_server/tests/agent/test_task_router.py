import pytest
from unittest.mock import Mock, AsyncMock, patch


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
        with patch.object(llm_client, 'call', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"tasks": []}'
            
            router = TaskRouter(llm_client, Mock())
            tasks = await router.decompose_task("Turn on lights", "system prompt", "context info")
            
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

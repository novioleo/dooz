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

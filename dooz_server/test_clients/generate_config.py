#!/usr/bin/env python3
"""
Config generator for dooz_server agent.
Creates config.json and prompts directory in the specified work directory.
"""

import argparse
import json
import os
from pathlib import Path


DEFAULT_CONFIG = {
    "agent": {
        "enabled": True,
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

DEFAULT_SYSTEM_PROMPT = """You are Dooz Assistant, an AI agent that helps users interact with smart home devices and other connected services.

Your role is to:
1. Understand user requests and break them into smaller tasks
2. Route tasks to appropriate sub-agents or devices
3. Aggregate results and present to the user

Always respond in a helpful and clear manner.
"""


def create_config(work_dir: str, config: dict = None):
    """Create config.json in the work directory."""
    config_path = Path(work_dir) / "config.json"
    
    if config_path.exists():
        print(f"Warning: {config_path} already exists. Use --force to overwrite.")
        return False
    
    config = config or DEFAULT_CONFIG
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Created config.json at {config_path}")
    return True


def create_prompts(work_dir: str, force: bool = False):
    """Create prompts directory with default files."""
    prompts_dir = Path(work_dir) / "prompts"
    
    if prompts_dir.exists() and not force:
        print(f"Warning: {prompts_dir} already exists. Use --force to overwrite.")
        return False
    
    prompts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create system prompt
    system_file = prompts_dir / "00_system_role.txt"
    if not system_file.exists() or force:
        with open(system_file, "w") as f:
            f.write(DEFAULT_SYSTEM_PROMPT)
        print(f"Created {system_file}")
    
    # Create context placeholder files
    context_files = [
        ("10_context_agents.txt", "# Available sub-agents will be inserted here at runtime\n"),
        ("20_context_history.txt", "# Conversation history will be inserted here at runtime\n"),
    ]
    
    for filename, content in context_files:
        filepath = prompts_dir / filename
        if not filepath.exists() or force:
            with open(filepath, "w") as f:
                f.write(content)
            print(f"Created {filepath}")
    
    return True


def setup_work_directory(
    work_dir: str,
    agent_name: str = None,
    agent_device_id: str = None,
    llm_provider: str = None,
    llm_model: str = None,
    llm_api_key: str = None,
    force: bool = False
):
    """Setup complete work directory with config and prompts."""
    work_path = Path(work_dir)
    
    # Create work directory if not exists
    work_path.mkdir(parents=True, exist_ok=True)
    print(f"Work directory: {work_path.absolute()}")
    
    # Build config
    config = DEFAULT_CONFIG.copy()
    
    if agent_name:
        config["agent"]["name"] = agent_name
    if agent_device_id:
        config["agent"]["device_id"] = agent_device_id
    
    # Handle LLM settings
    if llm_provider:
        config["llm"]["provider"] = llm_provider
        # Set default API key env var based on provider if not providing explicit key
        if not llm_api_key:
            config["llm"]["api_key"] = "${ANTHROPIC_API_KEY}" if llm_provider == "anthropic" else "${OPENAI_API_KEY}"
    if llm_model:
        config["llm"]["model"] = llm_model
    if llm_api_key:
        config["llm"]["api_key"] = llm_api_key
    
    # Create config
    config_path = work_path / "config.json"
    if config_path.exists() and not force:
        print(f"\nWarning: {config_path} already exists. Skipping config creation.")
    else:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Created config.json")
    
    # Create prompts
    create_prompts(str(work_path), force=force)
    
    print(f"\n✅ Setup complete!")
    print(f"\nTo start the server:")
    print(f"  DOOZ_WORK_DIRECTORY={work_path.absolute()} uvicorn dooz_server.main:app --reload --port 8000")
    print(f"\nOr use the dooz-server script:")
    print(f"  DOOZ_WORK_DIRECTORY={work_path.absolute()} dooz-server")


def main():
    parser = argparse.ArgumentParser(
        description="Generate dooz_server agent config and prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup with default config in ./my-workdir
  python generate_config.py ./my-workdir

  # Setup with custom agent name
  python generate_config.py ./my-workdir --agent-name "My Assistant"

  # Setup with custom LLM provider
  python generate_config.py ./my-workdir --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022

  # Force overwrite existing files
  python generate_config.py ./my-workdir --force
        """,
    )
    
    parser.add_argument(
        "work_dir",
        help="Work directory path to create config in",
    )
    
    parser.add_argument(
        "--agent-name",
        default=None,
        help="Agent name (default: Dooz Assistant)",
    )
    
    parser.add_argument(
        "--agent-device-id",
        default=None,
        help="Agent device ID (default: dooz-agent)",
    )
    
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "anthropic"],
        default=None,
        help="LLM provider (default: openai)",
    )
    
    parser.add_argument(
        "--llm-model",
        default=None,
        help="LLM model (default: gpt-4o for openai, claude-3-5-sonnet-20241022 for anthropic)",
    )
    
    parser.add_argument(
        "--llm-api-key",
        default=None,
        help="LLM API key (use ${ENV_VAR} for env var reference)",
    )
    
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force overwrite existing files",
    )
    
    args = parser.parse_args()
    
    setup_work_directory(
        work_dir=args.work_dir,
        agent_name=args.agent_name,
        agent_device_id=args.agent_device_id,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        llm_api_key=args.llm_api_key,
        force=args.force,
    )


if __name__ == "__main__":
    main()

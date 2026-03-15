"""
Main CLI entry point for dooz-server.
Provides commands to start the server and initialize work directories.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Configure logging at the root level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.INFO)

logger = logging.getLogger("dooz_server")

DEFAULT_WORK_DIRECTORY = os.environ.get("DOOZ_WORK_DIRECTORY", os.getcwd())


def create_app(work_directory: str = None) -> "FastAPI":
    """Create and configure the FastAPI application."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from dooz_server.router import router, init_agent_router
    
    work_dir = work_directory or DEFAULT_WORK_DIRECTORY
    
    app = FastAPI(
        title="Dooz WebSocket Server",
        description="WebSocket message relay server for client-to-client communication",
        version="0.1.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router)
    
    init_agent_router(work_dir)
    
    return app


# Default configuration
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


def cmd_init(args):
    """Initialize a work directory with config and prompts."""
    work_dir = args.work_dir
    work_path = Path(work_dir)
    
    # Create work directory if not exists
    work_path.mkdir(parents=True, exist_ok=True)
    print(f"Work directory: {work_path.absolute()}")
    
    # Build config based on arguments
    config = DEFAULT_CONFIG.copy()
    
    if args.agent_name:
        config["agent"]["name"] = args.agent_name
    if args.agent_device_id:
        config["agent"]["device_id"] = args.agent_device_id
    
    # Handle LLM settings
    if args.llm_provider:
        config["llm"]["provider"] = args.llm_provider
        if not args.llm_api_key:
            config["llm"]["api_key"] = "${ANTHROPIC_API_KEY}" if args.llm_provider == "anthropic" else "${OPENAI_API_KEY}"
    if args.llm_model:
        config["llm"]["model"] = args.llm_model
    if args.llm_api_key:
        config["llm"]["api_key"] = args.llm_api_key
    
    # Create config.json
    config_path = work_path / "config.json"
    if config_path.exists() and not args.force:
        print(f"Warning: {config_path} already exists. Use --force to overwrite.")
    else:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Created config.json")
    
    # Create prompts directory
    prompts_dir = work_path / "prompts"
    if prompts_dir.exists() and not args.force:
        print(f"Warning: {prompts_dir} already exists. Skipping prompts.")
    else:
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create system prompt
        system_file = prompts_dir / "00_system_role.txt"
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
            with open(filepath, "w") as f:
                f.write(content)
            print(f"Created {filepath}")
    
    print(f"\n✅ Initialization complete!")
    print(f"\nTo start the server:")
    print(f"  dooz-server start --work-dir {work_path.absolute()}")
    print(f"\nOr set environment variable:")
    print(f"  DOOZ_WORK_DIRECTORY={work_path.absolute()} dooz-server start")


def cmd_start(args):
    """Start the dooz-server."""
    import uvicorn
    
    # Set work directory from args or environment
    work_dir = args.work_dir or os.environ.get("DOOZ_WORK_DIRECTORY", os.getcwd())
    os.environ["DOOZ_WORK_DIRECTORY"] = work_dir
    
    # Create app with work directory
    app = create_app(work_dir)
    
    print(f"Starting dooz-server...")
    print(f"  Work directory: {work_dir}")
    print(f"  Host: {args.host}:{args.port}")
    
    # Check for agent config
    config_path = Path(work_dir) / "config.json"
    if config_path.exists():
        from dooz_server.agent import load_agent_config
        agent_config = load_agent_config(str(config_path))
        if agent_config and agent_config.agent.enabled:
            print(f"  Agent: {agent_config.agent.name} ({agent_config.agent.device_id})")
        else:
            print(f"  Agent: disabled")
    else:
        print(f"  Config: not found (run 'dooz-server init' first)")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dooz Server - WebSocket message relay server with AI agent support",
        prog="dooz-server",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a work directory with config and prompts",
    )
    init_parser.add_argument(
        "work_dir",
        help="Work directory path to initialize",
    )
    init_parser.add_argument(
        "--agent-name",
        help="Agent name (default: Dooz Assistant)",
    )
    init_parser.add_argument(
        "--agent-device-id",
        help="Agent device ID (default: dooz-agent)",
    )
    init_parser.add_argument(
        "--llm-provider",
        choices=["openai", "anthropic"],
        help="LLM provider (default: openai)",
    )
    init_parser.add_argument(
        "--llm-model",
        help="LLM model name",
    )
    init_parser.add_argument(
        "--llm-api-key",
        help="LLM API key (or use ${ENV_VAR} format)",
    )
    init_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force overwrite existing files",
    )
    init_parser.set_defaults(func=cmd_init)
    
    # Start command
    start_parser = subparsers.add_parser(
        "start",
        help="Start the dooz-server",
    )
    start_parser.add_argument(
        "--work-dir", "-w",
        help="Work directory path (default: $DOOZ_WORK_DIRECTORY or current directory)",
    )
    start_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)",
    )
    start_parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Server port (default: 8000)",
    )
    start_parser.add_argument(
        "--reload", "-r",
        action="store_true",
        help="Enable auto-reload",
    )
    start_parser.set_defaults(func=cmd_start)
    
    args = parser.parse_args()
    
    if args.command is None:
        # Default to start command if no subcommand provided
        args.command = "start"
        args.func = cmd_start
        # Set defaults for start command
        args.work_dir = os.environ.get("DOOZ_WORK_DIRECTORY", os.getcwd())
        args.host = "0.0.0.0"
        args.port = 8000
        args.reload = False
    
    args.func(args)


if __name__ == "__main__":
    main()

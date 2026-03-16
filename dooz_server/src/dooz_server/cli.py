"""
Main CLI entry point for dooz-server.
Provides commands to start the server and initialize work directories.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click

# Configure logging at the root level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.INFO)

from contextlib import asynccontextmanager

logger = logging.getLogger("dooz_server")

if TYPE_CHECKING:
    from fastapi import FastAPI

DEFAULT_WORK_DIRECTORY = os.environ.get("DOOZ_WORK_DIRECTORY", os.getcwd())


@asynccontextmanager
async def lifespan(app: "FastAPI"):
    """Lifespan context for server startup/shutdown."""
    from dooz_server.router import get_client_manager
    client_mgr = get_client_manager()
    
    # Pre-register system agents so they can be discovered
    client_mgr.register_client("dooz-agent", "Dooz Assistant", role="dooz")
    client_mgr.register_client("task-scheduler", "Task Scheduler", role="system")
    
    logger.info("System agents registered: dooz-agent, task-scheduler")
    yield
    logger.info("Server shutting down")


def create_app(work_directory: str = None) -> "FastAPI":
    """Create and configure the FastAPI application."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from dooz_server.router import router, init_agent_router
    
    work_dir = work_directory or DEFAULT_WORK_DIRECTORY
    
    app = FastAPI(
        title="Dooz WebSocket Server",
        description="WebSocket message relay server for client-to-client communication",
        version="0.1.0",
        lifespan=lifespan
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


@click.group()
def cli():
    """Dooz Server - WebSocket message relay server with AI agent support."""
    pass


@cli.command()
@click.argument("work_dir", default=".", type=click.Path())
@click.option("--llm-provider", type=click.Choice(["openai", "anthropic", "openai-compatible"]), help="LLM provider (default: openai)")
@click.option("--llm-model", help="LLM model name")
@click.option("--llm-api-key", help="LLM API key (or use ${ENV_VAR} format)")
@click.option("--llm-base-url", help="Base URL for openai-compatible providers")
@click.option("--force", "-f", is_flag=True, help="Force overwrite existing files")
def init(work_dir, llm_provider, llm_model, llm_api_key, llm_base_url, force):
    """Initialize a work directory with config and prompts."""
    work_path = Path(work_dir)
    
    # Create work directory if not exists
    work_path.mkdir(parents=True, exist_ok=True)
    click.echo(f"Work directory: {work_path.absolute()}")
    
    # Build config based on arguments
    config = DEFAULT_CONFIG.copy()
    
    # Handle LLM settings
    if llm_provider:
        config["llm"]["provider"] = llm_provider
        if not llm_api_key:
            if llm_provider == "anthropic":
                config["llm"]["api_key"] = "${ANTHROPIC_API_KEY}"
            elif llm_provider == "openai":
                config["llm"]["api_key"] = "${OPENAI_API_KEY}"
            else:
                config["llm"]["api_key"] = "${OPENAI_API_KEY}"
    if llm_model:
        config["llm"]["model"] = llm_model
    if llm_api_key:
        config["llm"]["api_key"] = llm_api_key
    if llm_base_url:
        config["llm"]["base_url"] = llm_base_url
    
    # Create config.json
    config_path = work_path / "config.json"
    if config_path.exists() and not force:
        click.echo(f"Warning: {config_path} already exists. Use --force to overwrite.")
    else:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        click.echo(f"Created config.json")
    
    # Create prompts directory
    prompts_dir = work_path / "prompts"
    if prompts_dir.exists() and not force:
        click.echo(f"Warning: {prompts_dir} already exists. Skipping prompts.")
    else:
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create system prompt
        system_file = prompts_dir / "00_system_role.txt"
        with open(system_file, "w") as f:
            f.write(DEFAULT_SYSTEM_PROMPT)
        click.echo(f"Created {system_file}")
        
        # Create context placeholder files
        context_files = [
            ("10_context_agents.txt", "# Available sub-agents will be inserted here at runtime\n"),
            ("20_context_history.txt", "# Conversation history will be inserted here at runtime\n"),
        ]
        
        for filename, content in context_files:
            filepath = prompts_dir / filename
            with open(filepath, "w") as f:
                f.write(content)
            click.echo(f"Created {filepath}")
    
    click.echo(f"\n✅ Initialization complete!")
    click.echo(f"\nTo start the server:")
    click.echo(f"  dooz-server start --work-dir {work_path.absolute()}")
    click.echo(f"\nOr set environment variable:")
    click.echo(f"  DOOZ_WORK_DIRECTORY={work_path.absolute()} dooz-server start")


@cli.command()
@click.option("--work-dir", "-w", help="Work directory path (default: $DOOZ_WORK_DIRECTORY or current directory)")
@click.option("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
@click.option("--port", "-p", type=int, default=8000, help="Server port (default: 8000)")
@click.option("--reload", "-r", is_flag=True, help="Enable auto-reload")
def start(work_dir, host, port, reload):
    """Start the dooz-server."""
    import uvicorn
    
    # Set work directory from args or environment
    work_dir = work_dir or os.environ.get("DOOZ_WORK_DIRECTORY", os.getcwd())
    os.environ["DOOZ_WORK_DIRECTORY"] = work_dir
    
    # Create app with work directory
    app = create_app(work_dir)
    
    click.echo(f"Starting dooz-server...")
    click.echo(f"  Work directory: {work_dir}")
    click.echo(f"  Host: {host}:{port}")
    
    # Check for agent config
    config_path = Path(work_dir) / "config.json"
    if config_path.exists():
        from dooz_server.agent import load_agent_config
        agent_config = load_agent_config(str(config_path))
        if agent_config and agent_config.agent.enabled:
            click.echo(f"  Agent: {agent_config.agent.name} ({agent_config.agent.device_id})")
        else:
            click.echo(f"  Agent: disabled")
    else:
        click.echo(f"  Config: not found (run 'dooz-server init' first)")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
    )


def main():
    """Main CLI entry point."""
    # Default to start command if no subcommand provided
    if len(sys.argv) == 1:
        sys.argv.append("start")
    cli()


if __name__ == "__main__":
    main()

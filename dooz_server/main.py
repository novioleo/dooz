"""Main entry point for the WebSocket message server."""
import logging
import os
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dooz_server.router import router, init_agent_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.INFO)

logger = logging.getLogger("dooz_server")

WORK_DIRECTORY = os.environ.get("DOOZ_WORK_DIRECTORY", os.getcwd())


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
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
    
    init_agent_router(WORK_DIRECTORY)
    
    return app


app = create_app()


def main():
    """Run the server using uvicorn."""
    import uvicorn
    
    logger.info(f"Starting Dooz server with work directory: {WORK_DIRECTORY}")
    
    config_path = Path(WORK_DIRECTORY) / "config.json"
    if config_path.exists():
        from dooz_server.agent import load_agent_config
        agent_config = load_agent_config(str(config_path))
        if agent_config and agent_config.agent.enabled:
            logger.info(f"Agent enabled: {agent_config.agent.name} ({agent_config.agent.device_id})")
        else:
            logger.info("Agent feature disabled in config")
    else:
        logger.info(f"No config.json found in {WORK_DIRECTORY}, agent disabled")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

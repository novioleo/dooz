# dooz_server/main.py
"""Main entry point for the WebSocket message server."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dooz_server.router import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Dooz WebSocket Server",
        description="WebSocket message relay server for client-to-client communication",
        version="0.1.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(router)
    
    return app


app = create_app()


def main():
    """Run the server using uvicorn."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

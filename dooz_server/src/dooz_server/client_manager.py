# dooz_server/src/dooz_server/client_manager.py
import uuid
from datetime import datetime
from typing import Optional, Any
from .schemas import ClientInfo


class ClientManager:
    """Manages connected client registry and WebSocket connections."""
    
    def __init__(self):
        self._clients: dict[str, ClientInfo] = {}
        self._connections: dict[str, Any] = {}  # client_id -> websocket
    
    def register_client(self, name: str, connection_type: str = "WebSocket") -> str:
        """Register a new client and return their client_id."""
        client_id = str(uuid.uuid4())
        client_info = ClientInfo(
            client_id=client_id,
            name=name,
            connected_at=datetime.utcnow().isoformat() + "Z"
        )
        self._clients[client_id] = client_info
        return client_id
    
    def unregister_client(self, client_id: str) -> bool:
        """Unregister a client by ID. Returns True if client was removed."""
        if client_id in self._clients:
            del self._clients[client_id]
            if client_id in self._connections:
                del self._connections[client_id]
            return True
        return False
    
    def get_client_info(self, client_id: str) -> Optional[ClientInfo]:
        """Get client information by ID."""
        return self._clients.get(client_id)
    
    def get_all_clients(self) -> list[ClientInfo]:
        """Get list of all connected clients."""
        return list(self._clients.values())
    
    def add_connection(self, client_id: str, websocket: Any) -> bool:
        """Associate a WebSocket connection with a client."""
        if client_id in self._clients:
            self._connections[client_id] = websocket
            return True
        return False
    
    def get_connection(self, client_id: str) -> Optional[Any]:
        """Get WebSocket connection for a client."""
        return self._connections.get(client_id)
    
    def is_connected(self, client_id: str) -> bool:
        """Check if a client is connected."""
        return client_id in self._clients and client_id in self._connections

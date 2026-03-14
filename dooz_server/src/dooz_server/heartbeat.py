# dooz_server/src/dooz_server/heartbeat.py
import asyncio
import time
from typing import Dict, Optional, Callable, Awaitable


class HeartbeatMonitor:
    """Monitors client heartbeats and detects timeouts."""
    
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self._heartbeats: Dict[str, float] = {}  # client_id -> last heartbeat timestamp
    
    async def record_heartbeat(self, client_id: str) -> None:
        """Record a heartbeat from a client."""
        self._heartbeats[client_id] = time.time()
    
    def is_alive(self, client_id: str) -> bool:
        """Check if a client is still alive (within timeout)."""
        if client_id not in self._heartbeats:
            return False
        
        last_heartbeat = self._heartbeats[client_id]
        elapsed = time.time() - last_heartbeat
        return elapsed < self.timeout_seconds
    
    def remove_client(self, client_id: str) -> None:
        """Remove a client from heartbeat tracking."""
        if client_id in self._heartbeats:
            del self._heartbeats[client_id]
    
    def get_last_heartbeat(self, client_id: str) -> Optional[float]:
        """Get the last heartbeat timestamp for a client."""
        return self._heartbeats.get(client_id)
    
    async def cleanup_dead_clients(self) -> list[str]:
        """Remove dead clients and return their IDs."""
        dead_clients = []
        for client_id in list(self._heartbeats.keys()):
            if not self.is_alive(client_id):
                self.remove_client(client_id)
                dead_clients.append(client_id)
        return dead_clients
    
    async def start_monitor_loop(self, callback: Optional[Callable[[str], Awaitable[None]]] = None) -> None:
        """Start the background monitoring loop."""
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            dead = await self.cleanup_dead_clients()
            if callback and dead:
                for client_id in dead:
                    await callback(client_id)

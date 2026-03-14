# dooz_server/src/dooz_server/heartbeat.py
import asyncio
import time
import logging
from typing import Dict, Optional, Callable, Awaitable

logger = logging.getLogger("dooz_server.heartbeat")


class HeartbeatMonitor:
    """Monitors client heartbeats and detects timeouts."""
    
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self._heartbeats: Dict[str, float] = {}  # client_id -> last heartbeat timestamp
        logger.info(f"HeartbeatMonitor initialized with timeout={timeout_seconds}s")
    
    async def record_heartbeat(self, client_id: str) -> None:
        """Record a heartbeat from a client."""
        self._heartbeats[client_id] = time.time()
        logger.debug(f"Heartbeat received from: {client_id}")
    
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
            logger.info(f"Client removed from heartbeat tracking: {client_id}")
    
    def get_last_heartbeat(self, client_id: str) -> Optional[float]:
        """Get the last heartbeat timestamp for a client."""
        return self._heartbeats.get(client_id)
    
    async def cleanup_dead_clients(self) -> list[str]:
        """Remove dead clients and return their IDs."""
        dead_clients = []
        for client_id in list(self._heartbeats.keys()):
            if not self.is_alive(client_id):
                last_beat = self._heartbeats.get(client_id, 0)
                elapsed = time.time() - last_beat
                self.remove_client(client_id)
                dead_clients.append(client_id)
                logger.warning(f"Client heartbeat timeout: {client_id} (no heartbeat for {elapsed:.1f}s)")
        return dead_clients
    
    async def start_monitor_loop(self, callback: Optional[Callable[[str], Awaitable[None]]] = None) -> None:
        """Start the background monitoring loop."""
        logger.info("Heartbeat monitor loop started")
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            dead = await self.cleanup_dead_clients()
            if callback and dead:
                for client_id in dead:
                    await callback(client_id)

# tests/test_heartbeat.py
import pytest
import asyncio
import time
from dooz_server.heartbeat import HeartbeatMonitor


@pytest.mark.asyncio
async def test_heartbeat_monitor_creation():
    monitor = HeartbeatMonitor()
    assert monitor is not None


@pytest.mark.asyncio
async def test_record_heartbeat():
    monitor = HeartbeatMonitor()
    await monitor.record_heartbeat("client-123")
    assert monitor.is_alive("client-123")


@pytest.mark.asyncio
async def test_client_timeout():
    monitor = HeartbeatMonitor(timeout_seconds=1)
    await monitor.record_heartbeat("client-123")
    await asyncio.sleep(1.5)
    assert not monitor.is_alive("client-123")


@pytest.mark.asyncio
async def test_remove_client():
    monitor = HeartbeatMonitor()
    await monitor.record_heartbeat("client-123")
    monitor.remove_client("client-123")
    assert not monitor.is_alive("client-123")


@pytest.mark.asyncio
async def test_get_last_heartbeat():
    monitor = HeartbeatMonitor()
    before = time.time()
    await monitor.record_heartbeat("client-123")
    after = time.time()
    
    last = monitor.get_last_heartbeat("client-123")
    assert last is not None
    assert before <= last <= after


@pytest.mark.asyncio
async def test_cleanup_dead_clients():
    monitor = HeartbeatMonitor(timeout_seconds=1)
    await monitor.record_heartbeat("client-1")
    await monitor.record_heartbeat("client-2")
    
    await asyncio.sleep(1.5)
    
    dead = await monitor.cleanup_dead_clients()
    assert len(dead) == 2
    assert "client-1" in dead
    assert "client-2" in dead

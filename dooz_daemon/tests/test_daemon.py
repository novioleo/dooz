import pytest
from dooz_daemon.config import DaemonConfig
from dooz_daemon.daemon import DoozDaemon


@pytest.mark.asyncio
async def test_daemon_initialization():
    config = DaemonConfig()
    daemon = DoozDaemon(config)
    assert daemon.config == config
    assert not daemon._running

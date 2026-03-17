"""Daemon CLI entry point."""

import asyncio
import logging
import signal

from . import DoozDaemon, DaemonConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    """Main entry point."""
    config = DaemonConfig()
    daemon = DoozDaemon(config)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        print(f"\nReceived signal {sig}, shutting down...")
        loop.create_task(daemon.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        loop.run_until_complete(daemon.start())
    except Exception as e:
        logging.error(f"Daemon error: {e}")
    finally:
        loop.close()


if __name__ == "__main__":
    main()

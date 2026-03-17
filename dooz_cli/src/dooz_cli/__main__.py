"""CLI entry point."""

import asyncio
import argparse

from . import DoozCLI


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Dooz CLI")
    parser.add_argument(
        "--uri",
        default="ws://localhost:8765",
        help="Daemon WebSocket URI",
    )
    parser.add_argument(
        "--dooz-id",
        default=None,
        help="Target dooz ID",
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send (if not interactive)",
    )
    
    args = parser.parse_args()
    
    cli = DoozCLI(args.uri)
    
    async def run():
        if args.message:
            # Single message mode
            if not await cli.connect():
                print("Failed to connect to daemon")
                return
            await cli.send_message(args.message, args.dooz_id)
            await asyncio.sleep(1)  # Wait for response
            await cli.disconnect()
        else:
            print("Interactive mode not implemented in this phase")
    
    asyncio.run(run())


if __name__ == "__main__":
    main()

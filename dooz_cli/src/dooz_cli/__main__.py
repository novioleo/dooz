"""CLI entry point."""

import asyncio
import argparse
import sys

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
        "--tui",
        action="store_true",
        help="Launch TUI interface (default for interactive mode)",
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send (if not interactive)",
    )
    
    args = parser.parse_args()
    
    if args.tui or (not args.message):
        # Launch TUI mode
        from dooz_cli.tui.websocket_tui import WebSocketTUI
        
        app = WebSocketTUI(uri=args.uri)
        app.run()
    else:
        # Single message mode (legacy)
        cli = DoozCLI(args.uri)
        
        async def run():
            if not await cli.connect():
                print("Failed to connect to daemon")
                sys.exit(1)
            await cli.send_message(args.message, args.dooz_id)
            await asyncio.sleep(1)  # Wait for response
            await cli.disconnect()
        
        asyncio.run(run())


if __name__ == "__main__":
    main()

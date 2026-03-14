# dooz_server/test_clients/client_bob.py
"""Bob - Test client 2."""
import asyncio
from .client_base import WebSocketClient


class BobClient(WebSocketClient):
    """Bob client with auto-response capability."""
    
    async def handle_message(self, message: dict):
        """Handle messages and auto-reply."""
        msg_type = message.get("type")
        
        if msg_type == "message":
            content = message.get("content", "")
            from_id = message.get("from_client_id")
            print(f"\n[Bob] Message from {from_id}: {content}")
            
            # Auto-reply
            await asyncio.sleep(0.5)
            await self.send({
                "type": "message",
                "to_client_id": from_id,
                "content": f"Bob received: {content}"
            })
            print(f"[Bob] Auto-replied to {from_id}")
        elif msg_type == "message_expired":
            print(f"\n[Bob] My message expired! Content: {message.get('content')}")
        else:
            await super().handle_message(message)


async def run_bob():
    """Run Bob client."""
    client = BobClient(
        client_id="bob-001",
        name="Bob"
    )
    try:
        await client.connect()
        
        # Start listening and heartbeat
        listen_task = asyncio.create_task(client.listen())
        heartbeat_task = asyncio.create_task(client.send_heartbeat())
        
        # Wait for commands
        print("\n[Bob] Running... Press Ctrl+C to exit")
        await asyncio.Future()  # Run forever
        
    except asyncio.CancelledError:
        pass
    finally:
        client.running = False
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_bob())

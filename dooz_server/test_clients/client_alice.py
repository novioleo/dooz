# dooz_server/test_clients/client_alice.py
"""Alice - Test client 1."""
import asyncio
import httpx
from .client_base import WebSocketClient


class AliceClient(WebSocketClient):
    """Alice client with interactive commands."""
    
    def __init__(self):
        super().__init__(
            client_id="alice-001",
            name="Alice"
        )
    
    async def handle_message(self, message: dict):
        """Handle messages with Alice-specific behavior."""
        msg_type = message.get("type")
        
        if msg_type == "message":
            print(f"\n[Alice] New message from {message.get('from_client_id')}: {message.get('content')}")
        elif msg_type == "message_expired":
            print(f"\n[Alice] My message expired! Content: {message.get('content')}")
        else:
            await super().handle_message(message)
    
    async def interactive_loop(self):
        """Interactive command loop."""
        print("\n=== Alice's Commands ===")
        print("msg <client_id> <content> - Send message")
        print("list - List all clients")
        print("quit - Exit")
        print("========================\n")
        
        while self.running:
            try:
                cmd = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("Alice> ").strip()
                )
                
                if not cmd:
                    continue
                
                if cmd == "quit":
                    break
                elif cmd == "list":
                    # Use HTTP to list clients
                    async with httpx.AsyncClient() as client:
                        resp = await client.get("http://localhost:8000/clients")
                        data = resp.json()
                        print(f"\nConnected clients ({data['total']}):")
                        for c in data['clients']:
                            print(f"  - {c['client_id']}: {c['name']}")
                elif cmd.startswith("msg "):
                    parts = cmd.split(" ", 2)
                    if len(parts) == 3:
                        _, to_client, content = parts
                        await self.send({
                            "type": "message",
                            "to_client_id": to_client,
                            "content": content,
                            "ttl_seconds": 3600
                        })
                        print(f"[Alice] Sent message to {to_client}")
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")


async def run_alice():
    """Run Alice client."""
    client = AliceClient()
    try:
        await client.connect()
        
        # Start listening and heartbeat in background
        listen_task = asyncio.create_task(client.listen())
        heartbeat_task = asyncio.create_task(client.send_heartbeat())
        
        # Run interactive loop
        await client.interactive_loop()
        
        # Cleanup
        client.running = False
        await asyncio.gather(listen_task, heartbeat_task, return_exceptions=True)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_alice())

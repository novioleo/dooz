# dooz_server/test_clients/client_charlie.py
"""Charlie - Test client 3."""
import asyncio
from .client_base import WebSocketClient


class CharlieClient(WebSocketClient):
    """Charlie client - simulates offline/online behavior."""
    
    def __init__(self):
        super().__init__(
            client_id="charlie-001",
            name="Charlie"
        )
        self.was_online = False
    
    async def handle_message(self, message: dict):
        """Handle messages with offline simulation."""
        msg_type = message.get("type")
        
        if msg_type == "message":
            print(f"\n[Charlie] NEW MESSAGE from {message.get('from_client_id')}: {message.get('content')}")
            if message.get("is_offline"):
                print("  (This was delivered from offline queue)")
        elif msg_type == "pending_delivered":
            print(f"\n[Charlie] Reconnected! Delivered {message.get('count')} pending messages")
            self.was_online = True
        elif msg_type == "message_expired":
            print(f"\n[Charlie] My message expired!")
        else:
            await super().handle_message(message)
    
    async def simulate_offline(self, duration: int = 10):
        """Simulate going offline for a duration."""
        print(f"\n[Charlie] Going offline for {duration} seconds...")
        self.running = False
        if self.websocket:
            await self.websocket.close()
        
        await asyncio.sleep(duration)
        
        print("[Charlie] Coming back online...")
        await self.connect()
        self.running = True


async def run_charlie():
    """Run Charlie client with offline simulation."""
    client = CharlieClient()
    try:
        await client.connect()
        
        listen_task = asyncio.create_task(client.listen())
        heartbeat_task = asyncio.create_task(client.send_heartbeat())
        
        print("\n[Charlie] Running... Type 'offline' to simulate going offline")
        print("[Charlie] Type 'msg <id> <msg>' to send messages")
        
        async def input_loop():
            while client.running:
                try:
                    cmd = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: input("Charlie> ").strip()
                    )
                    
                    if cmd == "offline":
                        await client.simulate_offline(10)
                        # Restart tasks after coming back online
                        listen_task = asyncio.create_task(client.listen())
                        heartbeat_task = asyncio.create_task(client.send_heartbeat())
                    elif cmd.startswith("msg "):
                        parts = cmd.split(" ", 2)
                        if len(parts) == 3:
                            await client.send({
                                "type": "message",
                                "to_client_id": parts[1],
                                "content": parts[2]
                            })
                except:
                    break
        
        await input_loop()
        
    finally:
        client.running = False
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_charlie())

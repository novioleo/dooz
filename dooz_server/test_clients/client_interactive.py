# dooz_server/test_clients/client_interactive.py
"""
Interactive test client for WebSocket message server.
Provides a command-line interface for sending/receiving messages.
"""
import asyncio
import argparse
import websockets
import json
import os
from pathlib import Path
from typing import Optional


def load_profile_from_file(profile_path: str) -> Optional[dict]:
    """Load profile JSON from file."""
    path = Path(profile_path)
    if not path.exists():
        print(f"Error: Profile file not found: {profile_path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in profile file: {e}")
        return None
    except Exception as e:
        print(f"Error reading profile file: {e}")
        return None


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Interactive WebSocket client for dooz server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect with profile from file
  python client_interactive.py --profile-file profile.json

  # Connect with inline profile JSON
  python client_interactive.py --profile-json '{"device_id":"device-001","name":"Agent1","role":"agent","skills":[["echo","Echo"]]}'

  # Connect to custom server
  python client_interactive.py --profile-file profile.json --server ws://localhost:9000
        """
    )
    parser.add_argument(
        '--server', '-s',
        default='ws://localhost:8000',
        help='WebSocket server URL (default: ws://localhost:8000)'
    )
    parser.add_argument(
        '--profile-file', '-f',
        required=True,
        help='Path to JSON file containing profile (required)'
    )
    parser.add_argument(
        '--profile-json', '-j',
        default=None,
        help='Inline profile JSON string'
    )
    
    args = parser.parse_args()
    
    # Load profile (required)
    profile = None
    if args.profile_file:
        profile = load_profile_from_file(args.profile_file)
    elif args.profile_json:
        try:
            profile = json.loads(args.profile_json)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid profile JSON: {e}")
            sys.exit(1)
    
    if not profile:
        print("Error: Profile is required")
        sys.exit(1)
    
    # Validate required fields in profile
    required_fields = ['device_id', 'name', 'role']
    missing = [f for f in required_fields if not profile.get(f)]
    if missing:
        print(f"Error: Profile missing required fields: {', '.join(missing)}")
        sys.exit(1)
    
    return args, profile


class InteractiveClient:
    """Interactive WebSocket client with CLI."""
    
    def __init__(self, server_url: str = "ws://localhost:8000", profile: Optional[dict] = None):
        # Device ID and name come from profile
        self.device_id = profile.get('device_id') if profile else None
        self.name = profile.get('name') if profile else 'Unknown'
        self.server_url = server_url
        self.profile = profile
        self.websocket = None
        self.running = False
        self.connected = False
        self.received_messages = []
        self.sent_messages = []
        
        # Colors for terminal output
        self.colors = {
            'reset': '\033[0m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'dim': '\033[2m',
        }
    
    def color(self, color: str, text: str) -> str:
        """Colorize text."""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
    
    def print_banner(self):
        """Print client banner."""
        print(self.color('bold', '=' * 60))
        print(self.color('bold', f'  WebSocket Interactive Client'))
        print(self.color('bold', f'  Device: {self.name} ({self.device_id})'))
        print(self.color('bold', f'  Server: {self.server_url}'))
        print(self.color('bold', '=' * 60))
        print()
    
    def print_help(self):
        """Print help message."""
        print(self.color('cyan', '\n📋 Available Commands:'))
        print(self.color('white', '  send <client_id> <message>  - Send message to client'))
        print(self.color('white', '  list                       - List all connected clients'))
        print(self.color('white', '  history                     - Show message history'))
        print(self.color('white', '  pending                     - Check pending messages'))
        print(self.color('white', '  clear                       - Clear screen'))
        print(self.color('white', '  help                        - Show this help'))
        print(self.color('white', '  quit                        - Disconnect and exit'))
        print()
    
    def print_received(self, message: dict):
        """Print received message."""
        msg_type = message.get('type')
        
        if msg_type == 'message':
            from_name = message.get('from_client_name', 'Unknown')
            from_id = message.get('from_client_id', '')
            content = message.get('content', '')
            is_offline = message.get('is_offline', False)
            
            prefix = self.color('yellow', '📥') if not is_offline else self.color('magenta', '📬')
            offline_tag = self.color('magenta', ' [OFFLINE]') if is_offline else ''
            
            print(f"\n{prefix} {self.color('bold', from_name)}{offline_tag}: {content}")
            print(f"   {self.color('dim', f'From: {from_id}')}")
            print()
            
            self.received_messages.append({
                'type': 'received',
                'from': from_name,
                'from_id': from_id,
                'content': content,
                'is_offline': is_offline
            })
            
        elif msg_type == 'message_sent':
            success = message.get('success', False)
            to_client = message.get('to_client_id', '')
            msg_text = message.get('message', '')
            
            if success:
                print(f"\n{self.color('green', '✓')} Message sent to {to_client}: {msg_text}")
            else:
                print(f"\n{self.color('red', '✗')} Failed to send: {msg_text}")
            print()
            
            self.sent_messages.append({
                'type': 'sent',
                'to': to_client,
                'success': success,
                'message': msg_text
            })
            
        elif msg_type == 'pending_delivered':
            count = message.get('count', 0)
            print(f"\n{self.color('magenta', f'📬')} Received {count} pending messages from offline")
            print()
            
        elif msg_type == 'message_expired':
            content = message.get('content', '')
            to_client = message.get('to_client_id', '')
            print(f"\n{self.color('red', '⏰')} Message expired (not read): {content}")
            print(f"   {self.color('dim', f'To: {to_client}')}")
            print()
    
    async def connect(self):
        """Connect to WebSocket server."""
        import urllib.parse
        uri = f"{self.server_url}/ws/{self.device_id}"
        
        # Add profile to query params if provided
        if self.profile:
            profile_json = urllib.parse.quote(json.dumps(self.profile))
            uri = f"{uri}?profile={profile_json}"
        
        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print(self.color('green', f"✓ Connected to server as {self.name}"))
            if self.profile:
                print(self.color('cyan', f"  Profile: {self.profile.get('role', 'unknown')} role"))
            return True
        except Exception as e:
            print(self.color('red', f"✗ Connection failed: {e}"))
            return False
    
    async def send(self, message: dict):
        """Send JSON message."""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
    
    async def receive_loop(self):
        """Receive and handle messages."""
        try:
            while self.running and self.connected:
                try:
                    data = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    message = json.loads(data)
                    self.print_received(message)
                except asyncio.TimeoutError:
                    continue
        except websockets.exceptions.ConnectionClosed:
            if self.running:
                print(self.color('red', '\n✗ Connection closed by server'))
                self.connected = False
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            if self.running:
                print(self.color('red', f'\n✗ Error receiving: {e}'))
                self.connected = False
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats."""
        try:
            while self.running and self.connected:
                await asyncio.sleep(10)
                if self.running and self.connected:
                    try:
                        await self.send({"type": "heartbeat"})
                    except:
                        pass
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
    
    async def list_clients(self):
        """List all connected clients via HTTP."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"http://localhost:8000/clients")
                if resp.status_code == 200:
                    data = resp.json()
                    print(self.color('cyan', f"\n📋 Connected Clients ({data['total']}):"))
                    for c in data['clients']:
                        is_me = self.color('yellow', ' (YOU)') if c['client_id'] == self.device_id else ''
                        print(f"  • {self.color('bold', c['name'])}{is_me}")
                        print(f"    {self.color('dim', c['client_id'])}")
                    print()
                else:
                    print(self.color('red', f"✗ Failed to list clients: {resp.status_code}"))
        except Exception as e:
            print(self.color('red', f"✗ Error listing clients: {e}"))
    
    def show_history(self):
        """Show message history."""
        print(self.color('cyan', '\n📨 Sent Messages:'))
        if not self.sent_messages:
            print(self.color('dim', '  (none)'))
        for i, msg in enumerate(self.sent_messages[-10:], 1):
            status = self.color('green', '✓') if msg['success'] else self.color('red', '✗')
            print(f"  {i}. {status} To {msg['to']}: {msg['message'][:50]}...")
        
        print(self.color('cyan', '\n📥 Received Messages:'))
        if not self.received_messages:
            print(self.color('dim', '  (none)'))
        for i, msg in enumerate(self.received_messages[-10:], 1):
            offline = self.color('magenta', ' [OFFLINE]') if msg.get('is_offline') else ''
            print(f"  {i}. From {msg['from']}{offline}: {msg['content'][:50]}...")
        print()
    
    async def check_pending(self):
        """Check pending messages."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"http://localhost:8000/messages/pending/{self.device_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    print(self.color('cyan', f"\n📬 Pending Messages ({data['total']}):"))
                    for m in data['messages']:
                        print(f"  • From {m['from_client_id']}: {m['content']}")
                    print()
                else:
                    print(self.color('red', f"✗ Failed to check pending: {resp.status_code}"))
        except Exception as e:
            print(self.color('red', f"✗ Error: {e}"))
    
    async def handle_command(self, cmd: str):
        """Handle user command."""
        parts = cmd.strip().split(maxsplit=2)
        command = parts[0].lower() if parts else ''
        
        if command == 'send' and len(parts) >= 3:
            to_client = parts[1]
            content = parts[2]
            await self.send({
                "type": "message",
                "to_client_id": to_client,
                "content": content,
                "ttl_seconds": 3600
            })
            print(self.color('yellow', f'→ Sending to {to_client}...'))
            
        elif command == 'list':
            await self.list_clients()
            
        elif command == 'history' or command == 'hist':
            self.show_history()
            
        elif command == 'pending':
            await self.check_pending()
            
        elif command == 'clear' or command == 'cls':
            os.system('clear' if os.name == 'posix' else 'cls')
            self.print_banner()
            self.print_help()
            
        elif command == 'help' or command == '?':
            self.print_help()
            
        elif command == 'quit' or command == 'exit' or command == 'q':
            self.running = False
            print(self.color('yellow', '\n👋 Disconnecting...'))
            
            # Clean up
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass
            
        elif command == '':
            pass
            
        else:
            print(self.color('red', f'Unknown command: {command}'))
            print(self.color('white', 'Type "help" for available commands'))
    
    async def run(self):
        """Run the interactive client."""
        self.print_banner()
        
        # Connect to server
        if not await self.connect():
            return
        
        self.print_help()
        
        self.running = True
        
        # Start background tasks
        receive_task = asyncio.create_task(self.receive_loop())
        heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
        try:
            while self.running and self.connected:
                try:
                    # Use asyncio to make input non-blocking
                    loop = asyncio.get_event_loop()
                    prompt = f"{self.color('bold', self.name)}> "
                    cmd = await loop.run_in_executor(None, lambda: input(prompt).strip())
                    
                    if cmd:
                        await self.handle_command(cmd)
                        
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print(self.color('yellow', '\n\nInterrupted. Type "quit" to exit.'))
                    self.running = False
                    break
                    
        finally:
            self.running = False
            self.connected = False
            
            # Close websocket first to unblock receive
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass
            
            # Cancel background tasks
            for task in [receive_task, heartbeat_task]:
                if task and not task.done():
                    task.cancel()
            
            # Wait for tasks to finish with timeout
            done, pending = await asyncio.wait(
                [receive_task, heartbeat_task], 
                timeout=2.0,
                return_when=asyncio.ALL_COMPLETED
            )
            
            print(self.color('yellow', '\n👋 Disconnected. Goodbye!'))


async def main():
    """Main entry point."""
    args, profile = parse_args()
    
    client = InteractiveClient(
        server_url=args.server,
        profile=profile
    )
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())

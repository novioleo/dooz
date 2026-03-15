# dooz_server/test_clients/user_client_interactive.py
"""
Interactive client for users to communicate with the AI Agent.
Provides a command-line interface for sending messages to the agent and receiving responses.
"""

import asyncio
import argparse
import websockets
import json
import os
from pathlib import Path
from typing import Optional
import sys


def load_profile_from_file(profile_path: str) -> Optional[dict]:
    """Load profile JSON from file."""
    path = Path(profile_path)
    if not path.exists():
        print(f"Error: Profile file not found: {profile_path}")
        return None
    try:
        with open(path, "r") as f:
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
        description="Interactive client for communicating with AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect with profile and default agent (dooz-agent)
  python user_client_interactive.py --profile-file profile.json

  # Connect with custom agent device_id
  python user_client_interactive.py --profile-file profile.json --agent-id my-agent

  # Connect to custom server
  python user_client_interactive.py --profile-file profile.json --server ws://localhost:9000
        """,
    )
    parser.add_argument(
        "--server",
        "-s",
        default="ws://localhost:8000",
        help="WebSocket server URL (default: ws://localhost:8000)",
    )
    parser.add_argument(
        "--profile-file",
        "-f",
        required=True,
        help="Path to JSON file containing user profile (required)",
    )
    parser.add_argument(
        "--profile-json", "-j", default=None, help="Inline profile JSON string"
    )
    parser.add_argument(
        "--agent-id",
        "-a",
        default="dooz-agent",
        help="Agent device ID to send messages to (default: dooz-agent)",
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
    required_fields = ["device_id", "name", "role"]
    missing = [f for f in required_fields if not profile.get(f)]
    if missing:
        print(f"Error: Profile missing required fields: {', '.join(missing)}")
        sys.exit(1)

    return args, profile


class UserAgentClient:
    """Interactive WebSocket client for communicating with AI Agent."""

    def __init__(
        self,
        server_url: str = "ws://localhost:8000",
        profile: Optional[dict] = None,
        agent_id: str = "dooz-agent",
    ):
        # Device ID and name come from profile
        self.device_id = profile.get("device_id") if profile else None
        self.name = profile.get("name") if profile else "Unknown"
        self.server_url = server_url
        self.profile = profile
        self.agent_id = agent_id
        self.websocket = None
        self.running = False
        self.connected = False
        self.conversation_history = []

        # Colors for terminal output
        self.colors = {
            "reset": "\033[0m",
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "bold": "\033[1m",
            "dim": "\033[2m",
        }

    def color(self, color: str, text: str) -> str:
        """Colorize text."""
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    def print_banner(self):
        """Print client banner."""
        print(self.color("bold", "=" * 60))
        print(self.color("bold", f"  AI Agent Chat Client"))
        print(self.color("bold", f"  User: {self.name} ({self.device_id})"))
        print(self.color("bold", f"  Agent: {self.agent_id}"))
        print(self.color("bold", f"  Server: {self.server_url}"))
        print(self.color("bold", "=" * 60))
        print()

    def print_help(self):
        """Print help message."""
        print(self.color("cyan", "\n📋 Available Commands:"))
        print(
            self.color(
                "white", "  msg <message>              - Send message to AI agent"
            )
        )
        print(
            self.color(
                "white", "  ask <question>             - Alias for msg, ask agent a question"
            )
        )
        print(
            self.color(
                "white", "  agent <device_id>          - Change agent device ID"
            )
        )
        print(
            self.color(
                "white", "  history                    - Show conversation history"
            )
        )
        print(
            self.color("white", "  clear                       - Clear screen")
        )
        print(
            self.color("white", "  help                        - Show this help")
        )
        print(
            self.color("white", "  quit                        - Disconnect and exit")
        )
        print()

    def print_agent_response(self, message: dict):
        """Print agent response message."""
        msg_type = message.get("type")

        if msg_type == "agent_response":
            status = message.get("status", "unknown")
            content = message.get("message", "")
            sub_tasks = message.get("sub_tasks", [])

            # Color based on status
            if status == "completed":
                status_color = "green"
                status_icon = "✓"
            elif status == "processing":
                status_color = "yellow"
                status_icon = "⏳"
            elif status == "error":
                status_color = "red"
                status_icon = "✗"
            else:
                status_color = "white"
                status_icon = "?"

            print(f"\n{self.color(status_color, f'{status_icon} Agent')}: {content}")
            
            # Show sub-tasks if any
            if sub_tasks:
                print(self.color("dim", "\n  Sub-tasks:"))
                for task in sub_tasks:
                    task_status = task.get("status", "unknown")
                    task_desc = task.get("description", "")
                    task_result = task.get("result", "")
                    task_error = task.get("error", "")
                    
                    if task_status == "completed":
                        task_icon = self.color("green", "✓")
                    elif task_status == "error":
                        task_icon = self.color("red", "✗")
                    else:
                        task_icon = self.color("yellow", "⏳")
                    
                    print(f"    {task_icon} {task_desc}")
                    if task_result:
                        print(f"      {self.color('dim', f'Result: {task_result}')}")
                    if task_error:
                        print(f"      {self.color('red', f'Error: {task_error}')}")

            print()

            # Add to conversation history
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": content,
                    "status": status,
                }
            )

        elif msg_type == "message_sent":
            success = message.get("success", False)
            to_client = message.get("to_client_id", "")
            msg_text = message.get("message", "")

            if success:
                print(
                    f"\n{self.color('green', '✓')} Message sent to {to_client}: {msg_text}"
                )
            else:
                print(f"\n{self.color('red', '✗')} Failed to send: {msg_text}")
            print()

        elif msg_type == "agent_connected":
            agent_name = message.get("agent_name", "Unknown")
            device_id = message.get("device_id", "")
            print(
                self.color(
                    "green",
                    f"\n✓ Connected to agent: {agent_name} ({device_id})",
                )
            )
            print()

        elif msg_type == "message":
            # Regular message from another client
            from_name = message.get("from_client_name", "Unknown")
            from_id = message.get("from_client_id", "")
            content = message.get("content", "")
            is_offline = message.get("is_offline", False)

            prefix = (
                self.color("yellow", "📥")
                if not is_offline
                else self.color("magenta", "📬")
            )
            offline_tag = (
                self.color("magenta", " [OFFLINE]") if is_offline else ""
            )

            print(f"\n{prefix} {self.color('bold', from_name)}{offline_tag}: {content}")
            print(f"   {self.color('dim', f'From: {from_id}')}")
            print()

        elif msg_type == "pending_delivered":
            count = message.get("count", 0)
            print(
                f"\n{self.color('magenta', f'📬')} Received {count} pending messages from offline"
            )
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
            print(
                self.color("green", f"✓ Connected to server as {self.name}")
            )
            if self.profile:
                role = self.profile.get("role", "unknown")
                role_color = "blue" if role == "user" else "green"
                print(
                    self.color(
                        role_color, f"  Role: {role}"
                    )
                )
            print(
                self.color("cyan", f"  Agent: {self.agent_id}")
            )
            return True
        except Exception as e:
            print(self.color("red", f"✗ Connection failed: {e}"))
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
                    self.print_agent_response(message)
                except asyncio.TimeoutError:
                    continue
        except websockets.exceptions.ConnectionClosed:
            if self.running:
                print(self.color("red", "\n✗ Connection closed by server"))
                self.connected = False
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if self.running:
                print(self.color("red", f"\n✗ Error receiving: {e}"))
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
            pass

    def show_history(self):
        """Show conversation history."""
        print(self.color("cyan", "\n📜 Conversation History:"))
        if not self.conversation_history:
            print(self.color("dim", "  (no messages yet)"))
        for i, msg in enumerate(self.conversation_history, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                print(f"  {i}. {self.color('blue', 'You')}: {content[:60]}...")
            else:
                status = msg.get("status", "")
                status_color = "green" if status == "completed" else "red" if status == "error" else "yellow"
                print(f"  {i}. {self.color(status_color, 'Agent')}: {content[:60]}...")
        print()

    async def handle_command(self, cmd: str):
        """Handle user command."""
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower() if parts else ""

        if command in ("msg", "ask") and len(parts) >= 2:
            # Send message to agent
            content = parts[1]
            await self.send(
                {
                    "type": "message",
                    "to_client_id": self.agent_id,
                    "content": content,
                    "ttl_seconds": 3600,
                }
            )
            print(self.color("yellow", f"→ Asking agent: {content[:50]}..."))

            # Add to conversation history
            self.conversation_history.append(
                {
                    "role": "user",
                    "content": content,
                }
            )

        elif command == "agent" and len(parts) >= 2:
            # Change agent device ID
            new_agent_id = parts[1].strip()
            old_agent_id = self.agent_id
            self.agent_id = new_agent_id
            print(
                self.color(
                    "cyan", f"Changed agent from '{old_agent_id}' to '{self.agent_id}'"
                )
            )

        elif command in ("history", "hist"):
            self.show_history()

        elif command in ("clear", "cls"):
            os.system("clear" if os.name == "posix" else "cls")
            self.print_banner()
            self.print_help()

        elif command in ("help", "?"):
            self.print_help()

        elif command in ("quit", "exit", "q"):
            self.running = False
            print(self.color("yellow", "\n👋 Disconnecting..."))

            # Clean up
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass

        elif command == "":
            pass

        else:
            print(self.color("red", f"Unknown command: {command}"))
            print(
                self.color(
                    "white", 'Type "help" for available commands (use "msg <message>" to chat with agent)'
                )
            )

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
                    cmd = await loop.run_in_executor(
                        None, lambda: input(prompt).strip()
                    )

                    if cmd:
                        await self.handle_command(cmd)

                except EOFError:
                    break
                except KeyboardInterrupt:
                    print(
                        self.color("yellow", '\n\nInterrupted. Type "quit" to exit.')
                    )
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
                return_when=asyncio.ALL_COMPLETED,
            )

            print(self.color("yellow", "\n👋 Disconnected. Goodbye!"))


async def main():
    """Main entry point."""
    args, profile = parse_args()

    client = UserAgentClient(
        server_url=args.server,
        profile=profile,
        agent_id=args.agent_id,
    )
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())

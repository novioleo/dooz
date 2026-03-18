"""Dooz CLI main interface."""

import asyncio
import logging
import uuid
from typing import Optional

from .clarification import ClarificationAgent
from .websocket_client import CliClient

logger = logging.getLogger("dooz_cli")


class DoozCLI:
    """Dooz command-line interface."""
    
    def __init__(self, uri: str = "ws://localhost:8765", enable_clarification: bool = True):
        self.uri = uri
        self.client: Optional[CliClient] = None
        self.session_id = str(uuid.uuid4())
        self._running = False
        self._enable_clarification = enable_clarification
        self._clarification_agent: Optional[ClarificationAgent] = None
    
    async def _handle_message(self, data: dict):
        """Handle message from daemon."""
        msg_type = data.get("type", "")
        
        if msg_type == "response":
            print(f"\n[data] {data.get('content', '')}")
        elif msg_type == "error":
            print(f"\n[error] {data.get('message', 'Unknown error')}")
        elif msg_type == "pong":
            print("\n[pong] Daemon is alive")
        else:
            print(f"\n[{msg_type}] {data}")
        
        if self._running:
            print("> ", end="", flush=True)
    
    async def connect(self) -> bool:
        """Connect to daemon."""
        self.client = CliClient(self.uri, on_message=self._handle_message)
        return await self.client.connect()
    
    async def disconnect(self):
        """Disconnect from daemon."""
        if self.client:
            await self.client.disconnect()
    
    async def send_message(self, content: str, dooz_id: Optional[str] = None):
        """Send user message to daemon."""
        if not self.client:
            logger.error("Not connected to daemon")
            return
        
        message = {
            "type": "user_message",
            "session_id": self.session_id,
            "content": content,
        }
        
        if dooz_id:
            message["dooz_id"] = dooz_id
        
        await self.client.send(message)
    
    async def send_message_with_clarification(
        self,
        content: str,
        dooz_id: Optional[str] = None,
        force: bool = False,
    ) -> bool:
        """Send message with optional clarification."""
        if not self.client:
            logger.error("Not connected to daemon")
            return False
        
        # If clarification disabled or force flag, send directly
        if not self._enable_clarification or force:
            return await self.send_message(content, dooz_id)
        
        # Initialize clarification agent if needed
        if self._clarification_agent is None:
            self._clarification_agent = ClarificationAgent(self.session_id)
        
        # Process through clarification
        response = self._clarification_agent.process_message(content)
        
        if response:
            print(f"\n[Clarification] {response}")
        
        # If clarification complete, send to daemon
        if self._clarification_agent.state.is_complete:
            clarified = self._clarification_agent.get_clarified_request()
            if clarified:
                message = {
                    "type": "clarified_request",
                    "session_id": self.session_id,
                    "clarified_goal": clarified["clarified_goal"],
                    "intent_type": clarified["intent_type"],
                    "entities": clarified["entities"],
                }
                if dooz_id:
                    message["dooz_id"] = dooz_id
                
                await self.client.send(message)
                self._clarification_agent = None  # Reset
                return True
        
        # Still clarifying
        return False
    
    async def ping(self) -> bool:
        """Ping daemon."""
        if not self.client:
            return False
        
        return await self.client.send({
            "type": "ping",
            "session_id": self.session_id,
        })
    
    async def run_interactive_with_clarification(self):
        """Run interactive CLI with clarification agent."""
        if not await self.connect():
            print("Failed to connect to daemon")
            return
        
        print(f"Connected to dooz daemon at {self.uri}")
        print("Type 'quit' or 'exit' to exit, 'ping' to check connection")
        print("Type '--force' to bypass clarification")
        print("> ", end="", flush=True)
        
        self._running = True
        await self.client.start_receiving()
        
        try:
            while self._running:
                try:
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, input, ""
                    )
                    line = line.strip()
                    
                    if not line:
                        print("> ", end="", flush=True)
                        continue
                    
                    if line.lower() in ("quit", "exit"):
                        break
                    elif line.lower() == "ping":
                        await self.ping()
                    else:
                        # Check for --force flag
                        force = "--force" in line
                        content = line.replace("--force", "").strip()
                        
                        await self.send_message_with_clarification(content, force=force)
                        
                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"Error: {e}")
                    
        finally:
            await self.client.stop_receiving()
            await self.disconnect()
            print("\nGoodbye!")

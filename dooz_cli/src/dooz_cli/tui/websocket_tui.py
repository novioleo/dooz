"""WebSocket-enabled TUI application."""

import asyncio
import logging
from typing import Optional

from textual.app import ComposeResult

from dooz_cli.tui.app import DoozTUI
from dooz_cli.tui.models import Message, MessageType
from dooz_cli.tui.screens.main_screen import MainScreen, ChatMessageSubmitted, ExitCommand, NewConversationCommand
from dooz_cli.websocket_client import CliClient

logger = logging.getLogger("dooz_cli")


class WebSocketTUI(DoozTUI):
    """TUI application with WebSocket daemon integration."""
    
    def __init__(self, uri: str = "ws://localhost:8765", **kwargs):
        super().__init__(**kwargs)
        self.uri = uri
        self.client: Optional[CliClient] = None
        self._receive_task: Optional[asyncio.Task] = None
    
    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield MainScreen()
    
    async def on_mount(self) -> None:
        """Handle app mount and connect to daemon."""
        await super().on_mount()
        self.client = CliClient(self.uri, on_message=self._handle_daemon_message)
        
        if await self.client.connect():
            self.screen.query_one(MainScreen).add_system_message("Connected to daemon")
            self._receive_task = asyncio.create_task(self._receive_loop())
        else:
            self.screen.query_one(MainScreen).add_error_message("Failed to connect to daemon")
    
    async def _receive_loop(self) -> None:
        """Receive messages from daemon."""
        if self.client:
            await self.client.start_receiving()
    
    def _handle_daemon_message(self, data: dict) -> None:
        """Handle message from daemon."""
        msg_type = data.get("type", "")
        
        if msg_type == "response":
            content = data.get("content", "")
            self.screen.query_one(MainScreen).add_daemon_message(content)
        elif msg_type == "error":
            error_msg = data.get("message", "Unknown error")
            self.screen.query_one(MainScreen).add_error_message(f"Error: {error_msg}")
        elif msg_type == "pong":
            self.screen.query_one(MainScreen).add_system_message("Pong received")
        else:
            self.screen.query_one(MainScreen).add_system_message(str(data))
    
    def on_chat_message_submitted(self, event: ChatMessageSubmitted) -> None:
        """Handle chat message submitted - send to daemon."""
        if self.client and self.client.is_connected:
            asyncio.create_task(self._send_message(event.content))
        else:
            self.screen.query_one(MainScreen).add_error_message("Not connected to daemon")
    
    async def _send_message(self, content: str) -> None:
        """Send message to daemon."""
        if self.client and self.client.is_connected:
            await self.client.send({
                "type": "user_message",
                "content": content,
            })
    
    def on_exit_command(self, event: ExitCommand) -> None:
        """Handle exit command."""
        self.exit()
    
    def on_new_conversation_command(self, event: NewConversationCommand) -> None:
        """Handle new conversation command."""
        pass
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self.client:
            await self.client.stop_receiving()
            await self.client.disconnect()

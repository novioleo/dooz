# dooz_server/src/dooz_server/message_handler.py
import asyncio
from typing import Optional
from pubsub import pub
from .client_manager import ClientManager
from .message_queue import MessageQueue


class MessageHandler:
    """Handles message routing between clients using pypubsub."""
    
    def __init__(self, client_manager: ClientManager, message_queue: Optional[MessageQueue] = None):
        self.client_manager = client_manager
        self.message_queue = message_queue or MessageQueue()
        self._setup_pubsub_listeners()
    
    def _setup_pubsub_listeners(self):
        """Set up pubsub listeners for message events."""
        pub.subscribe(self._on_message, 'message.send')
        pub.subscribe(self._on_message_expired, 'message.expired')
    
    def _on_message(self, data: dict):
        """Handle incoming message events."""
        pass
    
    def _on_message_expired(self, data: dict):
        """Handle expired messages - notify sender."""
        pass
    
    def send_message(
        self, 
        from_client_id: str, 
        to_client_id: str, 
        content: str,
        ttl_seconds: int = 3600
    ) -> tuple[bool, str, Optional[str]]:
        """
        Send a message from one client to another.
        Returns: (success, message, message_id or error_code)
        """
        # Verify sender exists
        if not self.client_manager.get_client_info(from_client_id):
            return (False, "Sender not found", None)
        
        # Verify recipient exists
        recipient_info = self.client_manager.get_client_info(to_client_id)
        if not recipient_info:
            return (False, "Recipient not found", None)
        
        # Check if recipient is connected
        ws = self.client_manager.get_connection(to_client_id)
        
        if ws:
            # Recipient is online - send directly
            message = {
                "type": "message",
                "from_client_id": from_client_id,
                "from_client_name": self.client_manager.get_client_info(from_client_id).name,
                "to_client_id": to_client_id,
                "content": content
            }
            
            try:
                # Try to send, handle both sync and async websockets
                if hasattr(ws, 'send_json'):
                    try:
                        loop = asyncio.get_running_loop()
                        # We're in async context
                        if asyncio.iscoroutinefunction(ws.send_json):
                            asyncio.create_task(ws.send_json(message))
                        else:
                            loop.run_until_complete(ws.send_json(message))
                    except RuntimeError:
                        # No running loop, try sync
                        loop = asyncio.new_event_loop()
                        try:
                            loop.run_until_complete(ws.send_json(message))
                        finally:
                            loop.close()
                return (True, "Message delivered", None)
            except Exception as e:
                return (False, f"Failed to send: {str(e)}", None)
        else:
            # Recipient is offline - store message
            if ttl_seconds == 0:
                return (False, "Recipient offline and TTL is 0 (no offline storage)", None)
            
            msg_id = self.message_queue.store_message(
                from_client_id=from_client_id,
                to_client_id=to_client_id,
                content=content,
                ttl_seconds=ttl_seconds
            )
            return (True, "Message queued for offline delivery", msg_id)
    
    def deliver_pending_messages(self, client_id: str) -> int:
        """Deliver all pending messages to a newly connected client."""
        pending = self.message_queue.get_pending_messages(client_id)
        ws = self.client_manager.get_connection(client_id)
        
        if not ws:
            return 0
        
        delivered = 0
        for msg in pending:
            message = {
                "type": "message",
                "message_id": msg.message_id,
                "from_client_id": msg.from_client_id,
                "from_client_name": self.client_manager.get_client_info(msg.from_client_id).name,
                "to_client_id": msg.to_client_id,
                "content": msg.content,
                "is_offline": True
            }
            
            try:
                if hasattr(ws, 'send_json'):
                    try:
                        loop = asyncio.get_running_loop()
                        if asyncio.iscoroutinefunction(ws.send_json):
                            asyncio.create_task(ws.send_json(message))
                        else:
                            loop.run_until_complete(ws.send_json(message))
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        try:
                            loop.run_until_complete(ws.send_json(message))
                        finally:
                            loop.close()
                self.message_queue.mark_as_read(msg.message_id)
                delivered += 1
            except Exception:
                pass
        
        return delivered
    
    def get_pending_messages(self, client_id: str) -> list:
        """Get pending messages for a client (without marking as read)."""
        return self.message_queue.get_pending_messages(client_id)
    
    def check_expired_messages(self) -> list:
        """Check and return expired messages, notify senders."""
        expired = self.message_queue.get_expired_messages()
        results = []
        
        for msg in expired:
            results.append({
                "message_id": msg.message_id,
                "from_client_id": msg.from_client_id,
                "to_client_id": msg.to_client_id,
                "content": msg.content
            })
            # Notify sender about expiration
            sender_ws = self.client_manager.get_connection(msg.from_client_id)
            if sender_ws:
                notification = {
                    "type": "message_expired",
                    "message_id": msg.message_id,
                    "to_client_id": msg.to_client_id,
                    "content": msg.content
                }
                try:
                    if hasattr(sender_ws, 'send_json'):
                        try:
                            loop = asyncio.get_running_loop()
                            if asyncio.iscoroutinefunction(sender_ws.send_json):
                                asyncio.create_task(sender_ws.send_json(notification))
                            else:
                                loop.run_until_complete(sender_ws.send_json(notification))
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            try:
                                loop.run_until_complete(sender_ws.send_json(notification))
                            finally:
                                loop.close()
                except Exception:
                    pass
        
        # Clean up expired messages
        self.message_queue.cleanup_expired()
        return results
    
    def broadcast_message(self, from_client_id: str, content: str) -> int:
        """Broadcast a message to all connected clients."""
        clients = self.client_manager.get_all_clients()
        sent_count = 0
        
        for client in clients:
            if client.client_id != from_client_id:
                success, _, _ = self.send_message(from_client_id, client.client_id, content)
                if success:
                    sent_count += 1
        
        return sent_count

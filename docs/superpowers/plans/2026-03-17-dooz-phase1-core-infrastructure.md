# Dooz Phase 1: Core Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build core infrastructure - MQTT broker (NanoMQ), Daemon (WebSocket server + MQTT client), CLI (WebSocket client). All components can communicate but no agent logic yet.

**Architecture:** 
- NanoMQ as MQTT broker for inter-agent communication
- Daemon runs as service, exposes WebSocket for CLI, connects to MQTT
- CLI connects to Daemon via WebSocket, sends commands, receives responses
- Message format: JSON with type, payload, session_id

**Tech Stack:** Python, NanoMQ, asyncio, websockets, pydantic, PyYAML

---

## Chunk 1: Project Setup & NanoMQ

### Task 1.1: Create dooz_daemon Package Structure

**Files:**
- Create: `dooz_daemon/pyproject.toml`
- Create: `dooz_daemon/src/dooz_daemon/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "dooz-daemon"
version = "0.1.0"
description = "Dooz Daemon - Agent management and message routing"
requires-python = ">=3.12"
dependencies = [
    "websockets>=12.0",
    "paho-mqtt>=1.6.0",
    "pydantic>=2.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create __init__.py**

```python
"""Dooz Daemon - Core infrastructure for dooz agent system."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Commit**

```bash
git add dooz_daemon/
git commit -m "feat: create dooz_daemon package structure"
```

---

### Task 1.2: Create dooz_cli Package Structure

**Files:**
- Create: `dooz_cli/pyproject.toml`
- Create: `dooz_cli/src/dooz_cli/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "dooz-cli"
version = "0.1.0"
description = "Dooz CLI - User interface for dooz"
requires-python = ">=3.12"
dependencies = [
    "websockets>=12.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create __init__.py**

```python
"""Dooz CLI - User interface for dooz agent system."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Commit**

```bash
git add dooz_cli/
git commit -m "feat: create dooz_cli package structure"
```

---

### Task 1.3: Install & Configure NanoMQ

**Files:**
- Create: `dooz/scripts/install-nanomq.sh` (install script reference)

- [ ] **Step 1: Check if NanoMQ is installed**

Run: `which nanomq`
Expected: Path to nanomq or empty

- [ ] **Step 2: Install NanoMQ (if not installed)**

```bash
# macOS
brew install nanomq

# Or download from https://github.com/emqx/nanomq/releases
```

- [ ] **Step 3: Start NanoMQ broker**

Run: `nanomq start --url mqtt-tcp://localhost:1883`
Expected: NanoMQ started

- [ ] **Step 4: Test MQTT connection**

Run: `python3 -c "import paho.mqtt.client as mqtt; print('paho-mqtt installed')"`
Expected: No error

- [ ] **Step 5: Commit**

```bash
git add dooz/scripts/  # if created
git commit -m "chore: add nanomq setup"
```

---

## Chunk 2: Daemon Core

### Task 2.1: Daemon Config Module

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/config.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_config.py
import pytest
from pydantic import ValidationError
from dooz_daemon.config import DaemonConfig, load_config

def test_default_config():
    config = DaemonConfig()
    assert config.host == "0.0.0.0"
    assert config.port == 8765
    assert config.mqtt.broker == "localhost"
    assert config.mqtt.port == 1883

def test_load_config_from_dict():
    config = DaemonConfig(
        host="127.0.0.1",
        port=9000,
        mqtt={"broker": "mqtt.local", "port": 1884}
    )
    assert config.host == "127.0.0.1"
    assert config.port == 9000
    assert config.mqtt.broker == "mqtt.local"
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_config.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: Write config module**

```python
# dooz_daemon/src/dooz_daemon/config.py
"""Daemon configuration."""

from pydantic import BaseModel, Field


class MqttConfig(BaseModel):
    """MQTT broker configuration."""
    broker: str = Field(default="localhost", description="MQTT broker host")
    port: int = Field(default=1883, description="MQTT broker port")
    client_id: str = Field(default="daemon", description="MQTT client ID")


class MonitorConfig(BaseModel):
    """Monitor agent configuration."""
    heartbeat_interval: int = Field(default=10, description="Heartbeat interval in seconds")
    offline_threshold: int = Field(default=30, description="Offline threshold in seconds")


class DaemonConfig(BaseModel):
    """Daemon server configuration."""
    host: str = Field(default="0.0.0.0", description="WebSocket server host")
    port: int = Field(default=8765, description="WebSocket server port")
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)


def load_config(**kwargs) -> DaemonConfig:
    """Load daemon configuration from kwargs."""
    return DaemonConfig(**kwargs)
```

- [ ] **Step 4: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/config.py dooz_daemon/tests/test_config.py
git commit -m "feat: add daemon config module"
```

---

### Task 2.2: MQTT Client

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/mqtt_client.py`
- Test: `dooz_daemon/tests/test_mqtt_client.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_mqtt_client.py
import pytest
from unittest.mock import Mock, AsyncMock
from dooz_daemon.mqtt_client import MqttClient, MqttMessage

@pytest.mark.asyncio
async def test_mqtt_client_initialization():
    client = MqttClient("localhost", 1883, "test-client")
    assert client.broker == "localhost"
    assert client.port == 1883
    assert client.client_id == "test-client"

@pytest.mark.asyncio
async def test_mqtt_client_connect():
    client = MqttClient("localhost", 1883, "test-client")
    # Mock the paho client
    client._client = Mock()
    client._client.connect = Mock(return_value=0)
    
    await client.connect()
    client._client.connect.assert_called_once()
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_mqtt_client.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: Write MQTT client module**

```python
# dooz_daemon/src/dooz_daemon/mqtt_client.py
"""MQTT client for dooz daemon."""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

import paho.mqtt.client as mqtt

logger = logging.getLogger("dooz_daemon.mqtt")


class MqttMessage:
    """MQTT message wrapper."""
    
    def __init__(
        self,
        topic: str,
        payload: str,
        qos: int = 0,
        retain: bool = False,
    ):
        self.topic = topic
        self.payload = payload
        self.qos = qos
        self.retain = retain
    
    @property
    def data(self) -> dict[str, Any]:
        """Parse payload as JSON."""
        try:
            return json.loads(self.payload)
        except json.JSONDecodeError:
            return {"raw": self.payload}
    
    def __repr__(self) -> str:
        return f"MqttMessage(topic={self.topic}, payload={self.payload[:50]}...)"


class MqttClient:
    """Async MQTT client wrapper."""
    
    def __init__(
        self,
        broker: str,
        port: int,
        client_id: str,
        on_message: Optional[Callable[[MqttMessage], None]] = None,
    ):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.on_message = on_message
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._loop: Optional[asyncio.Task] = None
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected."""
        if rc == 0:
            self._connected = True
            logger.info(f"Connected to MQTT broker {self.broker}:{self.port}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received."""
        if self.on_message:
            message = MqttMessage(
                topic=msg.topic,
                payload=msg.payload.decode("utf-8"),
                qos=msg.qos,
                retain=msg.retain,
            )
            self.on_message(message)
    
    async def connect(self) -> bool:
        """Connect to MQTT broker."""
        self._client = mqtt.Client(client_id=self.client_id)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        
        try:
            self._client.connect(self.broker, self.port, keepalive=60)
            self._client.loop_start()
            
            # Wait for connection
            for _ in range(50):  # 5 seconds max
                if self._connected:
                    return True
                await asyncio.sleep(0.1)
            
            logger.error("MQTT connection timeout")
            return False
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("Disconnected from MQTT broker")
    
    async def subscribe(self, topic: str, qos: int = 1) -> bool:
        """Subscribe to a topic."""
        if not self._connected:
            logger.error("Not connected to MQTT broker")
            return False
        
        result = self._client.subscribe(topic, qos)
        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Subscribed to topic: {topic}")
            return True
        else:
            logger.error(f"Failed to subscribe to {topic}")
            return False
    
    async def publish(self, topic: str, payload: str | dict, qos: int = 1) -> bool:
        """Publish to a topic."""
        if not self._connected:
            logger.error("Not connected to MQTT broker")
            return False
        
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        
        result = self._client.publish(topic, payload, qos)
        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published to {topic}: {payload[:50]}...")
            return True
        else:
            logger.error(f"Failed to publish to {topic}")
            return False
```

- [ ] **Step 4: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_mqtt_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/mqtt_client.py dooz_daemon/tests/test_mqtt_client.py
git commit -m "feat: add MQTT client module"
```

---

### Task 2.3: WebSocket Server

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/websocket_server.py`
- Test: `dooz_daemon/tests/test_websocket_server.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_websocket_server.py
import pytest
import asyncio
from dooz_daemon.websocket_server import WsMessage

def test_ws_message_parse():
    msg = WsMessage(type="user_message", content="hello", session_id="123")
    assert msg.type == "user_message"
    assert msg.content == "hello"
    assert msg.session_id == "123"
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_websocket_server.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: Write WebSocket server module**

```python
# dooz_daemon/src/dooz_daemon/websocket_server.py
"""WebSocket server for dooz daemon."""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger("dooz_daemon.ws")


class WsMessage:
    """WebSocket message."""
    
    def __init__(
        self,
        type: str,
        session_id: str,
        content: Optional[str] = None,
        dooz_id: Optional[str] = None,
        **kwargs,
    ):
        self.type = type
        self.session_id = session_id
        self.content = content
        self.dooz_id = dooz_id
        self.extra = kwargs
    
    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "WsMessage":
        """Parse from JSON."""
        return cls(
            type=data.get("type", ""),
            session_id=data.get("session_id", ""),
            content=data.get("content"),
            dooz_id=data.get("dooz_id"),
            **{k: v for k, v in data.items() 
               if k not in ("type", "session_id", "content", "dooz_id")},
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        result = {"type": self.type, "session_id": self.session_id}
        if self.content is not None:
            result["content"] = self.content
        if self.dooz_id is not None:
            result["dooz_id"] = self.dooz_id
        result.update(self.extra)
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class WebSocketServer:
    """WebSocket server for CLI connections."""
    
    def __init__(
        self,
        host: str,
        port: int,
        message_handler: Callable[[WsMessage, WebSocketServerProtocol], Any],
    ):
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self._server: Optional[websockets.Server] = None
        self._clients: set[WebSocketServerProtocol] = set()
    
    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """Handle a client connection."""
        self._clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    ws_msg = WsMessage.from_json(data)
                    
                    # Process message
                    response = await self.message_handler(ws_msg, websocket)
                    
                    # Send response if any
                    if response:
                        if isinstance(response, WsMessage):
                            await websocket.send(response.to_json())
                        elif isinstance(response, dict):
                            await websocket.send(json.dumps(response))
                        elif isinstance(response, str):
                            await websocket.send(response)
                            
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {websocket.remote_address}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }))
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            self._clients.discard(websocket)
    
    async def start(self):
        """Start the WebSocket server."""
        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
        )
        logger.info(f"WebSocket server started on {self.host}:{self.port}")
    
    async def stop(self):
        """Stop the WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def broadcast(self, message: WsMessage | dict):
        """Broadcast message to all clients."""
        if isinstance(message, WsMessage):
            msg_str = message.to_json()
        else:
            msg_str = json.dumps(message)
        
        if self._clients:
            await asyncio.gather(
                *[client.send(msg_str) for client in self._clients],
                return_exceptions=True,
            )
```

- [ ] **Step 4: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_websocket_server.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/websocket_server.py dooz_daemon/tests/test_websocket_server.py
git commit -m "feat: add WebSocket server module"
```

---

### Task 2.4: Daemon Main Module

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/daemon.py`
- Modify: `dooz_daemon/src/dooz_daemon/__init__.py`
- Test: `dooz_daemon/tests/test_daemon.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_daemon.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from dooz_daemon.daemon import DoozDaemon

@pytest.mark.asyncio
async def test_daemon_initialization():
    config = DaemonConfig()
    daemon = DoozDaemon(config)
    assert daemon.config == config
    assert not daemon._running
```

- [ ] **Step 2: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_daemon.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: Write daemon module**

```python
# dooz_daemon/src/dooz_daemon/daemon.py
"""Dooz daemon main module."""

import asyncio
import logging
from typing import Any, Optional

from .config import DaemonConfig
from .mqtt_client import MqttClient, MqttMessage
from .websocket_server import WebSocketServer, WsMessage, WebSocketServerProtocol

logger = logging.getLogger("dooz_daemon")


class DoozDaemon:
    """Main daemon process for dooz."""
    
    def __init__(self, config: DaemonConfig):
        self.config = config
        self._running = False
        self._mqtt_client: Optional[MqttClient] = None
        self._ws_server: Optional[WebSocketServer] = None
    
    async def _handle_ws_message(
        self,
        message: WsMessage,
        client: WebSocketServerProtocol,
    ) -> dict[str, Any]:
        """Handle WebSocket message from CLI."""
        logger.info(f"Received message: {message.type} from {message.session_id}")
        
        # Echo back for now (Phase 1 - no agent logic yet)
        if message.type == "user_message":
            return {
                "type": "response",
                "session_id": message.session_id,
                "content": f"Echo: {message.content}",
            }
        elif message.type == "ping":
            return {"type": "pong", "session_id": message.session_id}
        else:
            return {
                "type": "error",
                "session_id": message.session_id,
                "message": f"Unknown message type: {message.type}",
            }
    
    async def start(self):
        """Start the daemon."""
        logger.info("Starting dooz daemon...")
        
        # Start MQTT client
        self._mqtt_client = MqttClient(
            broker=self.config.mqtt.broker,
            port=self.config.mqtt.port,
            client_id=self.config.mqtt.client_id,
        )
        
        if not await self._mqtt_client.connect():
            logger.error("Failed to connect to MQTT broker")
            return
        
        # Start WebSocket server
        self._ws_server = WebSocketServer(
            host=self.config.host,
            port=self.config.port,
            message_handler=self._handle_ws_message,
        )
        await self._ws_server.start()
        
        self._running = True
        logger.info("Dooz daemon started successfully")
        
        # Keep running
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Daemon cancelled")
    
    async def stop(self):
        """Stop the daemon."""
        logger.info("Stopping dooz daemon...")
        self._running = False
        
        if self._ws_server:
            await self._ws_server.stop()
        
        if self._mqtt_client:
            await self._mqtt_client.disconnect()
        
        logger.info("Dooz daemon stopped")
```

- [ ] **Step 4: Update __init__.py**

```python
# dooz_daemon/src/dooz_daemon/__init__.py
"""Dooz Daemon - Core infrastructure for dooz agent system."""

from .config import DaemonConfig, load_config
from .daemon import DoozDaemon
from .mqtt_client import MqttClient, MqttMessage
from .websocket_server import WebSocketServer, WsMessage

__version__ = "0.1.0"

__all__ = [
    "DaemonConfig",
    "load_config",
    "DoozDaemon",
    "MqttClient",
    "MqttMessage",
    "WebSocketServer",
    "WsMessage",
]
```

- [ ] **Step 5: Run test**

Run: `cd dooz_daemon && uv run pytest tests/test_daemon.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/daemon.py dooz_daemon/src/dooz_daemon/__init__.py dooz_daemon/tests/test_daemon.py
git commit -m "feat: add daemon main module"
```

---

### Task 2.5: Daemon CLI Entry Point

**Files:**
- Create: `dooz_daemon/src/dooz_daemon/__main__.py`
- Create: `dooz_daemon/pyproject.toml` (console script)

- [ ] **Step 1: Write __main__.py**

```python
# dooz_daemon/src/dooz_daemon/__main__.py
"""Daemon CLI entry point."""

import asyncio
import logging
import signal

from . import DoozDaemon, DaemonConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    """Main entry point."""
    config = DaemonConfig()
    daemon = DoozDaemon(config)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Handle shutdown signals
    def signal_handler(sig):
        print(f"\nReceived signal {sig}, shutting down...")
        loop.create_task(daemon.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        loop.run_until_complete(daemon.start())
    except Exception as e:
        logging.error(f"Daemon error: {e}")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Update pyproject.toml with console script**

```toml
[project.scripts]
dooz-daemon = "dooz_daemon.__main__:main"
```

- [ ] **Step 3: Test daemon starts**

Run: `cd dooz_daemon && uv sync && timeout 3 uv run dooz-daemon || true`
Expected: "Starting dooz daemon..." in logs

- [ ] **Step 4: Commit**

```bash
git add dooz_daemon/src/dooz_daemon/__main__.py dooz_daemon/pyproject.toml
git commit -m "feat: add daemon CLI entry point"
```

---

## Chunk 3: CLI Core

### Task 3.1: CLI WebSocket Client

**Files:**
- Create: `dooz_cli/src/dooz_cli/websocket_client.py`
- Test: `dooz_cli/tests/test_websocket_client.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_websocket_client.py
import pytest
from dooz_cli.websocket_client import CliClient

def test_cli_client_initialization():
    client = CliClient("ws://localhost:8765")
    assert client.uri == "ws://localhost:8765"
```

- [ ] **Step 2: Run test**

Run: `cd dooz_cli && uv run pytest tests/test_websocket_client.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: Write CLI WebSocket client module**

```python
# dooz_cli/src/dooz_cli/websocket_client.py
"""WebSocket client for dooz CLI."""

import asyncio
import json
import logging
from typing import Any, Callable, Optional

import websockets
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger("dooz_cli")


class CliClient:
    """WebSocket client for CLI."""
    
    def __init__(
        self,
        uri: str = "ws://localhost:8765",
        on_message: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        self.uri = uri
        self.on_message = on_message
        self._ws: Optional[WebSocketClientProtocol] = None
        self._running = False
        self._receive_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """Connect to daemon."""
        try:
            self._ws = await websockets.connect(self.uri)
            logger.info(f"Connected to {self.uri}")
            self._running = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from daemon."""
        self._running = False
        if self._ws:
            await self._ws.close()
            logger.info("Disconnected from daemon")
    
    async def send(self, message: dict[str, Any]) -> bool:
        """Send message to daemon."""
        if not self._ws:
            logger.error("Not connected")
            return False
        
        try:
            await self._ws.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def _receive_loop(self):
        """Receive messages from daemon."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    if self.on_message:
                        self.on_message(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        finally:
            self._running = False
    
    async def start_receiving(self):
        """Start receiving messages."""
        self._receive_task = asyncio.create_task(self._receive_loop())
    
    async def stop_receiving(self):
        """Stop receiving messages."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
    
    @property
    def is_connected(self) -> bool:
        return self._ws is not None and self._running
```

- [ ] **Step 4: Run test**

Run: `cd dooz_cli && uv run pytest tests/test_websocket_client.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_cli/src/dooz_cli/websocket_client.py dooz_cli/tests/test_websocket_client.py
git commit -m "feat: add CLI WebSocket client module"
```

---

### Task 3.2: CLI Main Interface

**Files:**
- Create: `dooz_cli/src/dooz_cli/cli.py`
- Modify: `dooz_cli/src/dooz_cli/__init__.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cli.py
import pytest
from unittest.mock import Mock
from dooz_cli.cli import DoozCLI

def test_cli_initialization():
    cli = DoozCLI("ws://localhost:8765")
    assert cli.uri == "ws://localhost:8765"
```

- [ ] **Step 2: Run test**

Run: `cd dooz_cli && uv run pytest tests/test_cli.py -v`
Expected: FAIL - ModuleNotFoundError

- [ ] **Step 3: Write CLI main module**

```python
# dooz_cli/src/dooz_cli/cli.py
"""Dooz CLI main interface."""

import asyncio
import logging
import uuid
from typing import Optional

from .websocket_client import CliClient

logger = logging.getLogger("dooz_cli")


class DoozCLI:
    """Dooz command-line interface."""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.client: Optional[CliClient] = None
        self.session_id = str(uuid.uuid4())
        self._running = False
    
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
    
    async def ping(self) -> bool:
        """Ping daemon."""
        if not self.client:
            return False
        
        return await self.client.send({
            "type": "ping",
            "session_id": self.session_id,
        })
    
    async def run_interactive(self):
        """Run interactive CLI session."""
        if not await self.connect():
            print("Failed to connect to daemon")
            return
        
        print(f"Connected to dooz daemon at {self.uri}")
        print("Type 'quit' or 'exit' to exit, 'ping' to check connection")
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
                        await self.send_message(line)
                        
                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"Error: {e}")
                    
        finally:
            await self.client.stop_receiving()
            await self.disconnect()
            print("\nGoodbye!")
```

- [ ] **Step 4: Update __init__.py**

```python
# dooz_cli/src/dooz_cli/__init__.py
"""Dooz CLI - User interface for dooz agent system."""

from .cli import DoozCLI
from .websocket_client import CliClient

__version__ = "0.1.0"

__all__ = ["DoozCLI", "CliClient"]
```

- [ ] **Step 5: Run test**

Run: `cd dooz_cli && uv run pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add dooz_cli/src/dooz_cli/cli.py dooz_cli/src/dooz_cli/__init__.py dooz_cli/tests/test_cli.py
git commit -m "feat: add CLI main interface"
```

---

### Task 3.3: CLI Entry Point

**Files:**
- Create: `dooz_cli/src/dooz_cli/__main__.py`
- Modify: `dooz_cli/pyproject.toml` (console script)

- [ ] **Step 1: Write __main__.py**

```python
# dooz_cli/src/dooz_cli/__main__.py
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
            # Interactive mode
            await cli.run_interactive()
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Update pyproject.toml**

```toml
[project.scripts]
dooz = "dooz_cli.__main__:main"
```

- [ ] **Step 3: Test CLI help**

Run: `cd dooz_cli && uv sync && uv run dooz --help`
Expected: Help text

- [ ] **Step 4: Commit**

```bash
git add dooz_cli/src/dooz_cli/__main__.py dooz_cli/pyproject.toml
git commit -m "feat: add CLI entry point"
```

---

## Chunk 4: Integration Test

### Task 4.1: End-to-End Integration Test

**Files:**
- Create: `tests/integration/test_daemon_cli_mqtt.py`

- [ ] **Step 1: Write integration test**

```python
# tests/integration/test_daemon_cli_mqtt.py
"""End-to-end integration test for daemon, CLI, and MQTT."""

import asyncio
import pytest

# This test requires:
# 1. NanoMQ running on localhost:1883
# 2. Daemon running on localhost:8765


@pytest.mark.integration
@pytest.mark.asyncio
async def test_daemon_cli_communication():
    """Test that CLI can communicate with daemon."""
    from dooz_cli import DoozCLI
    
    cli = DoozCLI("ws://localhost:8765")
    
    # Connect
    connected = await cli.connect()
    assert connected, "Failed to connect to daemon"
    
    # Ping
    result = await cli.ping()
    assert result, "Failed to send ping"
    
    # Wait for response
    await asyncio.sleep(1)
    
    # Disconnect
    await cli.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mqtt_publish_subscribe():
    """Test MQTT publish/subscribe."""
    from dooz_daemon import MqttClient, MqttMessage
    
    received = []
    
    def on_message(msg: MqttMessage):
        received.append(msg)
    
    # Create subscriber
    sub = MqttClient("localhost", 1883, "test-sub", on_message=on_message)
    await sub.connect()
    await sub.subscribe("dooz/test/topic")
    
    # Create publisher
    pub = MqttClient("localhost", 1883, "test-pub")
    await pub.connect()
    await pub.publish("dooz/test/topic", {"hello": "world"})
    
    # Wait for message
    await asyncio.sleep(1)
    
    # Verify
    assert len(received) > 0
    assert received[0].topic == "dooz/test/topic"
    
    # Cleanup
    await sub.disconnect()
    await pub.disconnect()
```

- [ ] **Step 2: Run integration test (if broker and daemon running)**

Run: `cd dooz && uv run pytest tests/integration/test_daemon_cli_mqtt.py -v -m integration`
Expected: SKIPPED (if not running) or PASS (if running)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/
git commit -m "test: add integration tests"
```

---

## Summary

After completing Phase 1, you will have:
- [x] dooz_daemon package with WebSocket server and MQTT client
- [x] dooz_cli package with interactive CLI
- [x] NanoMQ broker (external)
- [x] Basic communication: CLI → WebSocket → Daemon → MQTT

**Next Phase:** Implement Core Agents (Monitor, Orchestrator, Task Scheduler) with heartbeat and task distribution.

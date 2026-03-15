# Client Profile Schema Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a strongly-validated profile schema to client registration, with support for name, role, extra info, **skills (list of tuples)**, input/output capabilities.

**Architecture:** Add a ClientProfile schema with required fields (name, role) and optional fields (extra_info, native_commands, supports_input, supports_output). Integrate into ClientInfo and client registration flow. Use Pydantic's `model_config` to allow extra fields to pass through without strict validation.

**Tech Stack:** Python 3.12+, Pydantic 2.5+, FastAPI, pytest

---

## File Structure

- `dooz_server/src/dooz_server/schemas.py` - Add ClientProfile schema, update ClientInfo
- `dooz_server/src/dooz_server/client_manager.py` - Update register_client() to accept profile
- `dooz_server/src/dooz_server/router.py` - Update WebSocket endpoint to accept profile in connection
- `dooz_server/tests/test_schemas.py` - Add tests for ClientProfile validation
- `dooz_server/tests/test_client_manager.py` - Add tests for profile registration

---

## Chunk 1: Schema Definition

### Task 1: Define ClientProfile Schema

**Files:**
- Modify: `dooz_server/src/dooz_server/schemas.py`
- Test: `dooz_server/tests/test_schemas.py`

- [ ] **Step 1: Write failing tests for ClientProfile schema**

```python
# Add to dooz_server/tests/test_schemas.py

def test_client_profile_required_fields():
    """Test that name and role are required."""
    from pydantic import ValidationError
    
    # Missing name should fail
    with pytest.raises(ValidationError):
        ClientProfile(role="agent")
    
    # Missing role should fail
    with pytest.raises(ValidationError):
        ClientProfile(name="TestClient")
    # Both present should pass
    profile = ClientProfile(name="TestClient", role="agent")
    assert profile.name == "TestClient"
    assert profile.role == "agent"


def test_client_profile_optional_fields():
    """Test optional fields have correct defaults."""
    profile = ClientProfile(name="TestClient", role="agent")
    assert profile.extra_info is None
    assert profile.skills == []
    assert profile.supports_input is False
    assert profile.supports_output is False


def test_client_profile_all_fields():
    """Test creating profile with all fields."""
    # skills is list[tuple[str, str]] - (ability_name, ability_description)
    profile = ClientProfile(
        name="TestClient",
        role="agent",
        extra_info="Custom info",
        skills=[("echo", "Echo back the input"), ("ls", "List directory contents")],
        supports_input=True,
        supports_output=True
    )
    assert profile.name == "TestClient"
    assert profile.role == "agent"
    assert profile.extra_info == "Custom info"
    assert profile.skills == [("echo", "Echo back the input"), ("ls", "List directory contents")]
    assert profile.supports_input is True
    assert profile.supports_output is True


def test_client_profile_extra_fields_ignored():
    """Test that extra fields are ignored (not strictly validated)."""
    # Extra fields should not raise validation error
    profile = ClientProfile(
        name="TestClient",
        role="agent",
        unknown_field="should be ignored"
    )
    assert profile.name == "TestClient"
    # The unknown_field should not be in the model
    assert not hasattr(profile, 'unknown_field')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_schemas.py::test_client_profile_required_fields -v`
Expected: FAIL with "ClientProfile not defined"

- [ ] **Step 3: Write minimal ClientProfile schema implementation**

```python
# Add to dooz_server/src/dooz_server/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ClientProfile(BaseModel):
    """Profile information for a registered client."""
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields, no strict validation
    
    name: str = Field(..., min_length=1, description="Client display name")
    role: str = Field(..., min_length=1, description="Client role (e.g., agent, user, service)")
    extra_info: Optional[str] = Field(default=None, description="Custom extra information")
    skills: list[tuple[str, str]] = Field(default_factory=list, description="List of (ability_name, ability_description) tuples")
    supports_input: bool = Field(default=False, description="Whether client supports input")
    supports_output: bool = Field(default=False, description="Whether client supports output")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_schemas.py::test_client_profile_required_fields tests/test_schemas.py::test_client_profile_optional_fields tests/test_schemas.py::test_client_profile_all_fields tests/test_schemas.py::test_client_profile_extra_fields_ignored -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz/dooz_server && git add src/dooz_server/schemas.py tests/test_schemas.py && git commit -m "feat: add ClientProfile schema with strong validation for required fields"
```

---

### Task 2: Update ClientInfo to Include Profile

**Files:**
- Modify: `dooz_server/src/dooz_server/schemas.py`
- Test: `dooz_server/tests/test_schemas.py`

- [ ] **Step 1: Write failing test for ClientInfo with profile**

```python
# Add to dooz_server/tests/test_schemas.py

def test_client_info_with_profile():
    """Test that ClientInfo accepts profile field."""
    profile = ClientProfile(name="TestClient", role="agent", supports_input=True)
    client = ClientInfo(
        client_id="test-123",
        name="TestUser",
        connected_at="2024-01-01T00:00:00Z",
        profile=profile
    )
    assert client.client_id == "test-123"
    assert client.profile.name == "TestClient"
    assert client.profile.role == "agent"
    assert client.profile.supports_input is True


def test_client_info_profile_optional():
    """Test that profile is optional in ClientInfo."""
    client = ClientInfo(
        client_id="test-123",
        name="TestUser",
        connected_at="2024-01-01T00:00:00Z"
    )
    assert client.profile is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_schemas.py::test_client_info_with_profile -v`
Expected: FAIL with "profile field not found"

- [ ] **Step 3: Update ClientInfo schema**

```python
# Modify ClientInfo in dooz_server/src/dooz_server/schemas.py

class ClientInfo(BaseModel):
    """Information about a connected client."""
    client_id: str
    name: str
    connected_at: str
    profile: Optional[ClientProfile] = Field(default=None, description="Client profile information")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_schemas.py::test_client_info_with_profile tests/test_schemas.py::test_client_info_profile_optional -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz/dooz_server && git add src/dooz_server/schemas.py tests/test_schemas.py && git commit -m "feat: add profile field to ClientInfo schema"
```

---

## Chunk 2: Client Manager Integration

### Task 3: Update ClientManager.register_client to Accept Profile

**Files:**
- Modify: `dooz_server/src/dooz_server/client_manager.py`
- Test: `dooz_server/tests/test_client_manager.py`

- [ ] **Step 1: Write failing test for register_client with profile**

```python
# Add to dooz_server/tests/test_client_manager.py

def test_register_client_with_profile(client_manager):
    """Test registering a client with profile information."""
    from dooz_server.schemas import ClientProfile
    
    profile = ClientProfile(
        name="TestAgent",
        role="agent",
        skills=[("echo", "Echo back input"), ("ls", "List directory")],
        supports_input=True,
        supports_output=False
    )
    client_id = client_manager.register_client(
        client_id="agent-001",
        name="TestAgent",
        profile=profile,
        connection_type="WebSocket"
    )
    
    info = client_manager.get_client_info(client_id)
    assert info is not None
    assert info.profile is not None
    assert info.profile.name == "TestAgent"
    assert info.profile.role == "agent"
    assert info.profile.skills == [("echo", "Echo back input"), ("ls", "List directory")]
    assert info.profile.supports_input is True
    assert info.profile.supports_output is False


def test_register_client_without_profile(client_manager):
    """Test that profile is optional when registering."""
    client_id = client_manager.register_client(
        client_id="user-001",
        name="RegularUser",
        connection_type="WebSocket"
    )
    
    info = client_manager.get_client_info(client_id)
    assert info is not None
    assert info.profile is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_client_manager.py::test_register_client_with_profile -v`
Expected: FAIL with "unexpected keyword argument 'profile'"

- [ ] **Step 3: Update ClientManager.register_client**

```python
# Modify register_client in dooz_server/src/dooz_server/client_manager.py

from .schemas import ClientInfo, ClientProfile

def register_client(
    self, 
    client_id: Optional[str] = None, 
    name: Optional[str] = None, 
    profile: Optional[ClientProfile] = None,
    connection_type: str = "WebSocket"
) -> str:
    """Register a new client and return their client_id.
    
    If client_id is not provided, a new UUID will be generated.
    If name is not provided, it will be derived from client_id.
    If profile is provided, it will be associated with the client.
    """
    # Generate client_id if not provided
    if client_id is None:
        client_id = str(uuid.uuid4())
    
    # Use name if provided, otherwise derive from client_id
    if name is None:
        name = client_id.split('-')[0].capitalize() if '-' in client_id else client_id
    
    client_info = ClientInfo(
        client_id=client_id,
        name=name,
        connected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        profile=profile
    )
    self._clients[client_id] = client_info
    logger.info(f"Client registered: {client_id} ({name}) via {connection_type}")
    return client_id
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_client_manager.py::test_register_client_with_profile tests/test_client_manager.py::test_register_client_without_profile -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz/dooz_server && git add src/dooz_server/client_manager.py tests/test_client_manager.py && git commit -m "feat: add profile parameter to ClientManager.register_client"
```

---

## Chunk 3: Router Integration

### Task 4: Update WebSocket Endpoint to Accept Profile

**Files:**
- Modify: `dooz_server/src/dooz_server/router.py`
- Test: `dooz_server/tests/test_router.py` (add new tests)

- [ ] **Step 1: Write failing test for WebSocket registration with profile**

```python
# Add to dooz_server/tests/test_router.py

@pytest.mark.asyncio
async def test_websocket_register_with_profile():
    """Test WebSocket connection accepts profile in connection request."""
    from fastapi.testclient import TestClient
    from dooz_server.main import create_app
    from dooz_server.router import get_client_manager
    
    app = create_app()
    
    # The profile would be sent in the WebSocket connection query params
    # as JSON-encoded string
    import json
    import urllib.parse
    
    profile_data = {
        "name": "TestAgent",
        "role": "agent",
        "skills": [["echo", "Echo back input"], ["ls", "List directory"]],
        "supports_input": True,
        "supports_output": False
    }
    profile_json = urllib.parse.quote(json.dumps(profile_data))
    
    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/test-client?profile={profile_json}") as ws:
            # Client should be registered with profile
            client_manager = get_client_manager()
            info = client_manager.get_client_info("test-client")
            assert info is not None
            assert info.profile is not None
            assert info.profile.name == "TestAgent"
            assert info.profile.role == "agent"
            assert info.profile.skills == [("echo", "Echo back input"), ("ls", "List directory")]
            assert info.profile.supports_input is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_router.py::test_websocket_register_with_profile -v`
Expected: FAIL with profile not being processed

- [ ] **Step 3: Update WebSocket endpoint to accept profile**

```python
# Modify websocket_endpoint in dooz_server/src/dooz_server/router.py

import json
import urllib.parse
from .schemas import ClientProfile

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, profile: Optional[str] = None):
    """WebSocket endpoint for client connections with heartbeat support and optional profile."""
    ws_mgr = get_ws_manager()
    await ws_mgr.connect(client_id, websocket)
    
    # Parse profile if provided
    client_profile = None
    if profile:
        try:
            profile_data = json.loads(urllib.parse.unquote(profile))
            client_profile = ClientProfile(**profile_data)
        except Exception as e:
            logger.warning(f"Failed to parse profile for {client_id}: {e}")
    
    # Register with client manager (auto-register if not exists)
    client_manager = get_client_manager()
    logger.info(f"WebSocket: Checking client {client_id}, existing: {client_manager.get_client_info(client_id)}")
    existing_client = client_manager.get_client_info(client_id)
    if not existing_client:
        # Auto-register new client with name from profile or derived from client_id
        client_name = client_profile.name if client_profile else (client_id.split('-')[0].capitalize() if '-' in client_id else client_id)
        registered_id = client_manager.register_client(client_id, client_name, client_profile, "WebSocket")
        logger.info(f"WebSocket: Registered new client {registered_id}, now exists: {client_manager.get_client_info(client_id)}")
    client_manager.add_connection(client_id, websocket)
    
    # ... rest of the existing code
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_router.py::test_websocket_register_with_profile -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz/dooz_server && git add src/dooz_server/router.py tests/test_router.py && git commit -m "feat: add profile support to WebSocket endpoint"
```

---

### Task 5: Update Interactive Test Client to Support Profile

**Files:**
- Modify: `dooz_server/test_clients/client_interactive.py`
- Test: `dooz_server/test_clients/client_interactive.py` (manual test)

- [ ] **Step 1: Write failing test - verify client doesn't support profile**

Currently the client connects without profile. We'll verify this by checking the code.

- [ ] **Step 2: Update InteractiveClient to accept and send profile**

```python
# Modify InteractiveClient in dooz_server/test_clients/client_interactive.py
# Add Optional import at the top
from typing import Optional, Tuple, List

class InteractiveClient:
    """Interactive WebSocket client with CLI."""
    
    def __init__(
        self, 
        client_id: str, 
        name: str, 
        server_url: str = "ws://localhost:8000",
        profile: Optional[dict] = None
    ):
        self.client_id = client_id
        self.name = name
        self.server_url = server_url
        self.profile = profile  # New: profile dict
        self.websocket = None
        self.running = False
        self.connected = False
        self.received_messages = []
        self.sent_messages = []
        # ... rest of colors remains the same
```

- [ ] **Step 3: Update connect method to send profile as query param**

```python
    async def connect(self):
        """Connect to WebSocket server."""
        import urllib.parse
        uri = f"{self.server_url}/ws/{self.client_id}"
        
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
```

- [ ] **Step 4: Update main() to support profile arguments**

```python
async def main():
    """Main entry point."""
    # Default client info
    client_id = "client-001"
    name = "TestUser"
    server_url = "ws://localhost:8000"
    profile = None
    
    # Parse arguments
    if len(sys.argv) > 1:
        name = sys.argv[1]
        client_id = f"{name.lower()}-{id(name) % 1000:03d}"
    if len(sys.argv) > 2:
        client_id = sys.argv[2]
    if len(sys.argv) > 3:
        server_url = sys.argv[3]
    
    # Parse profile from arguments (JSON string)
    # Usage: python client_interactive.py <name> <client_id> <server_url> '<profile_json>'
    # Example: python client_interactive.py Agent1 agent-001 ws://localhost:8000 '{"name":"Agent1","role":"agent","skills":[["echo","Echo"]],"supports_input":true}'
    if len(sys.argv) > 4:
        try:
            profile = json.loads(sys.argv[4])
        except json.JSONDecodeError:
            print(f"Warning: Invalid profile JSON, ignoring")
    
    client = InteractiveClient(client_id, name, server_url, profile)
    await client.run()
```

- [ ] **Step 5: Test the client manually**

Run: Start server first, then:
```bash
cd /Users/taoluo/projects/gcode/dooz/dooz_server
python test_clients/client_interactive.py Agent1 agent-001 "ws://localhost:8000" '{"name":"Agent1","role":"agent","skills":[["echo","Echo back input"],["ls","List directory"]],"supports_input":true,"supports_output":true}'
```
Expected: Client connects with profile, server should receive and store it

- [ ] **Step 6: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz/dooz_server && git add test_clients/client_interactive.py && git commit -m "feat: add profile support to interactive test client"
```

---

## Chunk 4: Validation and Edge Cases

### Task 5: Test Edge Cases and Validation

**Files:**
- Test: `dooz_server/tests/test_schemas.py`

- [ ] **Step 1: Write failing tests for edge cases**

```python
# Add to dooz_server/tests/test_schemas.py

def test_client_profile_empty_role():
    """Test that empty role fails validation."""
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        ClientProfile(name="Test", role="")


def test_client_profile_empty_name():
    """Test that empty name fails validation."""
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        ClientProfile(name="", role="agent")


def test_client_profile_whitespace_name():
    """Test that whitespace-only name fails validation."""
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        ClientProfile(name="   ", role="agent")


def test_client_profile_with_empty_skills():
    """Test that empty skills list is valid."""
    profile = ClientProfile(name="Test", role="agent", skills=[])
    assert profile.skills == []


def test_client_profile_with_skills():
    """Test skills list works correctly - list of tuples."""
    profile = ClientProfile(
        name="Test",
        role="agent",
        skills=[("cmd1", "Command 1 description"), ("cmd2", "Command 2 description")]
    )
    assert profile.skills == [("cmd1", "Command 1 description"), ("cmd2", "Command 2 description")]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_schemas.py::test_client_profile_empty_role -v`
Expected: FAIL (validation doesn't reject empty strings yet)

- [ ] **Step 3: Update ClientProfile to validate non-empty strings**

```python
# Modify ClientProfile in dooz_server/src/dooz_server/schemas.py

class ClientProfile(BaseModel):
    """Profile information for a registered client."""
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields, no strict validation
    
    name: str = Field(..., min_length=1, description="Client display name")
    role: str = Field(..., min_length=1, description="Client role (e.g., agent, user, service)")
    extra_info: Optional[str] = Field(default=None, description="Custom extra information")
    skills: list[tuple[str, str]] = Field(default_factory=list, description="List of (ability_name, ability_description) tuples")
    supports_input: bool = Field(default=False, description="Whether client supports input")
    supports_output: bool = Field(default=False, description="Whether client supports output")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/test_schemas.py -k "client_profile" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz/dooz_server && git add src/dooz_server/schemas.py tests/test_schemas.py && git commit -m "test: add edge case tests and validate non-empty fields"
```

---

## Chunk 5: Integration Tests

### Task 6: Run Full Test Suite

- [ ] **Step 1: Run all tests**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Run linting (if configured)**

Run: `cd /Users/taoluo/projects/gcode/dooz/dooz_server && python -m pytest tests/ -v --tb=short`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
cd /Users/taoluo/projects/gcode/dooz/dooz_server && git add -A && git commit -m "test: run full test suite for client profile feature"
```

---

## Summary

This plan adds a strongly-validated client profile schema to the dooz_server:

1. **ClientProfile schema** with required fields (name, role) and optional fields (extra_info, **skills**, supports_input, supports_output)
   - **skills** is `list[tuple[str, str]]` - each tuple is (ability_name, ability_description)
2. **Extra fields are ignored** - clients can pass additional fields without validation errors
3. **Updated ClientManager** to accept and store profile during registration
4. **Updated WebSocket endpoint** to accept profile via query parameter
5. **Updated Interactive test client** to support profile in connection
6. **Comprehensive tests** for schema validation, edge cases, and integration

The implementation follows TDD principles with small, verifiable steps.

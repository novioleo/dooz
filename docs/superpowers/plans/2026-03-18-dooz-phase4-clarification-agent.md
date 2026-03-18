# Phase 4: Clarification Agent Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Clarification Agent in CLI for multi-turn requirement clarification before sending tasks to the daemon. Rule-based with optional LLM enhancement.

**Architecture:** 
- ClarificationAgent class in CLI
- State machine for conversation flow
- Intent detection from user input
- Clarifying questions for ambiguous requests
- Integration with existing CLI WebSocket client

**Tech Stack:** Python, asyncio, re (regex for intent detection), optional: openai for LLM enhancement

---

## Chunk 1: Clarification Agent Core ✅ (Completed)

### Task 1.1: Clarification Agent State and Intent Models ✅

**Files:**
- Created: `dooz_cli/src/dooz_cli/clarification/state.py` (generic intent types)
- Created: `dooz_cli/src/dooz_cli/clarification/__init__.py`
- Tests: `dooz_cli/tests/test_clarification_state.py`

**Supported Intent Types (Generic):**
- `GET_INFO`, `LIST_ITEMS`, `GET_STATUS` - Information retrieval
- `CREATE`, `UPDATE`, `DELETE` - CRUD operations
- `EXECUTE_TASK`, `STOP_TASK` - Task execution
- `ENABLE`, `DISABLE`, `SET_VALUE` - Control operations
- `SEND_MESSAGE`, `READ_MESSAGE` - Communication
- `DOWNLOAD`, `UPLOAD` - File operations
- `HELP`, `UNKNOWN` - Special intents

**Status:** All tests passing (5 tests)

---

### Task 1.2: Intent Detection Engine ✅

**Files:**
- Created: `dooz_cli/src/dooz_cli/clarification/intent_detector.py`
- Tests: `dooz_cli/tests/test_intent_detector.py`

**Features:**
- Regex-based pattern matching for Chinese intent detection
- Entity extraction: target, name, scope
- Clarification triggers for missing required fields

**Status:** All tests passing (13 tests)

---

### Task 1.3: Clarification Question Generator ✅

**Files:**
- Created: `dooz_cli/src/dooz_cli/clarification/questions.py`
- Tests: `dooz_cli/tests/test_questions.py`

**Features:**
- Generic question templates for missing fields (target, name, value, recipient, scope)
- Dynamic confirmation message generation based on intent and entities

**Status:** All tests passing (10 tests)

---

## Chunk 2: Clarification Agent Integration

### Task 2.1: Main ClarificationAgent Class ✅

**Files:**
- Created: `dooz_cli/src/dooz_cli/clarification/agent.py`
- Tests: `dooz_cli/tests/test_clarification_agent.py`

**Status:** All tests passing (10 tests)

---

### Task 2.2: Integrate ClarificationAgent into CLI

**Files:**
- Modify: `dooz_cli/src/dooz_cli/cli.py`

- [ ] **Step 1: Write failing test for CLI with clarification**

```python
# tests/test_cli_clarification.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from dooz_cli.cli import DoozCLI


@pytest.mark.asyncio
async def test_cli_sends_to_daemon_after_clarification():
    """Test that CLI sends clarified request to daemon."""
    cli = DoozCLI("ws://localhost:8765")
    
    # Mock websocket client
    cli.client = Mock()
    cli.client.connect = AsyncMock(return_value=True)
    cli.client.send = AsyncMock(return_value=True)
    cli.client.disconnect = AsyncMock()
    
    # Process with clarification agent
    await cli.send_message_with_clarification("播放音乐")
    
    # Should have sent message
    cli.client.send.assert_called()


@pytest.mark.asyncio
async def test_cli_bypass_clarification_with_force():
    """Test bypassing clarification with --force flag."""
    cli = DoozCLI("ws://localhost:8765")
    
    # Mock websocket client
    cli.client = Mock()
    cli.client.connect = AsyncMock(return_value=True)
    cli.client.send = AsyncMock(return_value=True)
    cli.client.disconnect = AsyncMock()
    
    # Send with force flag
    await cli.send_message_with_clarification("播放音乐", force=True)
    
    # Should have sent immediately without clarification
    cli.client.send.assert_called()
```

- [ ] **Step 2: Run test**

Run: `cd dooz_cli && uv run pytest tests/test_cli_clarification.py -v`
Expected: FAIL - method doesn't exist

- [ ] **Step 3: Add clarification integration to CLI**

```python
# Add to cli.py
from .clarification import ClarificationAgent

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
        # ... existing code ...
    
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
```

- [ ] **Step 4: Run test**

Run: `cd dooz_cli && uv run pytest tests/test_cli_clarification.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dooz_cli/src/dooz_cli/cli.py dooz_cli/tests/test_cli_clarification.py
git commit -m "feat: integrate ClarificationAgent into CLI"
```

---

## Chunk 3: Optional LLM Enhancement (Future)

### Task 3.1: LLM-powered Clarification (Optional Enhancement)

**Files:**
- Create: `dooz_cli/src/dooz_cli/clarification/llm_enhancer.py`

**Note:** This is an optional enhancement for future implementation. The rule-based system should work well for MVP.

```python
# dooz_cli/src/dooz_cli/clarification/llm_enhancer.py
"""Optional LLM enhancement for clarification agent."""

from typing import Optional


class LLMClarificationEnhancer:
    """Uses LLM to enhance clarification when rules fail."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    async def clarify(self, user_input: str, context: dict) -> dict:
        """Use LLM to clarify user intent."""
        # TODO: Implement OpenAI API call
        pass
```

---

## Summary

After completing Phase 4, you will have:
- [x] ClarificationAgent with state management
- [x] Intent detection engine with generic regex patterns
- [x] Question generation for missing entities (target, name, value, recipient, scope)
- [x] CLI integration with clarification flow
- [x] Force flag to bypass clarification
- [ ] Optional LLM enhancement (future)

**Supported Intent Types (Generic - Not Limited to Smart Home):**
- Information: `get_info`, `list_items`, `get_status`
- CRUD: `create`, `update`, `delete`
- Tasks: `execute_task`, `stop_task`
- Control: `enable`, `disable`, `set_value`
- Communication: `send_message`, `read_message`
- Files: `download`, `upload`
- Special: `help`, `unknown`

**Total Tests:** 38 tests passing

**Implementation Complete!** The Clarification Agent can:
1. Detect generic intents from user input (not limited to any domain)
2. Ask clarifying questions for missing information (target, name, value, recipient, scope)
3. Generate confirmation messages dynamically
4. Send clarified requests to daemon
5. Handle max 3 turns before forcing completion
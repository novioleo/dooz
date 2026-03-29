---
name: dooz-cli-tui
description: Terminal UI for dooz with multi-fragment chat interface
status: backlog
created: 2026-03-29T13:29:39Z
---

# PRD: dooz-cli-tui

## Executive Summary

A terminal-based chat interface (TUI) for the dooz system, built with ratatui. The application provides a WeChat-style messaging experience with session management, persistent storage, and a modular fragment-based architecture designed for future extensibility.

## Problem Statement

Users need a terminal-based interface to interact with the dooz messaging system. The current system lacks a native TUI client, requiring users to either use web interfaces or raw API calls. This PRD defines the core TUI application with session management and chat functionality.

## User Stories

### As a user, I can:
1. Create a new chat session with `/new` command
2. Exit the program with `/exit` command
3. View my conversation history in a scrollable WeChat-style layout
4. Browse and resume previous sessions from the sidebar
5. Send messages and receive responses
6. Use mouse to scroll through chat history

### As a developer, I can:
1. Extend the application with new fragments
2. Add LLM-based session summarization in the future
3. Integrate with additional backends

## Functional Requirements

### Fragment Architecture
- **Multi-fragment design**: Application supports multiple fragments (panels/views)
- **Fragment1 (Chat Fragment)**: Primary chat interface with session management
- **Future fragments**: Architecture must support adding fragments without refactoring

### Session Management
- **Auto-create on start**: Program automatically creates a new session on startup
- **Create session**: `/new` command creates a new session (switches to it)
- **Exit program**: `/exit` command exits the entire application
- **Session storage**: Sessions stored in `.dooz/sessions/` directory
- **Session metadata**: Each session has `title` (timestamp initially), `created_at`, `updated_at`
- **Session content**: Messages stored as JSON array in session file

### Layout (Fragment1)
```
┌─────────────────────┬────────────────────────────────────┐
│                     │                                    │
│  Session List       │  Chat History                      │
│  (20% width)        │  (80% width, 80% height)          │
│                     │                                    │
│  - Session title    │  [Scrollable message area]         │
│  - Session time     │                                    │
│                     │                                    │
├─────────────────────┼────────────────────────────────────┤
│                     │  Input Area                        │
│                     │  (80% width, 20% height)          │
└─────────────────────┴────────────────────────────────────┘
```

### Chat Display
- **User messages**: Right-aligned, distinct color (e.g., cyan)
- **Received messages**: Left-aligned, distinct color (e.g., white/green)
- **Message bubble**: Clear visual separation
- **Timestamp**: Each message shows timestamp
- **Scroll behavior**: Mouse wheel scrolling in chat area

### Commands
- `/new`: Create and switch to new session
- `/exit`: Exit the entire program (not just the session)
- **Program startup**: Automatically creates a new session if no session exists

## Non-Functional Requirements

### Performance
- Startup time < 2 seconds
- Message rendering < 16ms (60fps)
- Session load time < 500ms

### Storage
- Session files: JSON format in `.dooz/sessions/`
- File naming: `{session_id}.json`
- No external database dependencies

### Architecture
- Rust with ratatui v0.30+
- TEA (The Elm Architecture) pattern
- Modular fragment system for extensibility

## Success Criteria

1. ✅ User can create a new session with `/new`
2. ✅ User can exit session with `/exit`
3. ✅ Session list shows all historical sessions with title and time
4. ✅ User can click a session to load and continue conversation
5. ✅ Chat history displays WeChat-style (user right/received left)
6. ✅ Different colors distinguish message types
7. ✅ Mouse scrolling works in chat area
8. ✅ Sessions persist across application restarts
9. ✅ Architecture supports future fragment addition

## Constraints & Assumptions

- Terminal must support UTF-8
- Minimum terminal size: 80x24
- Mouse support requires terminal to enable mouse events
- Future LLM summarization will be additive, not breaking

## Out of Scope

- LLM-based session title summarization (future enhancement)
- Additional fragments beyond Fragment1 (future work)
- Server-side persistence (relies on existing dooz server)
- Authentication UI (assumed handled by server)

## Dependencies

- ratatui v0.30+
- dooz-server for message relay (assumes running server)
- Session storage backend (filesystem)

## Technical Notes

### Session File Format
```json
{
  "id": "uuid",
  "title": "2026-03-29 10:30",
  "created_at": "2026-03-29T10:30:00Z",
  "updated_at": "2026-03-29T10:35:00Z",
  "messages": [
    {
      "id": "uuid",
      "role": "user|assistant",
      "content": "message text",
      "timestamp": "2026-03-29T10:30:00Z"
    }
  ]
}
```

### Fragment System Design
Each fragment is a self-contained module with:
- `Model`: Fragment state
- `update()`: State transition logic
- `view()`: Rendering logic
- `FragmentId`: Unique identifier for routing

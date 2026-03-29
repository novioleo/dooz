---
name: dooz-cli-tui
status: in-progress
created: 2026-03-29T13:34:57Z
updated: 2026-03-29T14:20:00Z
progress: 0%
prd: .claude/prds/dooz-cli-tui.md
github: https://github.com/novioleo/dooz/issues/1
---

# Epic: dooz-cli-tui

## Overview

A terminal-based chat TUI application built with ratatui, featuring WeChat-style messaging, session management, and a modular fragment-based architecture for future extensibility.

## Architecture Decisions

### TEA Pattern (The Elm Architecture)
- **Model**: Application state containing active fragment, session data, UI state
- **Message/Action**: User actions (key presses, mouse events, commands) trigger state changes
- **Update**: Pure function that transforms state based on messages
- **View**: Renders current state to terminal

### Fragment System
```
┌─────────────────────────────────────────────────────────────┐
│                         App                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Fragment Router                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │ Fragment1  │ │ Fragment2  │ │ FragmentN  │  (future)    │
│  │ (Chat)     │ │            │ │            │             │
│  └────────────┘ └────────────┘ └────────────┘             │
└─────────────────────────────────────────────────────────────┘
```
- Each fragment is a self-contained module with `Model`, `update()`, `view()`
- Fragment registry maps FragmentId → Fragment implementation
- Future fragments can be added without modifying existing code

### Session Storage
- Location: `.doz/sessions/` in program working directory
- Format: One JSON file per session
- Index: `sessions.json` for session list metadata

## Technical Approach

### Project Structure
```
dooz_cli/
├── Cargo.toml
├── src/
│   ├── main.rs              # Entry point, terminal setup
│   ├── app.rs               # App struct, main loop
│   ├── action.rs           # Action/Message enum
│   ├── fragments/
│   │   ├── mod.rs          # Fragment registry
│   │   ├── fragment.rs     # Fragment trait
│   │   └── chat/           # Fragment1: Chat interface
│   │       ├── mod.rs
│   │       ├── model.rs    # Chat state
│   │       ├── update.rs   # Chat update logic
│   │       └── view.rs     # Chat rendering
│   ├── session/
│   │   ├── mod.rs
│   │   ├── store.rs        # Session file I/O
│   │   └── types.rs       # Session, Message types
│   ├── ui/
│   │   ├── mod.rs
│   │   ├── layout.rs      # Main layout calculation
│   │   └── components.rs  # Shared UI components
│   └── tui.rs             # Terminal setup/utilities
```

### Dependencies
- `ratatui = "0.30"` - Terminal UI framework
- `crossterm = { version = "0.29", features = ["event-stream"] }` - Event handling
- `color-eyre = "0.6"` - Error handling
- `tokio = { version = "1", features = ["full"] }` - Async runtime
- `serde = { version = "1", features = ["derive"] }` - Serialization
- `serde_json = "1"` - JSON handling
- `uuid = { version = "1", features = ["v4", "serde"] }` - Session IDs
- `chrono = { version = "0.4", features = ["serde"] }` - Timestamps
- `dirs = "6"` - Directory utilities
- `tracing = "0.1"` - Logging
- `tracing-subscriber = { version = "0.3", features = ["env-filter"] }` - Log output

### Key Libraries
- ratatui v0.30+ uses `Layout` and `Rect` for UI composition
- `ScrollbarState` for scrollable message list
- `ListState` for session selection

## Implementation Strategy

### Phase 1: Project Setup
- Create Rust project with cargo
- Set up logging and error handling
- Configure ratatui terminal
- Implement basic TEA loop skeleton

### Phase 2: Session Storage
- Define Session, Message types with serde
- Implement session store (create, read, update, list)
- Auto-create `.doz/sessions/` directory
- Handle session index

### Phase 3: Fragment System
- Implement Fragment trait
- Create FragmentRegistry
- Wire up fragment routing in main loop

### Phase 4: Fragment1 (Chat)
- Build 3-panel layout (session list, chat area, input)
- Implement WeChat-style message rendering
- Add mouse scroll support
- Implement `/new` and `/exit` commands

### Phase 5: Integration
- Connect session storage to UI
- Test full user flow
- Add polish and error handling

## Task Breakdown Preview

1. **Project scaffolding** - Cargo project, dependencies, basic structure
2. **Session storage layer** - Types, store, file I/O
3. **Fragment trait & registry** - Modular fragment system
4. **Chat fragment - layout** - 3-panel UI structure
5. **Chat fragment - session list** - Left panel rendering & selection
6. **Chat fragment - message view** - Scrollable message area
7. **Chat fragment - input area** - User input handling
8. **Chat fragment - commands** - `/new`, `/exit` implementation
9. **Integration & polish** - Full integration testing

## Tasks Created

- [ ] 2.md - Project scaffolding (parallel: true)
- [ ] 3.md - Session storage layer (parallel: true)
- [ ] 4.md - Fragment trait and registry (parallel: true)
- [ ] 5.md - Chat fragment layout (parallel: false)
- [ ] 6.md - Chat fragment - session list (parallel: true)
- [ ] 7.md - Chat fragment - message view (parallel: true)
- [ ] 8.md - Chat fragment - input area (parallel: true)
- [ ] 9.md - Chat fragment - commands (parallel: false)
- [ ] 10.md - Integration and polish (parallel: false)

Total tasks: 9
Parallel tasks: 6
Sequential tasks: 3
Estimated total effort: 13-18 hours

## Dependencies

- ratatui v0.30+ (already using ratatui-tui skill)
- Existing dooz_server for message relay (assumed running)
- No external database (filesystem-based session storage)

## Success Criteria (Technical)

1. ✅ Cargo builds complete with `cargo build`
2. ✅ Application starts and displays TUI
3. ✅ Can create new session with `/new`
4. ✅ Can send messages (input area functional)
5. ✅ Messages display WeChat-style (user right, received left)
6. ✅ Mouse scrolling works in chat area
7. ✅ Session list shows historical sessions
8. ✅ Clicking session loads history
9. ✅ Sessions persist after restart
10. ✅ `/exit` terminates program cleanly
11. ✅ Architecture supports adding new fragments

## Estimated Effort

- Total tasks: 9
- Estimated: 2-3 days for initial implementation
- Future fragments: ~4 hours per fragment

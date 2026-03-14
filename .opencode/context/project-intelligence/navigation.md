<!-- Context: project-intelligence/nav | Priority: critical | Version: 2.0 | Updated: 2026-03-14 -->

# Project Intelligence

> Start here for quick project understanding. These files bridge business and technical domains.

## Structure

```
.opencode/context/project-intelligence/
├── navigation.md              # This file - quick overview
├── business-domain.md         # Business context and problem statement
├── technical-domain.md        # Stack, architecture, technical decisions
├── business-tech-bridge.md    # How business needs map to solutions
├── decisions-log.md           # Major decisions with rationale
└── living-notes.md            # Active issues, debt, open questions
```

## Quick Routes

### For dooz Project

| What You Need | File | Description |
|---------------|------|-------------|
| Tech stack & architecture | `technical-domain.md` | ROS2, Tailscale, Kotlin, Swift |
| Development setup | `technical-domain.md` | ROS2, Android, macOS SDK setup |
| Naming conventions | `technical-domain.md` | ROS2 packages, messages, services |
| MVP roadmap | `technical-domain.md` | Phase 1-3 milestones |

### General

| What You Need | File | Description |
|---------------|------|-------------|
| Understand the "why" | `business-domain.md` | Problem, users, value proposition |
| Understand the "how" | `technical-domain.md` | Stack, architecture, integrations |
| See the connection | `business-tech-bridge.md` | Business → technical mapping |
| Know the context | `decisions-log.md` | Why decisions were made |
| Current state | `living-notes.md` | Active issues and open questions |
| All of the above | Read all files in order | Full project intelligence |

---

## dooz Project Overview

**dooz** — AI-Friendly Hardware Module & System

> "One sentence — the device thinks, acts, checks, and reports by itself."

### Core Innovations

- **Dynamic Brain Election** — Intelligent leader election based on compute power, availability, task success
- **Distributed ReAct** — Direct device-to-device communication (no master-slave polling)
- **ROS2-Based Protocol** — Decentralized message exchange via ROS2 topics
- **Tailscale VPN** — Zero-config device discovery and secure mesh networking

### Tech Stack

| Component | Technology |
|-----------|------------|
| Protocol | ROS2 (Jazzy Jalisco / Humble) |
| Network | Tailscale |
| Core | C++ / Rust |
| Android | Kotlin 1.9.x |
| macOS | Swift 5.9+ |

### Project Location

```
dooz/
├── core/dooz_ros2/           # ROS2 packages (core, discovery, election, transport)
├── core/dooz_protocol/       # Protocol definitions (msg/srv/action)
├── clients/android/         # Kotlin SDK
├── clients/macos/           # Swift SDK
└── docs/                    # Documentation (dev/user/contributor)
```

---

## Usage

**New Team Member / Agent**:
1. Start with `navigation.md` (this file)
2. Read all files in order for complete understanding
3. Follow onboarding checklist in each file

**Quick Reference**:
- Business focus → `business-domain.md`
- Technical focus → `technical-domain.md`
- Decision context → `decisions-log.md`

**For dooz development**:
- Tech stack & setup → `technical-domain.md`
- Code patterns → Follow ROS2 conventions (see technical-domain.md)

---

## Integration

This folder is referenced from:
- `.opencode/context/core/standards/project-intelligence.md` (standards and patterns)
- `.opencode/context/core/system/context-guide.md` (context loading)
- `.opencode/context/projects/dooz.md` (project-specific context)

See `.opencode/context/core/context-system.md` for the broader context architecture.

---

## Maintenance

Keep this folder current:
- Update when business direction changes
- Document decisions as they're made
- Review `living-notes.md` regularly
- Archive resolved items from decisions-log.md

**Version**: 2.0 (2026-03-14) — Updated for dooz project

**Management Guide**: See `.opencode/context/core/standards/project-intelligence-management.md` for complete lifecycle management.

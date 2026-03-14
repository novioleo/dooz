# dooz Project Context

**Version**: 2.0  
**Last Updated**: 2026-03-14  
**Status**: Active Development (MVP Phase)

---

## Project Overview

**dooz** is a software-hardware integrated intelligent execution system. It transforms devices into sub-agents that collaborate dynamically without central control.

### Core Vision

> "One sentence — the device thinks, acts, checks, and reports by itself."

### Core Innovations

| Feature | Description |
|---------|-------------|
| **Dynamic Brain Election** | Intelligent leader election based on compute power, availability, and task success rate |
| **Distributed ReAct** | Devices communicate directly, eliminating master-slave polling inefficiency |
| **ROS2-Based Protocol** | Decentralized communication using ROS2 topics for efficient message exchange |
| **Tailscale VPN** | Zero-config device discovery and secure mesh networking |

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Protocol Layer | ROS2 | Jazzy Jalisco / Humble |
| Network | Tailscale | Latest |
| Core Language | C++ / Rust | C++17 / Rust 1.75+ |
| Android SDK | Kotlin | 1.9.x |
| macOS SDK | Swift | 5.9+ |
| Build | Colcon + CMake | Latest |

---

## Project Structure

```
dooz/
├── docs/
│   ├── dev/           # Development docs (architecture, design)
│   ├── user/          # User docs (Quick Start, usage)
│   └── contributor/  # Contributor guidelines
├── core/
│   ├── dooz_ros2/    # ROS2 packages
│   │   ├── dooz_core/       # Main orchestration
│   │   ├── dooz_discovery/  # Device discovery
│   │   ├── dooz_election/   # Brain election
│   │   └── dooz_transport/  # Message transport
│   └── dooz_protocol/      # Protocol definitions
│       ├── msg/      # ROS messages
│       ├── srv/      # ROS services
│       └── action/  # ROS actions
├── clients/
│   ├── android/     # Kotlin SDK
│   └── macos/       # Swift SDK
└── scripts/
    └── install/     # Installation scripts
```

---

## Code Standards

All code must follow:

1. **Modular Design** — Single responsibility, clear interfaces
2. **Functional Approach** — Pure functions, immutability
3. **Error Handling** — Graceful errors with context
4. **Security** — No hardcoded secrets, validate input

See `.opencode/context/core/standards/code-quality.md` for detailed standards.

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| ROS2 Packages | dooz_\<feature\> | dooz_discovery, dooz_election |
| ROS2 Nodes | dooz_\<feature\>_node | dooz_discovery_node |
| Messages | CamelCase | BrainElection.msg, DeviceInfo.msg |
| Services | CamelCase | GetDevices.srv |
| Files | lowercase_with_underscores | device_info.cpp |
| Functions | verbPhrase | discoverDevices() |

---

## MVP Milestones

| Milestone | Description | Status |
|-----------|-------------|--------|
| M1 | Project structure & README | ✅ Complete |
| M2 | ROS2 core framework | 🔄 In Progress |
| M3 | Device discovery service | ⏳ Pending |
| M4 | Dynamic brain election | ⏳ Pending |
| M5 | Android client SDK | ⏳ Pending |
| M6 | macOS client SDK | ⏳ Pending |

---

## Key Design Decisions

### Why ROS2?

- Truly decentralized (unlike MQTT)
- Topic mechanism ideal for device message exchange
- Mature ecosystem with strong community support

### Why Tailscale?

- Zero-config device discovery
- Built-in MagicDNS
- Automatic NAT traversal
- WireGuard-based (fast & secure)

### Why Dynamic Election?

- No single point of failure
- Optimizes resource usage
- Adapts to device capabilities

---

## Reference Links

- [ROS2 Documentation](https://docs.ros.org/en/jazzy/)
- [Tailscale Documentation](https://tailscale.com/kb/)
- [ROS2 DDS Communication](https://docs.ros.org/en/jazzy/Concepts/About-DDS.html)
- **Context Files**: See `.opencode/context/project-intelligence/technical-domain.md`

---

## Notes

- Phase 1 MVP focuses on device discovery + dynamic election
- No real-time audio/video in MVP
- Hardware module integration deferred to Phase 2+
- Project intelligence: See `.opencode/context/project-intelligence/`

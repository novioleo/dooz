<!-- Context: project-intelligence/technical | Priority: critical | Version: 2.0 | Updated: 2026-03-14 -->

# Technical Domain

> dooz technical foundation: ROS2-based distributed agent system with multi-platform SDKs.

## Quick Reference

- **Purpose**: Understand dooz architecture, tech stack, and development patterns
- **Update When**: Tech stack changes, new platforms, architecture decisions
- **Audience**: Developers building core framework, Android/iOS SDKs

---

## Primary Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| Protocol | ROS2 | Jazzy Jalisco / Humble | Decentralized message bus, mature ecosystem |
| Network | Tailscale | Latest | Zero-config VPN, MagicDNS, WireGuard-based |
| Core Language | C++ / Rust | C++17 / Rust 1.75+ | Performance-critical ROS2 nodes |
| Android SDK | Kotlin | 1.9.x | Native Android development |
| macOS SDK | Swift | 5.9+ | Native Apple platform development |
| Build | Colcon + CMake | Latest | ROS2 standard build tools |

---

## Architecture Pattern

```
Type: Agent-based distributed system (decentralized)
Pattern: Dynamic brain election with peer-to-peer communication
```

### Why This Architecture?

- **No single point of failure**: Dynamic brain election based on compute power + availability + success rate
- **Efficient communication**: Direct device-to-device messages via ROS2 topics (eliminates master-slave polling)
- **Scalable**: New devices auto-discover via Tailscale VPN mesh
- **Flexibility**: Brain node can be mobile, desktop, or cloud

---

## Project Structure

```
dooz/
├── docs/                          # Documentation
│   ├── dev/                       # Development docs (architecture, design)
│   ├── user/                      # User docs (Quick Start, usage)
│   └── contributor/               # Contributor guidelines
├── core/
│   ├── dooz_ros2/                 # ROS2 packages
│   │   ├── dooz_core/             # Main orchestration node
│   │   ├── dooz_discovery/        # Device discovery service
│   │   ├── dooz_election/         # Dynamic brain election
│   │   └── dooz_transport/        # Message transport service
│   └── dooz_protocol/            # Protocol definitions (msg/srv/action)
│       ├── msg/                   # ROS message definitions
│       ├── srv/                   # ROS service definitions
│       └── action/                # ROS action definitions
├── clients/
│   ├── android/                   # Kotlin SDK (dooz-client-android)
│   └── macos/                     # Swift SDK (dooz-client-macos)
└── scripts/
    └── install/                   # Installation scripts
```

---

## Key Technical Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| ROS2 over MQTT | Truly decentralized, topic-based pub/sub, native DDS support | Efficient many-to-many communication |
| Tailscale VPN | Zero-config discovery, MagicDNS, automatic NAT traversal | Devices auto-discover without manual setup |
| Dynamic Brain Election | Weighted ranking (compute + availability + success) | No fixed master, adapts to device capabilities |
| Distributed ReAct | Each device tracks action三元组 (done/doing/next) | Eliminates polling, enables proactive notifications |
| Memory per Device | Each sub-agent stores data locally, exposes via skills | Privacy-preserving, no central data store |

---

## Integration Points

| System | Purpose | Protocol | Direction |
|--------|---------|----------|-----------|
| Tailscale Network | Device discovery, P2P communication | WireGuard | Internal |
| ROS2 DDS | Message exchange between nodes | DDS/RTPS | Internal |
| Android Client | Mobile SDK for Android devices | ROS2 + Tailscale SDK | Outbound |
| macOS Client | Desktop SDK for Apple devices | ROS2 + Tailscale SDK | Outbound |

---

## Development Environment

### ROS2 Setup (Ubuntu 22.04+)

```bash
# Install ROS2 Jazzy
sudo apt update
sudo apt install ros-jazzy-desktop

# Setup workspace
mkdir -p ~/dooz_ws/src
cd ~/dooz_ws
source /opt/ros/jazzy/setup.bash

# Clone and build
colcon build --packages-select dooz_protocol dooz_discovery dooz_election dooz_transport dooz_core
```

### Android SDK

```bash
# Requires Android Studio or gradle
cd clients/android
./gradlew build
```

### macOS SDK

```bash
# Requires Xcode
cd clients/macos
xcodebuild -scheme dooz-client-macos
```

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| ROS2 Packages | dooz_\<feature\> | dooz_discovery, dooz_election |
| ROS2 Nodes | dooz_\<feature\>_node | dooz_discovery_node |
| Messages | CamelCase.msg | BrainElection.msg, DeviceInfo.msg |
| Services | CamelCase.srv | GetDevices.srv, RegisterDevice.srv |
| Files | lowercase_with_underscores.cpp | device_info.cpp, discovery_client.cpp |
| Functions | verbPhrase | discoverDevices(), registerClient() |

---

## MVP Milestones

| Milestone | Status | Description |
|-----------|--------|-------------|
| M1 | ✅ Complete | Project structure, README |
| M2 | 🔄 In Progress | ROS2 core framework |
| M3 | ⏳ Pending | Device discovery service |
| M4 | ⏳ Pending | Dynamic brain election |
| M5 | ⏳ Pending | Android client SDK |
| M6 | ⏳ Pending | macOS client SDK |

---

## Related Files

- `business-domain.md` - Business vision and problem statement
- `business-tech-bridge.md` - How business needs map to technical solutions
- `decisions-log.md` - Full decision history

# dooz

**AI-Friendly Hardware Module & System**

> "One sentence — the device thinks, acts, checks, and reports by itself."

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![ROS2](https://img.shields.io/badge/ROS2-Jazzy%20Jalisco-brightgreen)](https://docs.ros.org/en/jazzy/)
[![Status](https://img.shields.io/badge/Status-Concept-orange)]()

---

## Overview

dooz is a **software-hardware integrated intelligent execution system** that seamlessly connects devices, software, and terminals around human needs. Instead of manual pairing, complex rule configuration, or central server polling — users simply speak to dooz, and the entire ecosystem executes the task autonomously.

### Core Vision

Transform every device into a **sub-agent** that collaborates dynamically without central control. Each device (hardware module, mobile app, desktop software, cloud service) operates as an intelligent entity, with a dynamically elected "brain node" coordinating task distribution and execution.

### Key Innovations

| Feature | Description |
|---------|-------------|
| **Dynamic Brain Election** | Intelligent leader election based on compute power, availability, and task success rate |
| **Distributed ReAct** | Devices communicate directly, eliminating master-slave polling inefficiency |
| **ROS2-Based Protocol** | Decentralized communication using ROS2 topics for efficient message exchange |
| **Tailscale VPN** | Zero-config device discovery and secure mesh networking |

---

## Architecture

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      dooz System                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Android    │  │    macOS    │  │    Linux/C++        │ │
│  │   Client    │  │   Client    │  │      Client         │ │
│  │  (Kotlin)   │  │   (Swift)   │  │     (Future)        │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                 │                      │            │
│         └─────────────────┼──────────────────────┘            │
│                           │                                   │
│                    ┌──────▼──────┐                             │
│                    │   ROS2      │                             │
│                    │   Core      │                             │
│                    │  Framework  │                             │
│                    └──────┬──────┘                             │
│                           │                                   │
│         ┌─────────────────┼─────────────────┐                 │
│         │                 │                 │                  │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐          │
│  │  Discovery  │  │  Election   │  │  Transport  │          │
│  │  Service    │  │   Service   │  │   Service   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Tailscale VPN (Network Layer)             │ │
│  │         Auto-discovery • Encrypted • Mesh             │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Components

#### Core Framework (`core/`)
- **dooz_ros2/** — ROS2 package containing core services
  - `dooz_core/` — Main node orchestration
  - `dooz_discovery/` — Device discovery service
  - `dooz_election/` — Dynamic brain election service
  - `dooz_transport/` — Message transport service
- **dooz_protocol/** — Protocol definitions (msg/srv/action)

#### Client SDKs (`clients/`)
- **android/** — Kotlin SDK for Android
- **macos/** — Swift SDK for macOS/iOS
- **linux/** — C++ SDK (planned)

---

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Protocol** | ROS2 | Jazzy Jalisco / Humble |
| **Network** | Tailscale | Latest |
| **Language (Core)** | C++ / Rust | C++17 / Rust 1.75+ |
| **Language (Android)** | Kotlin | 1.9.x |
| **Language (macOS)** | Swift | 5.9+ |
| **Build System** | Colcon + CMake | Latest |

---

## Quick Start

### Prerequisites

- ROS2 installed (Jazzy Jalisco or Humble Hawksbill recommended)
- Tailscale account
- For development: Ubuntu 22.04+ or macOS 13+

### Installation

```bash
# 1. Clone repository
git clone https://github.com/your-org/dooz.git
cd dooz

# 2. Install ROS2 dependencies
./scripts/install/install-ros2-dependencies.sh

# 3. Install Tailscale
./scripts/install/install-tailscale.sh

# 4. Build ROS2 packages
source /opt/ros/jazzy/setup.bash
colcon build --packages-select dooz_protocol dooz_discovery dooz_election dooz_transport dooz_core

# 5. Run demo
ros2 launch dooz_core demo_launch.py
```

### Android Quick Start

See [clients/android/README.md](clients/android/README.md)

### macOS Quick Start

See [clients/macos/README.md](clients/macos/README.md)

---

## Documentation

| Guide | Description |
|-------|-------------|
| [docs/dev/](./docs/dev/) | Development documentation (architecture, design) |
| [docs/user/](./docs/user/) | User documentation (Quick Start, usage) |
| [docs/contributor/](./docs/contributor/) | Contributor guidelines |

---

## MVP Roadmap

### Phase 1: Core Infrastructure (Current)
- [x] Project structure established
- [ ] ROS2 core framework
- [ ] Device discovery service
- [ ] Dynamic brain election service
- [ ] Android client SDK
- [ ] macOS client SDK

### Phase 2: Production Ready
- [ ] Full protocol implementation
- [ ] Memory system for sub-agents
- [ ] Skill management system
- [ ] Cross-platform testing

### Phase 3: Ecosystem Expansion
- [ ] Linux client (C++)
- [ ] Hardware module firmware
- [ ] IoT device integration
- [ ] Cloud backup brain

---

## Why dooz?

### Current Pain Points

| Problem | dooz Solution |
|---------|----------------|
| **Sensors only execute, no feedback** | Every device observes and reports results |
| **Complex protocol integration** | ROS2-based standardized protocol |
| **Limited edge compute** | Brain node offloads heavy AI processing |
| **Centralized polling inefficiency** | Direct device-to-device communication |

### Comparison with Existing Solutions

| Feature | dooz | OpenCV/OpenCLAW | Traditional IoT |
|---------|------|-----------------|------------------|
| Centralized Control | ❌ Decentralized | Partial | ✅ |
| Dynamic Brain Election | ✅ | ❌ | ❌ |
| Direct Device Communication | ✅ | ❌ | ❌ |
| ROS2-Based | ✅ | ❌ | ❌ |
| Zero-Config Discovery | ✅ (Tailscale) | ❌ | Partial |

---

## Contributing

We welcome contributions! Please see [docs/contributor/CONTRIBUTING.md](docs/contributor/CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality
5. Submit a pull request

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

## Contact

- Website: [dooz.ai](https://dooz.ai) (coming soon)
- Issues: [GitHub Issues](https://github.com/your-org/dooz/issues)
- Discussion: [GitHub Discussions](https://github.com/your-org/dooz/discussions)

---

**dooz — Let every device become a true sub-agent, making AI truly "for people, by people, and understanding people."**

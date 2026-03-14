# User Documentation

This directory contains user-facing documentation for dooz.

## Contents

- [Quick Start](./quick-start.md) — Get started in 5 minutes
- [Installation](./installation.md) — Detailed installation guide
- [Troubleshooting](./troubleshooting.md) — Common issues and solutions

## Quick Start

### 1. Install Tailscale

Download and install Tailscale from [tailscale.com](https://tailscale.com)

### 2. Set Up ROS2

```bash
# Install ROS2 (Jazzy Jalisco recommended)
sudo apt update
sudo apt install ros-jazzy-desktop
```

### 3. Build & Run

```bash
# Build the project
source /opt/ros/jazzy/setup.bash
colcon build

# Run the demo
ros2 launch dooz_core demo_launch.py
```

### 4. Connect Your Device

1. Install the dooz client for your platform
2. Sign in with your Tailscale account
3. Devices will auto-discover each other

## Support

For issues, see [Troubleshooting](./troubleshooting.md) or file a GitHub issue.

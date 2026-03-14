#!/bin/bash
# scripts/vpn/start_vpn.sh - 启动 Headscale VPN

set -e

echo "Starting Headscale VPN..."

# 检查 docker 是否运行
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

# 检查 headscale 是否已存在
if docker ps -a --format '{{.Names}}' | grep -q "^headscale$"; then
    echo "Headscale container already exists"
    
    if docker ps --format '{{.Names}}' | grep -q "^headscale$"; then
        echo "Headscale is already running"
    else
        echo "Starting existing Headscale container..."
        docker start headscale
    fi
else
    echo "Creating and starting Headscale container..."
    docker run -d --name headscale \
        --volume "$(pwd)/headscale:/var/lib/headscale" \
        --volume "$(pwd)/headscale/config.yaml:/etc/headscale.yml" \
        -p 8080:8080 \
        headscale/headscale \
        serve &
        
    sleep 3
fi

echo ""
echo "Headscale started!"
echo "Access UI at: http://localhost:8080"
echo ""
echo "To connect clients, run:"
echo "  tailscaled --tun=headscale0 --login-server=http://localhost:8080"

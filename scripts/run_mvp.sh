#!/bin/bash
# scripts/run_mvp.sh - 一键启动 5 个客户端

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_DIR/config"

echo "Starting dooz MVP..."

# 检查配置文件
for config in computer phone speaker tv light; do
    if [ ! -f "$CONFIG_DIR/${config}.yaml" ]; then
        echo "Error: Config file not found: $CONFIG_DIR/${config}.yaml"
        exit 1
    fi
done

# 启动 5 个客户端 (后台运行)
echo "Starting Computer (Brain)..."
python -m client.main --config "$CONFIG_DIR/computer.yaml" --brain &
PID_COMPUTER=$!

sleep 1

echo "Starting Phone..."
python -m client.main --config "$CONFIG_DIR/phone.yaml" &
PID_PHONE=$!

sleep 1

echo "Starting Speaker..."
python -m client.main --config "$CONFIG_DIR/speaker.yaml" &
PID_SPEAKER=$!

sleep 1

echo "Starting TV..."
python -m client.main --config "$CONFIG_DIR/tv.yaml" &
PID_TV=$!

sleep 1

echo "Starting Light..."
python -m client.main --config "$CONFIG_DIR/light.yaml" &
PID_LIGHT=$!

echo ""
echo "All clients started!"
echo "Computer PID: $PID_COMPUTER"
echo "Phone PID: $PID_PHONE"
echo "Speaker PID: $PID_SPEAKER"
echo "TV PID: $PID_TV"
echo "Light PID: $PID_LIGHT"
echo ""
echo "Press Ctrl+C to stop all clients"

# 等待中断
trap "kill $PID_COMPUTER $PID_PHONE $PID_SPEAKER $PID_TV $PID_LIGHT 2>/dev/null; exit" INT TERM

wait

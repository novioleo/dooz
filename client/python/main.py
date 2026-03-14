"""Client 入口."""

import asyncio
import yaml
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client.python.client import Client


async def main():
    config_path = os.path.join(os.path.dirname(__file__), "config/devices/computer.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    client = Client(config)
    
    client.on("task/dispatch", lambda msg: print(f"[DISPATCH] Task: {msg.get('skill_name')}, Params: {msg.get('parameters')}"))
    client.on("task/notify", lambda msg: print(f"[NOTIFY] {msg.get('message')}"))
    client.on("device/announce", lambda msg: print(f"[ANNOUNCE] {msg.get('device', {}).get('name')}"))
    
    print(f"Connecting as {config['device']['id']}...")
    try:
        if not await client.connect():
            print("Failed to connect!")
            return
    except Exception as e:
        print(f"Connection error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("Connected! Sending test request...")
    
    # 发送测试请求
    await asyncio.sleep(1)
    await client.send_request("开灯")
    
    # 保持运行
    await asyncio.sleep(5)
    await client.disconnect()
    print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())

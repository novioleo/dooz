"""Client 入口."""

import asyncio
import yaml
from client.python.client import Client


async def main():
    with open("config/devices/computer.yaml") as f:
        config = yaml.safe_load(f)
    
    client = Client(config)
    
    client.on("task/dispatch", lambda msg: print(f"Task: {msg.get('skill_name')}"))
    client.on("task/notify", lambda msg: print(f"Notify: {msg.get('message')}"))
    
    if not await client.connect():
        return
    
    asyncio.create_task(client.loop())
    
    await asyncio.sleep(1)
    await client.send_request("开灯")
    
    await asyncio.sleep(10)
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

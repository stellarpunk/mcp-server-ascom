#!/usr/bin/env python3
"""
Simple test for ASCOM device discovery
"""

import os
os.environ["ASCOM_KNOWN_DEVICES"] = "localhost:5555:seestar_alp"

import asyncio
from ascom_mcp.devices.manager import DeviceManager


async def test_discovery():
    print("Testing ASCOM discovery...")
    print(f"ASCOM_KNOWN_DEVICES: {os.environ.get('ASCOM_KNOWN_DEVICES')}")
    
    manager = DeviceManager()
    await manager.initialize()
    
    # The manager should find known devices immediately
    print(f"Available devices: {list(manager._available_devices.keys())}")
    
    # Test discovery
    devices = await manager.discover_devices(timeout=2.0)
    print(f"Discovered {len(devices)} devices:")
    for device in devices:
        print(f"  - {device.id}: {device.name} ({device.type})")
    
    await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(test_discovery())
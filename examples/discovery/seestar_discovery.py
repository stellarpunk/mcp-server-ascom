#!/usr/bin/env python3
"""Test Seestar discovery with known devices."""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ascom_mcp.devices.manager import DeviceManager
from ascom_mcp.logging import StructuredLogger

logger = StructuredLogger("test")


async def test_discovery():
    """Test device discovery including known devices."""
    print("Testing ASCOM device discovery...")
    print(f"ASCOM_KNOWN_DEVICES: {os.getenv('ASCOM_KNOWN_DEVICES', 'not set')}")
    
    # Initialize device manager
    manager = DeviceManager()
    await manager.initialize()
    
    try:
        # Discover devices
        devices = await manager.discover_devices(timeout=3.0)
        
        print(f"\nFound {len(devices)} devices:")
        for device in devices:
            print(f"  - {device.name} ({device.type}) at {device.host}:{device.port}")
            print(f"    ID: {device.id}")
            print(f"    Unique ID: {device.unique_id}")
        
        # Check if we found Seestar
        seestar = next((d for d in devices if "seestar" in d.name.lower()), None)
        if seestar:
            print(f"\n✅ Successfully discovered Seestar: {seestar.name}")
            
            # Try to connect
            print(f"\nConnecting to {seestar.id}...")
            connected = await manager.connect_device(seestar.id)
            print(f"✅ Connected to {connected.info.name}")
            
            # Get telescope info
            telescope = connected.client
            print(f"\nTelescope info:")
            print(f"  Description: {telescope.Description}")
            print(f"  Driver Info: {telescope.DriverInfo}")
            print(f"  Can Slew: {telescope.CanSlew}")
            
            # Disconnect
            await manager.disconnect_device(seestar.id)
            print(f"\n✅ Disconnected successfully")
        else:
            print("\n❌ Seestar not found in discovered devices")
            
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(test_discovery())
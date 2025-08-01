#!/usr/bin/env python3
"""Test v0.4.0 direct connection features with real Seestar."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ascom_mcp.devices.manager import DeviceManager
from ascom_mcp.devices.device_resolver import DeviceResolver


async def test_connection_string_parsing():
    """Test that connection strings parse correctly."""
    print("Testing connection string parsing...")
    
    test_cases = [
        "seestar@192.168.1.100:5555",
        "seestar@seestar.local:5555",
        "192.168.1.100:5555",  # No name
        "telescope_1",  # Not a connection string
    ]
    
    for test in test_cases:
        result = DeviceResolver.parse_connection_string(test)
        print(f"  '{test}' -> {result}")
    print()


async def test_direct_connection():
    """Test direct connection without discovery."""
    print("Testing direct connection to real Seestar...")
    
    manager = DeviceManager()
    
    # Test connection strings
    connection_strings = [
        "seestar@seestar.local:5555",
        # Add your actual Seestar IP here:
        # "seestar@192.168.1.100:5555",
    ]
    
    for conn_str in connection_strings:
        print(f"\nTrying: {conn_str}")
        try:
            device = await manager.connect_device(conn_str)
            print(f"  ✅ Connected! Device ID: {device.device_id}")
            
            # Test basic info
            info = device.device.Description()
            print(f"  Description: {info}")
            
            # Disconnect
            await manager.disconnect_device(device.device_id)
            print(f"  ✅ Disconnected")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")


async def test_state_persistence():
    """Test that discovered devices persist."""
    print("\nTesting state persistence...")
    
    from ascom_mcp.devices.state_persistence import DeviceStatePersistence
    
    persistence = DeviceStatePersistence()
    devices = persistence.load_devices()
    
    print(f"Found {len(devices)} saved devices:")
    for device in devices:
        print(f"  - {device.name} @ {device.host}:{device.port}")


async def main():
    """Run all tests."""
    print("=== v0.4.0 Direct Connection Tests ===\n")
    
    await test_connection_string_parsing()
    await test_direct_connection()
    await test_state_persistence()
    
    print("\n✅ Tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
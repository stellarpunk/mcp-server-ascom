#!/usr/bin/env python3
"""
Test end-to-end MCP flow with simulator
"""

import asyncio
import json
import sys
from typing import Dict, Any

# For this test, we'll use the direct Python API
# In real usage, this would go through Claude's MCP interface
from ascom_mcp.devices.manager import DeviceManager
from ascom_mcp.tools.discovery import DiscoveryTools
from ascom_mcp.tools.telescope import TelescopeTools


async def test_mcp_flow():
    """Test complete MCP flow from discovery to control"""
    print("=== MCP End-to-End Test ===\n")
    
    # Initialize device manager
    manager = DeviceManager()
    await manager.initialize()
    
    # Create tools
    discovery = DiscoveryTools(manager)
    telescope = TelescopeTools(manager)
    
    # Step 1: Discover devices
    print("1. Discovering ASCOM devices...")
    result = await discovery.discover_devices(timeout=5.0)
    print(f"   Found {len(result['devices'])} devices:")
    for device in result['devices']:
        print(f"   - {device['name']} ({device['type']}) at {device['host']}:{device['port']}")
    print()
    
    # Step 2: Get device info
    if result['devices']:
        device_id = result['devices'][0]['id']
        print(f"2. Getting info for device: {device_id}")
        info = await discovery.get_device_info(device_id)
        print(f"   Device: {info['device']['name']}")
        print(f"   Type: {info['device']['type']}")
        print(f"   Status: {'Connected' if info['device'].get('connected') else 'Not connected'}")
        print()
        
        # Step 3: Connect to telescope
        if info['device']['type'] == 'Telescope':
            print("3. Connecting to telescope...")
            connect_result = await telescope.connect(device_id)
            if connect_result['success']:
                print("   ✓ Connected successfully!")
                print(f"   Can slew: {connect_result['telescope']['can_slew']}")
                print(f"   Can park: {connect_result['telescope']['can_park']}")
                print()
                
                # Step 4: Get current position
                print("4. Getting current position...")
                pos_result = await telescope.get_position(device_id)
                if pos_result['success']:
                    print(f"   RA: {pos_result['position']['ra_hours']}h")
                    print(f"   Dec: {pos_result['position']['dec_degrees']}°")
                    print(f"   Alt: {pos_result['position'].get('altitude', 'N/A')}°")
                    print(f"   Az: {pos_result['position'].get('azimuth', 'N/A')}°")
                print()
                
                # Step 5: Custom action - check mount status
                print("5. Checking mount status...")
                try:
                    custom_result = await telescope.custom_action(
                        device_id,
                        "method_sync",
                        {"method": "get_device_state"}
                    )
                    if custom_result['success']:
                        mount_info = custom_result['result'].get('mount', {})
                        print(f"   Mount closed: {mount_info.get('close', 'Unknown')}")
                        print(f"   Tracking: {mount_info.get('tracking', 'Unknown')}")
                except Exception as e:
                    print(f"   Custom action not supported: {e}")
                print()
                
                # Step 6: Disconnect
                print("6. Disconnecting...")
                disconnect_result = await telescope.disconnect(device_id)
                if disconnect_result['success']:
                    print("   ✓ Disconnected successfully!")
            else:
                print(f"   ✗ Connection failed: {connect_result.get('error', 'Unknown error')}")
        else:
            print("   Device is not a telescope, skipping connection test")
    else:
        print("No devices found. Is seestar_alp running?")
    
    # Cleanup
    await manager.shutdown()
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_mcp_flow())
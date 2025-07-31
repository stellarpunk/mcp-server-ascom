#!/usr/bin/env python3
"""
Example: Controlling Seestar S50 through ASCOM MCP.

This demonstrates how to connect to and control a Seestar S50 telescope
using the ASCOM MCP Server.

Prerequisites:
1. seestar_alp must be running (http://localhost:5555)
2. Set ASCOM_KNOWN_DEVICES environment variable
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ascom_mcp.devices.manager import DeviceManager
from ascom_mcp.tools.telescope import TelescopeTools
from ascom_mcp.logging import StructuredLogger

logger = StructuredLogger("seestar_example")


async def main():
    """Main example demonstrating Seestar control."""
    print("=== Seestar S50 ASCOM Control Example ===\n")
    
    # Ensure known devices is set
    if not os.getenv('ASCOM_KNOWN_DEVICES'):
        os.environ['ASCOM_KNOWN_DEVICES'] = 'localhost:5555:seestar_alp'
        print("Set ASCOM_KNOWN_DEVICES=localhost:5555:seestar_alp\n")
    
    # Initialize device manager
    manager = DeviceManager()
    await manager.initialize()
    telescope_tools = TelescopeTools(manager)
    
    try:
        # 1. Discover devices
        print("1. Discovering ASCOM devices...")
        devices = await manager.discover_devices(timeout=3.0)
        print(f"   Found {len(devices)} devices")
        
        # Find Seestar
        seestar = None
        for device in devices:
            print(f"   - {device.name} ({device.type}) at {device.host}:{device.port}")
            if "seestar" in device.name.lower():
                seestar = device
        
        if not seestar:
            print("\n❌ Seestar not found! Make sure seestar_alp is running.")
            return
        
        print(f"\n✅ Found Seestar: {seestar.name} (ID: {seestar.id})")
        
        # 2. Connect to Seestar
        print("\n2. Connecting to Seestar...")
        result = await telescope_tools.connect(seestar.id)
        if result['success']:
            print(f"   ✅ {result['message']}")
            telescope = result['telescope']
            print(f"   Description: {telescope['description']}")
            print(f"   Driver: {telescope['driver_info']}")
        else:
            print(f"   ❌ {result['message']}")
            return
        
        # 3. Get current position
        print("\n3. Getting current position...")
        result = await telescope_tools.get_position(seestar.id)
        if result['success']:
            pos = result['position']
            status = result['status']
            print(f"   RA: {pos['ra_hours']:.3f}h ({pos.get('ra_hms', 'N/A')})")
            print(f"   Dec: {pos['dec_degrees']:.2f}° ({pos.get('dec_dms', 'N/A')})")
            if pos.get('altitude') is not None:
                print(f"   Alt: {pos['altitude']:.2f}°")
            if pos.get('azimuth') is not None:
                print(f"   Az: {pos['azimuth']:.2f}°")
            print(f"   Tracking: {status.get('tracking', 'Unknown')}")
        
        # 4. Demonstrate custom Seestar actions
        print("\n4. Seestar-specific commands...")
        
        # Get focus position
        print("\n   Getting focus position...")
        result = await telescope_tools.custom_action(
            seestar.id, 
            "method_sync",
            {"method": "get_focuser_position"}
        )
        if result['success']:
            print(f"   Current focus position: {result['result']}")
        
        # List available presets
        print("\n   Getting available presets...")
        result = await telescope_tools.custom_action(
            seestar.id,
            "list_presets"
        )
        if result['success'] and isinstance(result['result'], dict):
            presets = result['result'].get('presets', {})
            if presets:
                print("   Available presets:")
                for preset_id, preset_info in presets.items():
                    print(f"   - {preset_id}: {preset_info}")
        
        # Example: Move telescope (Seestar uses reversed controls)
        print("\n5. Movement example (3 seconds east = move view up)...")
        print("   Note: Seestar movement is counterintuitive:")
        print("   - North/South (0°/180°) = horizontal panning")
        print("   - East/West (90°/270°) = vertical movement")
        
        # Move east (90°) for 3 seconds at speed 300 - this moves view UP
        result = await telescope_tools.custom_action(
            seestar.id,
            "method_sync",
            {
                "method": "scope_speed_move",
                "params": {
                    "speed": 300,
                    "angle": 90,  # East = move view up
                    "dur_sec": 3
                }
            }
        )
        if result['success']:
            print("   ✅ Movement command sent")
            await asyncio.sleep(3.5)  # Wait for movement to complete
        
        # 6. Disconnect
        print("\n6. Disconnecting...")
        result = await telescope_tools.disconnect(seestar.id)
        if result['success']:
            print(f"   ✅ {result['message']}")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"\n❌ Error: {e}")
    
    finally:
        await manager.shutdown()
        print("\n=== Example Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
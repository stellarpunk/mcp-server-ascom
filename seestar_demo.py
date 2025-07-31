#!/usr/bin/env python3
"""
Seestar S50 Demo - Complete workflow demonstration.

This script demonstrates the full integration:
1. MCP Server discovers seestar_alp
2. Connects to Seestar S50 
3. Controls telescope (focus, movement)
4. Shows what works and current limitations
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ascom_mcp.devices.manager import DeviceManager
from ascom_mcp.tools.telescope import TelescopeTools

async def demo():
    print("=" * 60)
    print("SEESTAR S50 DEMONSTRATION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Ensure seestar_alp is configured
    os.environ['ASCOM_KNOWN_DEVICES'] = 'localhost:5555:seestar_alp'
    
    # Initialize
    manager = DeviceManager()
    await manager.initialize()
    telescope_tools = TelescopeTools(manager)
    
    try:
        # 1. DISCOVERY
        print("1. DEVICE DISCOVERY")
        print("-" * 40)
        devices = await manager.discover_devices(timeout=3.0)
        
        seestar = None
        for device in devices:
            print(f"✓ Found: {device.name}")
            print(f"  Type: {device.type}")
            print(f"  Location: {device.host}:{device.port}")
            print(f"  ID: {device.id}")
            if "seestar" in device.name.lower():
                seestar = device
        
        if not seestar:
            print("\n❌ ERROR: Seestar not found!")
            print("   Make sure seestar_alp is running on localhost:5555")
            return
        
        print(f"\n✅ Seestar ready for control")
        
        # 2. CONNECTION
        print("\n2. CONNECTION")
        print("-" * 40)
        result = await telescope_tools.connect(seestar.id)
        if result['success']:
            print(f"✓ Connected successfully")
            telescope = result['telescope']
            print(f"  Description: {telescope['description']}")
            print(f"  Driver Info: {telescope.get('driver_info', 'N/A')}")
        else:
            print(f"❌ Connection failed: {result['message']}")
            return
        
        # 3. POSITION & STATUS
        print("\n3. CURRENT STATUS")
        print("-" * 40)
        result = await telescope_tools.get_position(seestar.id)
        if result['success']:
            pos = result['position']
            status = result['status']
            print(f"✓ Position:")
            print(f"  RA: {pos['ra_hours']:.3f}h ({pos.get('ra_hms', 'N/A')})")
            print(f"  Dec: {pos['dec_degrees']:.2f}° ({pos.get('dec_dms', 'N/A')})")
            print(f"  Alt: {pos.get('altitude', 0):.2f}° (Note: May show 0 when parked)")
            print(f"  Az: {pos.get('azimuth', 0):.2f}°")
            print(f"  Tracking: {status.get('tracking', 'Unknown')}")
        
        # 4. FOCUS CONTROL
        print("\n4. FOCUS CONTROL")
        print("-" * 40)
        
        # Get current focus
        result = await telescope_tools.custom_action(
            seestar.id, 
            "method_sync",
            {"method": "get_focuser_position"}
        )
        if result['success']:
            current_focus = result['result'].get('result', 'Unknown')
            print(f"✓ Current focus position: {current_focus}")
            
            # Set new focus
            new_focus = 1500
            print(f"  Setting focus to {new_focus}...")
            result = await telescope_tools.custom_action(
                seestar.id,
                "method_sync",
                {
                    "method": "set_focuser_position",
                    "params": {"position": new_focus}
                }
            )
            if result['success']:
                print(f"  ✅ Focus set successfully")
        
        # 5. MOVEMENT DEMONSTRATION
        print("\n5. MOVEMENT CONTROL")
        print("-" * 40)
        print("⚠️  Seestar movement is counterintuitive:")
        print("   - North/South (0°/180°) = Horizontal panning")
        print("   - East/West (90°/270°) = Vertical movement")
        print()
        
        movements = [
            ("UP", 90, "East"),      # Move view up
            ("RIGHT", 0, "North"),   # Pan view right
        ]
        
        for direction, angle, compass in movements:
            print(f"✓ Moving {direction} (using {compass} = {angle}°)")
            result = await telescope_tools.custom_action(
                seestar.id,
                "method_sync",
                {
                    "method": "scope_speed_move",
                    "params": {
                        "speed": 300,
                        "angle": angle,
                        "dur_sec": 2
                    }
                }
            )
            if result['success']:
                print(f"  Movement command sent")
                await asyncio.sleep(2.5)  # Wait for movement
        
        # 6. KNOWN LIMITATIONS
        print("\n6. CURRENT LIMITATIONS")
        print("-" * 40)
        print("❌ Park/Unpark - Not implemented in seestar_alp")
        print("❌ Altitude/Azimuth - May not update in real-time")
        print("❌ Presets - list_presets not working (use goto_preset)")
        print("❌ Slewing - Standard ASCOM slew commands not implemented")
        print("✓ Working: Focus, Movement, Position reading, Connection")
        
        # 7. DISCONNECT
        print("\n7. CLEANUP")
        print("-" * 40)
        result = await telescope_tools.disconnect(seestar.id)
        if result['success']:
            print("✓ Disconnected successfully")
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE - Seestar S50 integration working!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ DEMO ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await manager.shutdown()

if __name__ == "__main__":
    print("\nStarting Seestar S50 Demo...")
    print("Prerequisites:")
    print("  1. seestar_alp must be running (http://localhost:5555)")
    print("  2. Seestar S50 must be connected to seestar_alp")
    print()
    
    asyncio.run(demo())
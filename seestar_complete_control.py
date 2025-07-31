#!/usr/bin/env python3
"""
Complete Seestar S50 Control Demo - with proper startup sequence.

This demonstrates the CORRECT workflow:
1. Connect seestar_alp to telescope
2. Open telescope with startup sequence
3. Set view mode
4. Control telescope (movement, presets)
5. Proper shutdown

Prerequisites:
- Seestar S50 powered on (wait 60-90 seconds after power on)
- seestar_alp running (http://localhost:5555)
"""

import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ascom_mcp.devices.manager import DeviceManager
from ascom_mcp.tools.telescope import TelescopeTools


async def main():
    print("=" * 60)
    print("COMPLETE SEESTAR S50 CONTROL DEMONSTRATION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Configure known devices
    os.environ["ASCOM_KNOWN_DEVICES"] = "localhost:5555:seestar_alp"

    # Initialize MCP server components
    manager = DeviceManager()
    await manager.initialize()
    telescope_tools = TelescopeTools(manager)

    try:
        # 1. DISCOVERY
        print("1. DISCOVERING SEESTAR")
        print("-" * 40)
        devices = await manager.discover_devices(timeout=3.0)

        seestar = None
        for device in devices:
            if "seestar" in device.name.lower():
                seestar = device
                print(f"✓ Found: {device.name} at {device.host}:{device.port}")

        if not seestar:
            print("❌ Seestar not found! Ensure seestar_alp is running.")
            return

        # 2. CONNECT TO TELESCOPE
        print("\n2. CONNECTING TO TELESCOPE")
        print("-" * 40)
        print("Connecting through MCP server...")
        result = await telescope_tools.connect(seestar.id)
        if not result["success"]:
            print(f"❌ Failed to connect: {result['message']}")
            return
        print("✓ MCP server connected to seestar_alp")

        # 3. OPEN TELESCOPE (CRITICAL STEP!)
        print("\n3. OPENING TELESCOPE")
        print("-" * 40)
        print("⚠️  This is the critical step that was missing!")
        print("Sending startup sequence to open telescope arm...")

        startup_params = {
            "lat": 40.745,  # Hoboken latitude
            "lon": -74.0256,  # Hoboken longitude
            "move_arm": True,  # CRITICAL: Opens the telescope!
        }

        result = await telescope_tools.custom_action(
            seestar.id, "action_start_up_sequence", startup_params
        )

        if result["success"]:
            print("✓ Startup sequence sent - telescope should be opening")
            print("  Listen for motor sounds as telescope opens")
            print("  Waiting 10 seconds for telescope to open...")
            await asyncio.sleep(10)
        else:
            print(f"❌ Startup failed: {result.get('error', 'Unknown error')}")
            return

        # 4. SET VIEW MODE
        print("\n4. SETTING VIEW MODE")
        print("-" * 40)
        print("Setting to scenery mode for terrestrial viewing...")

        result = await telescope_tools.custom_action(
            seestar.id,
            "method_sync",
            {"method": "iscope_start_view", "params": {"mode": "scenery"}},
        )

        if result["success"]:
            print("✓ View mode set to scenery")
        else:
            print(f"⚠️  View mode setting failed: {result.get('error', 'Unknown')}")
            # Continue anyway - not critical

        # 5. CHECK CURRENT POSITION
        print("\n5. CURRENT TELESCOPE STATUS")
        print("-" * 40)
        result = await telescope_tools.get_position(seestar.id)
        if result["success"]:
            pos = result["position"]
            print("✓ Position:")
            print(f"  Alt: {pos.get('altitude', 0):.2f}°")
            print(f"  Az: {pos.get('azimuth', 0):.2f}°")
            print(f"  RA: {pos['ra_hours']:.3f}h")
            print(f"  Dec: {pos['dec_degrees']:.2f}°")

        # 6. DEMONSTRATE MOVEMENT
        print("\n6. MOVEMENT DEMONSTRATION")
        print("-" * 40)
        print("Now the telescope should actually move!")

        movements = [
            ("DOWN toward horizon", 270, 5, 400),
            ("RIGHT (pan north)", 0, 3, 300),
            ("UP slightly", 90, 2, 300),
        ]

        for description, angle, duration, speed in movements:
            print(f"\n✓ Moving {description}")
            print(f"  Angle: {angle}°, Duration: {duration}s, Speed: {speed}")

            result = await telescope_tools.custom_action(
                seestar.id,
                "method_sync",
                {
                    "method": "scope_speed_move",
                    "params": {"speed": speed, "angle": angle, "dur_sec": duration},
                },
            )

            if result["success"]:
                print("  Movement command sent - watch the telescope!")
                await asyncio.sleep(duration + 1)
            else:
                print(f"  ❌ Movement failed: {result.get('error', 'Unknown')}")

        # 7. GO TO PRESET (if available)
        print("\n7. PRESET DEMONSTRATION")
        print("-" * 40)
        print("Attempting to go to manhattan_skyline preset...")

        result = await telescope_tools.custom_action(
            seestar.id, "goto_preset", {"preset_id": "manhattan_skyline"}
        )

        if result["success"]:
            print("✓ Preset command sent")
            print("  Telescope should move to preset position")
            await asyncio.sleep(5)
        else:
            print(f"⚠️  Preset not found or failed: {result.get('error', 'No preset')}")

        # 8. FOCUS CONTROL
        print("\n8. FOCUS ADJUSTMENT")
        print("-" * 40)

        # Get current focus
        result = await telescope_tools.custom_action(
            seestar.id, "method_sync", {"method": "get_focuser_position"}
        )

        if result["success"] and "result" in result:
            current = result["result"].get("result", 1500)
            print(f"✓ Current focus: {current}")

            # Adjust focus for Manhattan (approx 2 miles)
            new_focus = 1233  # Good for Manhattan from Hoboken
            print(f"  Setting focus to {new_focus} (optimized for ~2 miles)")

            result = await telescope_tools.custom_action(
                seestar.id,
                "method_sync",
                {"method": "set_focuser_position", "params": {"position": new_focus}},
            )

            if result["success"]:
                print("  ✓ Focus adjusted")

        # 9. SHUTDOWN SEQUENCE
        print("\n9. SHUTDOWN SEQUENCE")
        print("-" * 40)
        print("Properly closing telescope...")

        # Send shutdown command
        result = await telescope_tools.custom_action(
            seestar.id, "method_sync", {"method": "pi_shutdown"}
        )

        if result["success"]:
            print("✓ Shutdown command sent")
            print("  Telescope will park and close")
            print("  Listen for motor sounds...")
            await asyncio.sleep(10)

        # Disconnect
        result = await telescope_tools.disconnect(seestar.id)
        if result["success"]:
            print("✓ Disconnected from telescope")

        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE!")
        print("The telescope should have:")
        print("  1. Opened from parked position")
        print("  2. Moved in multiple directions")
        print("  3. Returned to park position")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await manager.shutdown()
        print("\nMCP server components shut down")


if __name__ == "__main__":
    print("\nCOMPLETE SEESTAR S50 CONTROL DEMO")
    print("Prerequisites:")
    print("  1. Seestar S50 powered on (wait 60-90 seconds)")
    print("  2. seestar_alp running (http://localhost:5555)")
    print("  3. Telescope currently DISCONNECTED in seestar_alp")
    print()
    print("Starting demonstration in 3 seconds...")
    import time

    time.sleep(3)

    asyncio.run(main())

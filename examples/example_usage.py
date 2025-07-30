#!/usr/bin/env python3
"""
Example usage of the ASCOM MCP Server.

This script demonstrates how to use the MCP server to control
ASCOM-compatible astronomy equipment.
"""

import asyncio
import json
from datetime import datetime


async def example_telescope_session():
    """
    Example telescope control session.
    
    This would normally be called by an AI assistant through MCP,
    but we're simulating the calls here for demonstration.
    """
    print("=" * 60)
    print("ASCOM MCP Server - Example Telescope Session")
    print("=" * 60)
    print()
    
    # In a real MCP scenario, these would be tool calls from the AI
    # Here we're simulating the workflow
    
    print("1. Discovering ASCOM devices on the network...")
    print("   Tool: discover_ascom_devices")
    print("   Simulated response:")
    discovery_response = {
        "success": True,
        "count": 2,
        "devices": [
            {
                "id": "telescope_0",
                "name": "Celestron NexStar 8SE",
                "type": "telescope",
                "host": "192.168.1.100",
                "port": 11111,
                "connect_hint": "Use 'telescope_connect' with device_id='telescope_0'"
            },
            {
                "id": "camera_0", 
                "name": "ZWO ASI294MC Pro",
                "type": "camera",
                "host": "192.168.1.101",
                "port": 11111,
                "connect_hint": "Use 'camera_connect' with device_id='camera_0'"
            }
        ]
    }
    print(json.dumps(discovery_response, indent=2))
    print()
    
    print("2. Connecting to telescope...")
    print("   Tool: telescope_connect")
    print("   Args: device_id='telescope_0'")
    print("   Simulated response:")
    connect_response = {
        "success": True,
        "message": "Connected to Celestron NexStar 8SE",
        "telescope": {
            "device_id": "telescope_0",
            "name": "Celestron NexStar 8SE",
            "connected": True,
            "can_slew": True,
            "can_park": True,
            "tracking": True
        }
    }
    print(json.dumps(connect_response, indent=2))
    print()
    
    print("3. Getting current telescope position...")
    print("   Tool: telescope_get_position")
    print("   Simulated response:")
    position_response = {
        "success": True,
        "position": {
            "ra_hours": 5.575,
            "dec_degrees": -5.39,
            "ra_hms": "5:34:30.0",
            "dec_dms": "-5:23:24",
            "altitude": 45.2,
            "azimuth": 180.5,
            "sidereal_time": 3.456
        },
        "status": {
            "tracking": True,
            "slewing": False,
            "at_park": False
        }
    }
    print(json.dumps(position_response, indent=2))
    print()
    
    print("4. Slewing to the Orion Nebula (M42)...")
    print("   Tool: telescope_goto_object")
    print("   Args: object_name='M42'")
    print("   Simulated response:")
    goto_response = {
        "success": True,
        "message": "Slewing to M42 (RA=5.588h, Dec=-5.45°)",
        "object_info": {
            "name": "M42",
            "ra_hours": 5.588,
            "dec_degrees": -5.45,
            "ra_hms": "5:35:17.0",
            "dec_dms": "-5:27:00"
        },
        "status": {
            "slewing": True,
            "target_ra": 5.588,
            "target_dec": -5.45
        }
    }
    print(json.dumps(goto_response, indent=2))
    print()
    
    print("5. Example natural language requests that AI could handle:")
    print("   - 'Show me the Andromeda Galaxy'")
    print("   - 'Point at Jupiter'") 
    print("   - 'Go to that bright star in Orion'")
    print("   - 'Park the telescope for the night'")
    print()
    
    print("6. Parking telescope...")
    print("   Tool: telescope_park")
    print("   Simulated response:")
    park_response = {
        "success": True,
        "message": "Telescope parking initiated",
        "status": {
            "at_park": False,
            "slewing": True
        }
    }
    print(json.dumps(park_response, indent=2))
    print()


async def example_camera_session():
    """Example camera control session."""
    print("=" * 60)
    print("ASCOM MCP Server - Example Camera Session")
    print("=" * 60)
    print()
    
    print("1. Connecting to camera...")
    print("   Tool: camera_connect")
    print("   Args: device_id='camera_0'")
    print("   Simulated response:")
    camera_connect = {
        "success": True,
        "message": "Connected to ZWO ASI294MC Pro",
        "camera": {
            "device_id": "camera_0",
            "name": "ZWO ASI294MC Pro",
            "sensor_type": "Color",
            "pixel_size": {"x": 4.63, "y": 4.63},
            "sensor_size": {"width": 4144, "height": 2822},
            "has_cooler": True,
            "cooler_on": True,
            "ccd_temperature": -10.0
        }
    }
    print(json.dumps(camera_connect, indent=2))
    print()
    
    print("2. Capturing a 30-second exposure...")
    print("   Tool: camera_capture")
    print("   Args: exposure_seconds=30, light_frame=True")
    print("   Simulated response:")
    capture_response = {
        "success": True,
        "message": "Captured 30s light frame",
        "metadata": {
            "exposure_time": 30,
            "frame_type": "light",
            "timestamp": datetime.utcnow().isoformat(),
            "ccd_temperature": -10.0,
            "gain": 120,
            "offset": 30
        },
        "image_info": {
            "width": 4144,
            "height": 2822,
            "bit_depth": "uint16"
        }
    }
    print(json.dumps(capture_response, indent=2))
    print()


def main():
    """Run example sessions."""
    print("\nASCOM MCP Server - Example Usage")
    print("================================\n")
    
    print("This example demonstrates how an AI assistant would use")
    print("the ASCOM MCP server to control astronomy equipment.\n")
    
    print("In a real scenario:")
    print("1. The MCP server runs as a subprocess")
    print("2. AI assistants communicate via JSON-RPC over stdio")
    print("3. Natural language gets translated to tool calls")
    print("4. Results are returned to the AI for interpretation\n")
    
    # Run example sessions
    asyncio.run(example_telescope_session())
    print()
    asyncio.run(example_camera_session())
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
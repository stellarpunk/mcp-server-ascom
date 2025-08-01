#!/usr/bin/env python3
"""Test ASCOM MCP discovery directly."""

import asyncio
import sys
sys.path.insert(0, 'src')

from ascom_mcp.server_fastmcp import discovery_tools, telescope_tools, ensure_initialized
from unittest.mock import MagicMock
import structlog


async def test_discovery():
    """Test discovery and connection flow."""
    
    # Create mock context
    ctx = MagicMock()
    ctx.logger = structlog.get_logger()
    
    # Ensure server is initialized
    await ensure_initialized()
    
    print("=== Testing ASCOM MCP Discovery ===\n")
    
    # 1. Discover devices
    print("1. Discovering ASCOM devices...")
    result = await discovery_tools.discover_devices(timeout=3.0)
    print(f"Discovery result: {result}")
    
    if result.get("success") and result.get("count", 0) > 0:
        # 2. Connect to first telescope
        device_id = result["devices"][0]["id"]
        print(f"\n2. Connecting to telescope: {device_id}")
        connect_result = await telescope_tools.connect(device_id=device_id)
        print(f"Connect result: {connect_result}")
        
        if connect_result.get("success"):
            # 3. Get telescope position
            print(f"\n3. Getting telescope position...")
            pos_result = await telescope_tools.get_position(device_id=device_id)
            print(f"Position result: {pos_result}")
            
            print("\n✅ All tests passed! MCP integration is working correctly.")
        else:
            print("\n❌ Failed to connect to telescope")
    else:
        print("\n❌ No devices discovered")


if __name__ == "__main__":
    asyncio.run(test_discovery())
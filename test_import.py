#!/usr/bin/env python3
"""Test that the ASCOM MCP server can be imported."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ascom_mcp import create_server, __version__
    print(f"✓ Successfully imported ascom_mcp v{__version__}")
    
    from ascom_mcp.server import mcp
    print("✓ Successfully imported FastMCP server")
    
    from ascom_mcp.devices.manager import DeviceManager
    print("✓ Successfully imported DeviceManager")
    
    from ascom_mcp.tools.discovery import DiscoveryTools
    print("✓ Successfully imported DiscoveryTools")
    
    from ascom_mcp.tools.telescope import TelescopeTools
    print("✓ Successfully imported TelescopeTools")
    
    from ascom_mcp.tools.camera import CameraTools
    print("✓ Successfully imported CameraTools")
    
    print("\n✓ All imports successful! The server structure is valid.")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
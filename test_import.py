#!/usr/bin/env python3
"""Test that the ASCOM MCP server can be imported."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ascom_mcp import __version__
    print(f"✓ Successfully imported ascom_mcp v{__version__}")

    # Test that create_server is importable
    import ascom_mcp
    assert hasattr(ascom_mcp, 'create_server'), "create_server not found in ascom_mcp"
    print("✓ create_server function is available")

    # Test imports - using importlib to avoid unused import warnings
    import importlib
    modules_to_test = [
        ("ascom_mcp.server", "FastMCP server"),
        ("ascom_mcp.devices.manager", "DeviceManager"),
        ("ascom_mcp.tools.discovery", "DiscoveryTools"),
        ("ascom_mcp.tools.telescope", "TelescopeTools"),
        ("ascom_mcp.tools.camera", "CameraTools"),
    ]

    for module_name, display_name in modules_to_test:
        importlib.import_module(module_name)
        print(f"✓ Successfully imported {display_name}")

    print("\n✓ All imports successful! The server structure is valid.")

except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

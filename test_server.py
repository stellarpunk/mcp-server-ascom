#!/usr/bin/env python3
"""
Test script for ASCOM MCP Server functionality.

This script tests the server without needing MCP Inspector UI.
"""

import asyncio
import json

from mcp.types import (
    CallToolRequest,
    ClientCapabilities,
    Implementation,
    InitializeRequest,
    InitializeRequestParams,
    ListResourcesRequest,
    ListToolsRequest,
)

from ascom_mcp.server import create_server


async def test_server():
    """Test basic server functionality."""
    print("Creating ASCOM MCP Server...")
    server = create_server()

    # Test initialization
    print("\n1. Testing initialization...")
    init_params = InitializeRequestParams(
        protocolVersion="2025-06-18",  # Using latest MCP specification
        capabilities=ClientCapabilities(),
        clientInfo=Implementation(name="test_client", version="1.0.0")
    )
    init_request = InitializeRequest(method="initialize", params=init_params)
    init_result = await server.handle_initialize(init_request)
    print(f"✓ Server initialized: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
    print(f"  Capabilities: tools={init_result.capabilities.tools}, resources={init_result.capabilities.resources}")

    # Test list resources
    print("\n2. Testing list resources...")
    resources_request = ListResourcesRequest(method="resources/list", params={})
    resources_result = await server.handle_list_resources(resources_request)
    print(f"✓ Found {len(resources_result.resources)} resources:")
    for resource in resources_result.resources:
        print(f"  - {resource.name}: {resource.uri}")

    # Test list tools
    print("\n3. Testing list tools...")
    tools_request = ListToolsRequest(method="tools/list", params={})
    tools_result = await server.handle_list_tools(tools_request)
    print(f"✓ Found {len(tools_result.tools)} tools:")
    for tool in tools_result.tools[:5]:  # Show first 5
        print(f"  - {tool.name}: {tool.description}")
    print(f"  ... and {len(tools_result.tools) - 5} more")

    # Test discovery tool
    print("\n4. Testing device discovery...")
    discovery_request = CallToolRequest(
        method="tools/call",
        params={
            "name": "discover_ascom_devices",
            "arguments": {"timeout": 2.0}
        }
    )
    try:
        discovery_result = await server.handle_call_tool(discovery_request)
        # Handle structured content - first block is JSON, second is text fallback
        if discovery_result.content:
            # Parse the JSON content
            json_content = discovery_result.content[0].text
            result_data = json.loads(json_content)

            # Check if it's an error or success
            if "error" in result_data:
                print(f"⚠️  Discovery returned error: {result_data['error']['message']}")
            else:
                device_count = len(result_data.get("devices", []))
                print(f"✓ Discovery completed: Found {device_count} devices")
                if device_count > 0:
                    for device in result_data["devices"]:
                        print(f"  - {device.get('name', 'Unknown')} at {device.get('host', 'Unknown')}")
        else:
            print("⚠️  No content in discovery result")
    except Exception as e:
        print(f"⚠️  Discovery test failed: {e}")

    # Cleanup
    await server.cleanup()
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_server())

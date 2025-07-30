"""Integration tests for MCP protocol implementation."""

import json
from unittest.mock import patch

import pytest
from mcp.types import (
    InitializeRequest,
    ListResourcesRequest,
    ReadResourceRequest,
)


class TestMCPProtocol:
    """Test MCP protocol message flow."""

    @pytest.mark.asyncio
    async def test_initialize(self, mcp_server):
        """Test server initialization with current protocol."""
        # Test with Claude Desktop's protocol version
        request = InitializeRequest(
            protocolVersion="2025-06-18",
            capabilities={},
            clientInfo={"name": "claude-desktop", "version": "1.0"}
        )
        result = await mcp_server.handle_initialize(request)

        # Server should negotiate protocol version
        assert result.protocolVersion in ["2025-06-18", "2024-11-05"]
        assert result.capabilities.tools is not None
        assert result.capabilities.resources is not None
        assert result.serverInfo.name == "ascom-mcp-server"
        assert "0.2" in result.serverInfo.version

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_server, list_tools_request):
        """Test listing available tools."""
        # Initialize first
        await mcp_server.handle_initialize(
            InitializeRequest(protocolVersion="2024-11-05", capabilities={})
        )

        result = await mcp_server.handle_list_tools(list_tools_request)

        tool_names = [tool.name for tool in result.tools]
        assert "discover_ascom_devices" in tool_names
        assert "telescope_connect" in tool_names
        assert "telescope_goto" in tool_names
        assert "camera_capture" in tool_names
        assert len(result.tools) == 11  # Total tools

    @pytest.mark.asyncio
    async def test_list_resources(self, mcp_server):
        """Test listing available resources."""
        await mcp_server.handle_initialize(
            InitializeRequest(protocolVersion="2024-11-05", capabilities={})
        )

        result = await mcp_server.handle_list_resources(ListResourcesRequest())

        resource_uris = [r.uri for r in result.resources]
        assert "ascom://server/info" in resource_uris
        assert "ascom://devices/connected" in resource_uris
        assert "ascom://devices/available" in resource_uris

    @pytest.mark.asyncio
    async def test_read_server_info_resource(self, mcp_server):
        """Test reading server info resource."""
        await mcp_server.handle_initialize(
            InitializeRequest(protocolVersion="2024-11-05", capabilities={})
        )

        result = await mcp_server.handle_read_resource(
            ReadResourceRequest(uri="ascom://server/info")
        )

        assert len(result.contents) == 1
        content = json.loads(result.contents[0].text)
        assert content["name"] == "ascom-mcp-server"
        assert content["ascom_version"] == "Alpaca v1.0"
        assert "telescope" in content["capabilities"]

    @pytest.mark.asyncio
    async def test_discover_devices_tool(self, mcp_server, call_tool_request):
        """Test device discovery tool call."""
        await mcp_server.handle_initialize(
            InitializeRequest(protocolVersion="2024-11-05", capabilities={})
        )

        # Mock discovery to return test devices
        with patch.object(
            mcp_server.device_manager,
            'discover_devices',
            return_value=[]
        ):
            request = call_tool_request("discover_ascom_devices", {"timeout": 2.0})
            result = await mcp_server.handle_call_tool(request)

            assert not result.isError
            response = json.loads(result.content[0].text)
            assert response["success"] is True
            assert "count" in response

    @pytest.mark.asyncio
    async def test_telescope_connect_flow(self, mcp_server, call_tool_request):
        """Test complete telescope connection flow."""
        await mcp_server.handle_initialize(
            InitializeRequest(protocolVersion="2024-11-05", capabilities={})
        )

        # 1. Discover devices
        await mcp_server.device_manager.discover_devices()

        # 2. Connect to telescope
        request = call_tool_request("telescope_connect", {"device_id": "telescope_0"})
        result = await mcp_server.handle_call_tool(request)

        response = json.loads(result.content[0].text)
        assert response["success"] is True
        assert response["telescope"]["connected"] is True

        # 3. Get position
        request = call_tool_request("telescope_get_position", {"device_id": "telescope_0"})
        result = await mcp_server.handle_call_tool(request)

        response = json.loads(result.content[0].text)
        assert response["success"] is True
        assert "position" in response
        assert "ra_hours" in response["position"]

    @pytest.mark.asyncio
    async def test_error_handling(self, mcp_server, call_tool_request):
        """Test error handling in tool calls."""
        await mcp_server.handle_initialize(
            InitializeRequest(protocolVersion="2024-11-05", capabilities={})
        )

        # Call with invalid tool name
        request = call_tool_request("invalid_tool", {})
        result = await mcp_server.handle_call_tool(request)

        assert result.isError
        response = json.loads(result.content[0].text)
        assert response["success"] is False
        assert "Unknown tool" in response["error"]

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mcp_server, call_tool_request):
        """Test handling concurrent tool calls."""
        await mcp_server.handle_initialize(
            InitializeRequest(protocolVersion="2024-11-05", capabilities={})
        )

        # Discover devices first
        await mcp_server.device_manager.discover_devices()

        # Make multiple concurrent requests
        import asyncio

        tasks = [
            mcp_server.handle_call_tool(
                call_tool_request("telescope_connect", {"device_id": "telescope_0"})
            ),
            mcp_server.handle_call_tool(
                call_tool_request("camera_connect", {"device_id": "camera_0"})
            )
        ]

        results = await asyncio.gather(*tasks)

        # Both should succeed
        for result in results:
            response = json.loads(result.content[0].text)
            assert response["success"] is True

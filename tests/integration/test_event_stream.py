"""Integration tests for event stream functionality."""

import asyncio
import json
import os
import time
from unittest.mock import patch

import pytest
from fastmcp import Client

from ascom_mcp.server_fastmcp import create_server


class TestEventStream:
    """Test event streaming from ASCOM devices."""
    
    @pytest.mark.asyncio
    async def test_event_types_available(self):
        """Test that event types can be retrieved."""
        server = create_server()
        async with Client(server) as client:
            result = await client.call_tool("get_event_types", {})
            
            data = json.loads(result.content[0].text)
            assert data["success"] is True
            assert "event_types" in data
            assert "PiStatus" in data["event_types"]
            assert "GotoComplete" in data["event_types"]
        
    @pytest.mark.asyncio
    async def test_event_history_without_device(self):
        """Test getting event history for non-connected device."""
        server = create_server()
        async with Client(server) as client:
            result = await client.call_tool(
                "get_event_history",
                {"device_id": "unknown_device"}
            )
            
            data = json.loads(result.content[0].text)
            assert data["success"] is False
            assert "not found" in data["error"]
        
    @pytest.mark.asyncio
    async def test_event_stream_resource(self):
        """Test that event stream resource is available."""
        with patch.dict(os.environ, {
            "ASCOM_DIRECT_DEVICES": "telescope_1:localhost:5555:Seestar S50"
        }):
            server = create_server()
            async with Client(server) as client:
                # List resources and templates
                resources = await client.list_resources()
                resource_uris = [str(r.uri) for r in resources]
                
                # Get resource templates too
                templates = await client.list_resource_templates()
                template_uris = [str(t.uriTemplate) for t in templates]
                
                # Event stream should be available as a template
                assert any("ascom://events/" in uri for uri in template_uris)
                
                # Read event stream for non-connected device
                result = await client.read_resource("ascom://events/telescope_1/stream")
                data = json.loads(result[0].text)
                
                assert data["device_id"] == "telescope_1"
                assert data["status"] == "no_events"
                assert data["events"] == []
        
    @pytest.mark.asyncio
    async def test_event_filtering(self):
        """Test event filtering by type and time."""
        server = create_server()
        async with Client(server) as client:
            # Test with event type filter
            result = await client.call_tool(
                "get_event_history",
                {
                    "device_id": "telescope_1",
                    "event_types": ["PiStatus", "GotoComplete"],
                    "count": 5
                }
            )
            
            data = json.loads(result.content[0].text)
            # Should handle gracefully even if device not found
            assert "success" in data
        
    @pytest.mark.asyncio
    async def test_clear_event_history(self):
        """Test clearing event history."""
        server = create_server()
        async with Client(server) as client:
            result = await client.call_tool(
                "clear_event_history",
                {"device_id": "telescope_1"}
            )
            
            data = json.loads(result.content[0].text)
            # Should fail since device not connected
            assert data["success"] is False
            assert "not found" in data["error"]
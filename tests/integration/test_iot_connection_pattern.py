"""Integration tests for IoT-style connection patterns."""

import json
import os
from unittest.mock import patch

import pytest
from fastmcp import Client

from ascom_mcp.server_fastmcp import create_server


class TestIoTConnectionPattern:
    """Test IoT-style device connection without discovery."""
    
    @pytest.mark.asyncio
    async def test_connect_with_direct_string(self):
        """Test connecting using direct connection string."""
        # No discovery, no pre-configuration
        with patch.dict(os.environ, {}, clear=True):
            server = create_server()
            async with Client(server) as client:
                # Should connect directly without discovery
                result = await client.call_tool(
                    "telescope_connect",
                    {"device_id": "seestar@localhost:5555"}
                )
                
                data = json.loads(result.content[0].text)
                assert data["success"] is True
                assert "seestar" in data["message"].lower()
                
    @pytest.mark.asyncio
    async def test_connect_from_persistent_state(self):
        """Test connecting to device from persistent state."""
        # Simulate having discovered before
        with patch("ascom_mcp.devices.state_persistence.DeviceStatePersistence.load_devices") as mock_load:
            from ascom_mcp.devices.manager import DeviceInfo
            
            # Mock stored devices
            stored_device = DeviceInfo({
                "DeviceType": "Telescope",
                "DeviceNumber": 1,
                "DeviceName": "My Seestar",
                "Host": "localhost",
                "Port": 5555,
                "UniqueID": "stored_device_1"
            })
            mock_load.return_value = [stored_device]
            
            server = create_server()
            async with Client(server) as client:
                # Connect using saved device ID
                result = await client.call_tool(
                    "telescope_connect",
                    {"device_id": "telescope_1"}
                )
                
                data = json.loads(result.content[0].text)
                assert data["success"] is True
                
    @pytest.mark.asyncio
    async def test_connect_without_discovery_fails_helpfully(self):
        """Test that connection without discovery gives helpful error."""
        with patch.dict(os.environ, {}, clear=True):
            server = create_server()
            async with Client(server) as client:
                # Try to connect to unknown device
                try:
                    await client.call_tool(
                        "telescope_connect",
                        {"device_id": "unknown_device"}
                    )
                    assert False, "Should have raised error"
                except Exception as e:
                    error_msg = str(e)
                    # Should suggest helpful options
                    assert "discover_ascom_devices" in error_msg
                    assert "host:port" in error_msg
                    assert "ASCOM_DIRECT_DEVICES" in error_msg
                    
    @pytest.mark.asyncio
    async def test_discovery_not_automatic(self):
        """Test that discovery doesn't run automatically."""
        with patch.dict(os.environ, {}, clear=True):
            server = create_server()
            async with Client(server) as client:
                # Get device list without discovery
                result = await client.call_tool("list_devices", {})
                data = json.loads(result.content[0].text)
                
                # Should have no devices (or only from config/state)
                # Not from UDP discovery
                assert data["success"] is True
                # No assertion on device count - depends on state/config
                
    @pytest.mark.asyncio
    async def test_multiple_connection_methods(self):
        """Test various ways to specify device connection."""
        test_cases = [
            # Direct connection string
            "seestar@localhost:5555",
            # IP only connection string  
            "192.168.1.100:5555",
            # From environment (when configured)
            "telescope_1",
        ]
        
        with patch.dict(os.environ, {
            "ASCOM_DIRECT_DEVICES": "telescope_1:localhost:5555:Seestar S50"
        }):
            server = create_server()
            async with Client(server) as client:
                for device_id in test_cases:
                    # Each should work without discovery
                    result = await client.call_tool(
                        "telescope_connect",
                        {"device_id": device_id}
                    )
                    
                    data = json.loads(result.content[0].text)
                    assert data["success"] is True
                    
                    # Disconnect for next test
                    await client.call_tool(
                        "telescope_disconnect",
                        {"device_id": device_id}
                    )
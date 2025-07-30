"""Unit tests for discovery tools."""

from unittest.mock import AsyncMock

import pytest

from ascom_mcp.devices.manager import DeviceInfo
from ascom_mcp.tools.discovery import DiscoveryTools


class TestDiscoveryTools:
    """Test DiscoveryTools class."""

    @pytest.mark.asyncio
    async def test_discover_devices_success(self):
        """Test successful device discovery."""
        # Mock device manager
        mock_manager = AsyncMock()
        mock_devices = [
            DeviceInfo({
                "DeviceType": "Telescope",
                "DeviceNumber": 0,
                "DeviceName": "Test Telescope",
                "Host": "192.168.1.100"
            }),
            DeviceInfo({
                "DeviceType": "Camera",
                "DeviceNumber": 0,
                "DeviceName": "Test Camera",
                "Host": "192.168.1.101"
            })
        ]
        mock_manager.discover_devices.return_value = mock_devices

        tools = DiscoveryTools(mock_manager)
        result = await tools.discover_devices(timeout=3.0)

        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["devices"]) == 2
        assert "connect_hint" in result["devices"][0]
        assert result["devices"][0]["connect_hint"] == "Use 'telescope_connect' with device_id='telescope_0'"

    @pytest.mark.asyncio
    async def test_discover_devices_empty(self):
        """Test discovery with no devices found."""
        mock_manager = AsyncMock()
        mock_manager.discover_devices.return_value = []

        tools = DiscoveryTools(mock_manager)
        result = await tools.discover_devices()

        assert result["success"] is True
        assert result["count"] == 0
        assert result["message"] == "No ASCOM devices found on network"

    @pytest.mark.asyncio
    async def test_discover_devices_error(self):
        """Test discovery with network error."""
        mock_manager = AsyncMock()
        mock_manager.discover_devices.side_effect = Exception("Network timeout")

        tools = DiscoveryTools(mock_manager)
        result = await tools.discover_devices()

        assert result["success"] is False
        assert "Network timeout" in result["error"]
        assert "Check network connection" in result["message"]

    @pytest.mark.asyncio
    async def test_get_device_info_telescope(self):
        """Test getting telescope device info."""
        mock_manager = AsyncMock()
        mock_info = {
            "id": "telescope_0",
            "type": "telescope",
            "name": "Test Telescope",
            "connected": True,
            "driver_info": "Test Driver v1.0"
        }
        mock_manager.get_device_info.return_value = mock_info

        tools = DiscoveryTools(mock_manager)
        result = await tools.get_device_info("telescope_0")

        assert result["success"] is True
        assert result["device"]["type"] == "telescope"
        assert "capabilities" in result["device"]
        assert "goto" in result["device"]["capabilities"]
        assert "park" in result["device"]["capabilities"]

    @pytest.mark.asyncio
    async def test_get_device_info_camera(self):
        """Test getting camera device info."""
        mock_manager = AsyncMock()
        mock_info = {
            "id": "camera_0",
            "type": "camera",
            "name": "Test Camera"
        }
        mock_manager.get_device_info.return_value = mock_info

        tools = DiscoveryTools(mock_manager)
        result = await tools.get_device_info("camera_0")

        assert result["success"] is True
        assert "capture" in result["device"]["capabilities"]
        assert "cooling" in result["device"]["capabilities"]

    @pytest.mark.asyncio
    async def test_get_device_info_error(self):
        """Test device info with error."""
        mock_manager = AsyncMock()
        mock_manager.get_device_info.side_effect = Exception("Device not found")

        tools = DiscoveryTools(mock_manager)
        result = await tools.get_device_info("unknown_device")

        assert result["success"] is False
        assert "Device not found" in result["error"]

"""Unit tests for telescope tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ascom_mcp.devices.manager import ConnectedDevice, DeviceInfo
from ascom_mcp.tools.telescope import TelescopeTools


class TestTelescopeTools:
    """Test TelescopeTools class."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_telescope):
        """Test successful telescope connection."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({
            "DeviceType": "Telescope",
            "DeviceNumber": 0,
            "DeviceName": "Test Telescope"
        })
        connected = ConnectedDevice(device_info, mock_telescope)
        mock_manager.connect_device.return_value = connected

        tools = TelescopeTools(mock_manager)
        result = await tools.connect("Telescope_0")

        assert result["success"] is True
        assert result["telescope"]["connected"] is True
        assert result["telescope"]["can_slew"] is True
        assert "Test Telescope" in result["message"]

    @pytest.mark.asyncio
    async def test_disconnect_with_park(self, mock_telescope):
        """Test disconnect parks telescope if needed."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Telescope", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_telescope)
        mock_manager.get_connected_device.return_value = connected

        # Telescope can park but not at park
        mock_telescope.CanPark = True
        mock_telescope.AtPark = False

        tools = TelescopeTools(mock_manager)
        result = await tools.disconnect("Telescope_0")

        assert result["success"] is True
        mock_telescope.Park.assert_called_once()
        mock_manager.disconnect_device.assert_called_once_with("Telescope_0")

    @pytest.mark.asyncio
    async def test_goto_valid_coordinates(self, mock_telescope):
        """Test goto with valid coordinates."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Telescope", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_telescope)
        mock_manager.get_connected_device.return_value = connected

        mock_telescope.CanSlew = True
        mock_telescope.Slewing = False

        tools = TelescopeTools(mock_manager)
        result = await tools.goto("Telescope_0", ra=12.5, dec=45.0)

        assert result["success"] is True
        assert result["status"]["target_ra"] == 12.5
        assert result["status"]["target_dec"] == 45.0
        mock_telescope.SlewToCoordinatesAsync.assert_called_once_with(12.5, 45.0)

    @pytest.mark.asyncio
    async def test_goto_invalid_ra(self):
        """Test goto with invalid RA."""
        mock_manager = AsyncMock()
        tools = TelescopeTools(mock_manager)

        # RA out of range
        result = await tools.goto("Telescope_0", ra=25.0, dec=0.0)

        assert result["success"] is False
        assert "RA must be between 0 and 24" in result["error"]

    @pytest.mark.asyncio
    async def test_goto_invalid_dec(self):
        """Test goto with invalid declination."""
        mock_manager = AsyncMock()
        tools = TelescopeTools(mock_manager)

        # Dec out of range
        result = await tools.goto("Telescope_0", ra=12.0, dec=-95.0)

        assert result["success"] is False
        assert "Dec must be between -90 and +90" in result["error"]

    @pytest.mark.asyncio
    async def test_goto_telescope_busy(self, mock_telescope):
        """Test goto when telescope is slewing."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Telescope", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_telescope)
        mock_manager.get_connected_device.return_value = connected

        mock_telescope.Slewing = True

        tools = TelescopeTools(mock_manager)
        result = await tools.goto("Telescope_0", ra=12.0, dec=45.0)

        assert result["success"] is False
        assert "already slewing" in result["error"]

    @pytest.mark.asyncio
    async def test_goto_object_success(self, mock_telescope):
        """Test goto named object."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Telescope", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_telescope)
        mock_manager.get_connected_device.return_value = connected

        mock_telescope.CanSlew = True
        mock_telescope.Slewing = False

        tools = TelescopeTools(mock_manager)

        # Mock astropy SkyCoord
        with patch("ascom_mcp.tools.telescope.SkyCoord") as mock_skycoord:
            mock_coord = MagicMock()
            mock_coord.ra.hour = 5.588
            mock_coord.dec.degree = -5.45
            mock_coord.ra.to_string.return_value = "5:35:17.0"
            mock_coord.dec.to_string.return_value = "-5:27:00"
            mock_skycoord.from_name.return_value = mock_coord

            result = await tools.goto_object("Telescope_0", "M42")

            assert result["success"] is True
            assert "M42" in result["message"]
            assert result["object_info"]["ra_hours"] == 5.588
            mock_telescope.SlewToCoordinatesAsync.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_position(self, mock_telescope):
        """Test getting telescope position."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Telescope", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_telescope)
        mock_manager.get_connected_device.return_value = connected

        mock_telescope.RightAscension = 12.345
        mock_telescope.Declination = 45.678
        mock_telescope.Altitude = 60.0
        mock_telescope.Azimuth = 180.0

        tools = TelescopeTools(mock_manager)

        with patch("ascom_mcp.tools.telescope.SkyCoord"):
            result = await tools.get_position("Telescope_0")

            assert result["success"] is True
            assert result["position"]["ra_hours"] == 12.345
            assert result["position"]["dec_degrees"] == 45.678
            assert result["position"]["altitude"] == 60.0
            assert result["status"]["tracking"] is True

    @pytest.mark.asyncio
    async def test_park_success(self, mock_telescope):
        """Test parking telescope."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Telescope", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_telescope)
        mock_manager.get_connected_device.return_value = connected

        mock_telescope.CanPark = True
        mock_telescope.AtPark = False

        tools = TelescopeTools(mock_manager)
        result = await tools.park("Telescope_0")

        assert result["success"] is True
        mock_telescope.Park.assert_called_once()
        assert "parking initiated" in result["message"]

    @pytest.mark.asyncio
    async def test_park_already_parked(self, mock_telescope):
        """Test parking when already parked."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Telescope", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_telescope)
        mock_manager.get_connected_device.return_value = connected

        mock_telescope.CanPark = True
        mock_telescope.AtPark = True

        tools = TelescopeTools(mock_manager)
        result = await tools.park("Telescope_0")

        assert result["success"] is True
        assert "already parked" in result["message"]
        mock_telescope.Park.assert_not_called()

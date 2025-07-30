"""Unit tests for camera tools."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from ascom_mcp.tools.camera import CameraTools
from ascom_mcp.devices.manager import ConnectedDevice, DeviceInfo
from ascom_mcp.utils.errors import InvalidParameterError, DeviceBusyError


class TestCameraTools:
    """Test CameraTools class."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_camera):
        """Test successful camera connection."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({
            "DeviceType": "Camera",
            "DeviceNumber": 0,
            "DeviceName": "Test Camera"
        })
        connected = ConnectedDevice(device_info, mock_camera)
        mock_manager.connect_device.return_value = connected
        
        tools = CameraTools(mock_manager)
        result = await tools.connect("camera_0")
        
        assert result["success"] == True
        assert result["camera"]["connected"] == True
        assert result["camera"]["sensor_type"] == "Color"
        assert result["camera"]["has_cooler"] == True
        
    @pytest.mark.asyncio
    async def test_capture_invalid_exposure(self):
        """Test capture with invalid exposure time."""
        mock_manager = AsyncMock()
        tools = CameraTools(mock_manager)
        
        result = await tools.capture("camera_0", exposure_seconds=-1)
        
        assert result["success"] == False
        assert "must be positive" in result["error"]
        
    @pytest.mark.asyncio
    async def test_capture_camera_busy(self, mock_camera):
        """Test capture when camera is busy."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Camera", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_camera)
        mock_manager.get_connected_device.return_value = connected
        
        mock_camera.CameraState = 2  # exposing
        
        tools = CameraTools(mock_manager)
        result = await tools.capture("camera_0", exposure_seconds=10)
        
        assert result["success"] == False
        assert "Camera is busy" in result["error"]
        
    @pytest.mark.asyncio
    async def test_capture_success(self, mock_camera):
        """Test successful image capture."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Camera", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_camera)
        mock_manager.get_connected_device.return_value = connected
        
        mock_camera.CameraState = 0  # idle
        mock_camera.ImageReady = False
        
        # Simulate exposure completion
        async def simulate_exposure():
            await asyncio.sleep(0.1)
            mock_camera.ImageReady = True
            
        tools = CameraTools(mock_manager)
        
        # Start capture and simulation concurrently
        capture_task = asyncio.create_task(
            tools.capture("camera_0", exposure_seconds=0.5)
        )
        sim_task = asyncio.create_task(simulate_exposure())
        
        result = await capture_task
        await sim_task
        
        assert result["success"] == True
        assert result["metadata"]["exposure_time"] == 0.5
        assert result["metadata"]["frame_type"] == "light"
        mock_camera.StartExposure.assert_called_once_with(0.5, True)
        
    @pytest.mark.asyncio
    async def test_get_status_with_cooler(self, mock_camera):
        """Test getting camera status with cooler info."""
        mock_manager = AsyncMock()
        device_info = DeviceInfo({"DeviceType": "Camera", "DeviceNumber": 0})
        connected = ConnectedDevice(device_info, mock_camera)
        mock_manager.get_connected_device.return_value = connected
        
        mock_camera.CameraState = 0  # idle
        mock_camera.CoolerPower = 75.5
        
        tools = CameraTools(mock_manager)
        result = await tools.get_status("camera_0")
        
        assert result["success"] == True
        assert result["status"]["state"] == "idle"
        assert result["status"]["temperature"]["ccd"] == -10.0
        assert result["status"]["temperature"]["cooler_on"] == True
        assert result["settings"]["binning"]["x"] == 1
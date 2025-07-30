"""Pytest configuration and fixtures."""

import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.types import (
    InitializeRequest,
    ListToolsRequest,
    CallToolRequest,
    TextContent
)


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_telescope():
    """Mock ASCOM telescope device."""
    telescope = MagicMock()
    telescope.Connected = False
    telescope.CanSlew = True
    telescope.CanPark = True
    telescope.CanFindHome = True
    telescope.CanSetTracking = True
    telescope.Slewing = False
    telescope.AtPark = False
    telescope.Tracking = True
    telescope.RightAscension = 5.5
    telescope.Declination = -5.4
    telescope.Description = "Mock Telescope"
    telescope.DriverInfo = "Mock Driver v1.0"
    telescope.DriverVersion = "1.0"
    telescope.InterfaceVersion = 3
    return telescope


@pytest.fixture
def mock_camera():
    """Mock ASCOM camera device."""
    camera = MagicMock()
    camera.Connected = False
    camera.CameraState = 0  # idle
    camera.ImageReady = False
    camera.CanAbortExposure = True
    camera.CanSetCCDTemperature = True
    camera.CoolerOn = True
    camera.CCDTemperature = -10.0
    camera.SensorType = 1  # Color
    camera.PixelSizeX = 4.63
    camera.PixelSizeY = 4.63
    camera.CameraXSize = 4144
    camera.CameraYSize = 2822
    camera.MaxBinX = 4
    camera.MaxBinY = 4
    camera.BinX = 1
    camera.BinY = 1
    camera.StartX = 0
    camera.StartY = 0
    camera.NumX = 4144
    camera.NumY = 2822
    camera.Description = "Mock Camera"
    camera.DriverInfo = "Mock Camera Driver v1.0"
    return camera


@pytest.fixture
def mock_discovery_response():
    """Mock device discovery response."""
    return [
        {
            "DeviceName": "Mock Telescope",
            "DeviceType": "Telescope",
            "DeviceNumber": 0,
            "UniqueID": "mock-telescope-001",
            "Host": "localhost",
            "Port": 11111,
            "ApiVersion": 1
        },
        {
            "DeviceName": "Mock Camera",
            "DeviceType": "Camera", 
            "DeviceNumber": 0,
            "UniqueID": "mock-camera-001",
            "Host": "localhost",
            "Port": 11111,
            "ApiVersion": 1
        }
    ]


@pytest.fixture
async def mock_device_manager(mock_telescope, mock_camera):
    """Mock device manager with test devices."""
    from ascom_mcp.devices.manager import DeviceManager
    
    manager = DeviceManager()
    manager._session = MagicMock()
    
    # Mock discovery
    async def mock_discover(timeout=5.0):
        from ascom_mcp.devices.manager import DeviceInfo
        devices = [
            DeviceInfo({
                "DeviceName": "Mock Telescope",
                "DeviceType": "Telescope",
                "DeviceNumber": 0,
                "Host": "localhost",
                "Port": 11111
            }),
            DeviceInfo({
                "DeviceName": "Mock Camera",
                "DeviceType": "Camera",
                "DeviceNumber": 0,
                "Host": "localhost",
                "Port": 11111
            })
        ]
        manager._available_devices = {d.id: d for d in devices}
        return devices
    
    manager.discover_devices = mock_discover
    
    # Mock alpyca constructors
    import alpyca
    alpyca.Telescope = MagicMock(return_value=mock_telescope)
    alpyca.Camera = MagicMock(return_value=mock_camera)
    
    await manager.initialize()
    return manager


@pytest.fixture
async def mcp_server(mock_device_manager):
    """Create MCP server with mocked devices."""
    from ascom_mcp.server import AscomMCPServer
    
    server = AscomMCPServer()
    
    # Replace device manager with mock
    server.device_manager = mock_device_manager
    
    # Initialize tools
    from ascom_mcp.tools.discovery import DiscoveryTools
    from ascom_mcp.tools.telescope import TelescopeTools
    from ascom_mcp.tools.camera import CameraTools
    
    server.discovery_tools = DiscoveryTools(mock_device_manager)
    server.telescope_tools = TelescopeTools(mock_device_manager)
    server.camera_tools = CameraTools(mock_device_manager)
    
    return server


@pytest.fixture
def initialize_request():
    """Create initialize request."""
    return InitializeRequest(
        protocolVersion="2024-11-05",
        capabilities={},
        clientInfo={"name": "test-client", "version": "1.0"}
    )


@pytest.fixture
def list_tools_request():
    """Create list tools request."""
    return ListToolsRequest()


@pytest.fixture
def call_tool_request():
    """Factory for creating tool call requests."""
    def _make_request(tool_name: str, arguments: Dict[str, Any]):
        return CallToolRequest(
            name=tool_name,
            arguments=arguments
        )
    return _make_request
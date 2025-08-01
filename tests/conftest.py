"""Pytest configuration and fixtures."""

import asyncio
import uuid
from typing import Any
from unittest.mock import MagicMock, AsyncMock

import pytest
import structlog
from fastmcp import Context
from mcp.types import CallToolRequest, InitializeRequest, ListToolsRequest


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
    # Properties (synchronous)
    telescope.Connected = True
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
    
    # Methods (synchronous - alpyca uses synchronous methods)
    telescope.Park = MagicMock()
    telescope.Unpark = MagicMock()
    telescope.SlewToCoordinatesAsync = MagicMock()  # Despite name, this is sync in alpyca
    telescope.SlewToCoordinates = MagicMock()
    telescope.AbortSlew = MagicMock()
    telescope.FindHome = MagicMock()
    telescope.SetTracking = MagicMock()
    
    return telescope


@pytest.fixture
def mock_camera():
    """Mock ASCOM camera device."""
    camera = MagicMock()
    # Properties (synchronous)
    camera.Connected = True
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
    
    # Methods (synchronous - alpyca uses synchronous methods)
    camera.StartExposure = MagicMock()
    camera.StopExposure = MagicMock()
    camera.AbortExposure = MagicMock()
    camera.ImageArray = MagicMock(return_value=[[0] * 100] * 100)
    
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
            "ApiVersion": 1,
        },
        {
            "DeviceName": "Mock Camera",
            "DeviceType": "Camera",
            "DeviceNumber": 0,
            "UniqueID": "mock-camera-001",
            "Host": "localhost",
            "Port": 11111,
            "ApiVersion": 1,
        },
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
            DeviceInfo(
                {
                    "DeviceName": "Mock Telescope",
                    "DeviceType": "Telescope",
                    "DeviceNumber": 0,
                    "Host": "localhost",
                    "Port": 11111,
                }
            ),
            DeviceInfo(
                {
                    "DeviceName": "Mock Camera",
                    "DeviceType": "Camera",
                    "DeviceNumber": 0,
                    "Host": "localhost",
                    "Port": 11111,
                }
            ),
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
    # Replace device manager with mock
    from ascom_mcp import devices
    from ascom_mcp.server_fastmcp import mcp
    from ascom_mcp.tools.camera import CameraTools
    from ascom_mcp.tools.discovery import DiscoveryTools
    from ascom_mcp.tools.telescope import TelescopeTools

    devices.manager._instance = mock_device_manager

    # Initialize tools
    discovery_tools = DiscoveryTools(mock_device_manager)
    telescope_tools = TelescopeTools(mock_device_manager)
    camera_tools = CameraTools(mock_device_manager)

    # Store tools for access in tests
    mcp._discovery_tools = discovery_tools
    mcp._telescope_tools = telescope_tools
    mcp._camera_tools = camera_tools

    return mcp


@pytest.fixture
def initialize_request():
    """Create initialize request."""
    return InitializeRequest(
        protocolVersion="2025-06-18",
        capabilities={},
        clientInfo={"name": "test-client", "version": "1.0"},
    )


@pytest.fixture
def list_tools_request():
    """Create list tools request."""
    return ListToolsRequest()


@pytest.fixture
def call_tool_request():
    """Factory for creating tool call requests."""

    def _make_request(tool_name: str, arguments: dict[str, Any]):
        return CallToolRequest(name=tool_name, arguments=arguments)

    return _make_request


@pytest.fixture
def mock_context():
    """Mock FastMCP Context for testing."""
    ctx = MagicMock(spec=Context)
    ctx.logger = structlog.get_logger()
    ctx.request_id = str(uuid.uuid4())
    
    # Add any additional context attributes needed for tests
    ctx.meta = {}
    ctx.session_id = str(uuid.uuid4())
    
    return ctx


@pytest.fixture
def mock_simulator_device():
    """Mock simulator device info."""
    return {
        "DeviceName": "seestar_simulator (Simulator)",
        "DeviceType": "Telescope", 
        "DeviceNumber": 99,
        "UniqueID": "simulator_localhost_4700",
        "Host": "localhost",
        "Port": 4700,
        "ApiVersion": 1,
        "IsSimulator": True
    }


@pytest.fixture
def mock_device_discovery():
    """Mock device discovery for MCP tests."""
    from unittest.mock import patch, AsyncMock
    from ascom_mcp.devices.manager import DeviceInfo
    
    mock_devices = [
        DeviceInfo({
            "DeviceName": "Test Telescope",
            "DeviceType": "Telescope", 
            "DeviceNumber": 0,
            "UniqueID": "test-telescope-001",
            "Host": "localhost",
            "Port": 11111,
            "ApiVersion": 1
        }),
        DeviceInfo({
            "DeviceName": "Test Camera",
            "DeviceType": "Camera",
            "DeviceNumber": 0,
            "UniqueID": "test-camera-001",
            "Host": "localhost",
            "Port": 11111,
            "ApiVersion": 1
        })
    ]
    
    # Mock discover_devices to return test devices
    with patch('ascom_mcp.devices.manager.DeviceManager.discover_devices', AsyncMock(return_value=mock_devices)):
        # Also add the devices to available devices
        with patch('ascom_mcp.devices.manager.DeviceManager._available_devices', {d.id: d for d in mock_devices}):
            yield mock_devices


@pytest.fixture
def mock_connected_telescope(mock_telescope, mock_device_discovery):
    """Mock a connected telescope for MCP tests."""
    from unittest.mock import patch, MagicMock
    from ascom_mcp.devices.manager import ConnectedDevice, DeviceInfo
    
    device_info = DeviceInfo({
        "DeviceName": "Test Telescope",
        "DeviceType": "Telescope",
        "DeviceNumber": 0,
        "UniqueID": "test-telescope-001",
        "Host": "localhost", 
        "Port": 11111,
        "ApiVersion": 1
    })
    
    connected_device = MagicMock()
    connected_device.info = device_info
    connected_device.client = mock_telescope
    connected_device.number = 0
    
    with patch('ascom_mcp.devices.manager.DeviceManager.get_connected_device', return_value=connected_device):
        with patch('ascom_mcp.devices.manager.DeviceManager._connected_devices', {"Telescope_0": connected_device}):
            yield connected_device


@pytest.fixture
async def device_manager_with_simulator(mock_telescope):
    """Create device manager configured for simulator."""
    from ascom_mcp.devices.manager import DeviceManager, DeviceInfo
    
    # Set environment for simulator
    import os
    os.environ["ASCOM_SIMULATOR_DEVICES"] = "localhost:4700:seestar_simulator"
    
    manager = DeviceManager()
    manager._session = MagicMock()
    
    # Mock discovery to include simulator
    async def mock_discover(timeout=5.0):
        devices = [
            DeviceInfo({
                "DeviceType": "Telescope",
                "DeviceNumber": 99,
                "DeviceName": "seestar_simulator (Simulator)",
                "Host": "localhost",
                "Port": 4700,
                "ApiVersion": 1
            })
        ]
        manager._available_devices = {d.id: d for d in devices}
        return devices
    
    manager.discover_devices = mock_discover
    
    # Mock alpaca constructor for simulator
    from unittest.mock import patch
    
    # We'll patch alpyca at the module level when needed
    await manager.initialize()
    return manager


@pytest.fixture  
def simulator_environment():
    """Set up environment for simulator testing."""
    import os
    old_env = os.environ.copy()
    
    # Set simulator configuration
    os.environ["ASCOM_SIMULATOR_DEVICES"] = "localhost:4700:seestar_simulator"
    os.environ["ASCOM_KNOWN_DEVICES"] = "localhost:5555:seestar_alp"
    
    yield
    
    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)

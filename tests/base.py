"""Base test classes for extensible ASCOM device testing."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ascom_mcp.devices.manager import ConnectedDevice, DeviceInfo, DeviceManager

if TYPE_CHECKING:
    pass


class BaseDeviceTest(ABC):
    """Base test class for any ASCOM device type.

    Subclass this for each device type (telescope, camera, etc.)
    and override the abstract properties.
    """

    @property
    @abstractmethod
    def device_type(self) -> str:
        """Device type name (e.g., 'Telescope', 'Camera')."""
        pass

    @property
    @abstractmethod
    def required_properties(self) -> list[str]:
        """List of required ASCOM properties for this device type."""
        pass

    def test_device_has_required_properties(self, mock_device):
        """Test that device has all required ASCOM properties."""
        for prop in self.required_properties:
            assert hasattr(mock_device, prop), f"Missing required property: {prop}"

    def test_device_connection_lifecycle(self, mock_device):
        """Test device can be connected and disconnected."""
        # Initially disconnected
        assert mock_device.Connected is False

        # Connect
        mock_device.Connected = True
        assert mock_device.Connected is True

        # Disconnect
        mock_device.Connected = False
        assert mock_device.Connected is False

    def test_device_info_properties(self, mock_device):
        """Test device provides required info properties."""
        assert hasattr(mock_device, 'Description')
        assert hasattr(mock_device, 'DriverInfo')
        assert hasattr(mock_device, 'DriverVersion')
        assert hasattr(mock_device, 'InterfaceVersion')


class BaseToolTest(ABC):
    """Base test class for device tool implementations.

    Provides common test patterns for all device tools.
    """

    @property
    @abstractmethod
    def tool_class(self) -> type[Any]:
        """Tool class being tested."""
        pass

    @property
    @abstractmethod
    def device_type(self) -> str:
        """Device type for this tool."""
        pass

    @pytest.fixture
    def mock_manager(self):
        """Mock device manager."""
        return AsyncMock(spec=DeviceManager)

    @pytest.fixture
    def tool_instance(self, mock_manager):
        """Create tool instance with mock manager."""
        return self.tool_class(mock_manager)

    @pytest.mark.asyncio
    async def test_connect_returns_success_dict(self, tool_instance, mock_manager):
        """Test connect returns standard success response."""
        # Setup
        device_info = DeviceInfo({
            "DeviceType": self.device_type,
            "DeviceNumber": 0,
            "DeviceName": f"Test {self.device_type}"
        })
        mock_device = MagicMock()
        mock_device.Connected = True
        connected = ConnectedDevice(device_info, mock_device)
        mock_manager.connect_device.return_value = connected

        # Execute
        result = await tool_instance.connect(f"{self.device_type.lower()}_0")

        # Verify standard response format
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True
        assert "message" in result

    @pytest.mark.asyncio
    async def test_error_returns_standard_format(self, tool_instance, mock_manager):
        """Test errors return standard format."""
        # Setup to fail
        mock_manager.connect_device.side_effect = Exception("Test error")

        # Execute
        result = await tool_instance.connect("invalid_device")

        # Verify error format
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]


class BaseIntegrationTest(ABC):
    """Base class for integration tests.

    Provides patterns for testing complete workflows.
    """

    @property
    @abstractmethod
    def device_types(self) -> list[str]:
        """List of device types used in this integration test."""
        pass

    @pytest.fixture
    async def connected_devices(self, mock_device_manager):
        """Setup connected devices for integration test."""
        devices = {}
        for device_type in self.device_types:
            device_id = f"{device_type.lower()}_0"
            await mock_device_manager.connect_device(device_id)
            devices[device_type] = device_id
        return devices

    @abstractmethod
    async def test_workflow(self, mcp_server, connected_devices):
        """Test the complete workflow. Override in subclass."""
        pass

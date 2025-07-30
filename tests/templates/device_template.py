"""Template for adding tests for a new ASCOM device type.

Instructions:
1. Replace {DeviceType} with your device name (e.g., Focuser, Dome, Rotator)
2. Replace {device_type} with lowercase version
3. Update capability lists based on ASCOM spec for your device
4. Add device-specific test methods
5. Move completed file to tests/unit/tools/test_{device_type}.py
"""

import pytest
from typing import Dict, Any

from tests.base import BaseToolTest, BaseDeviceTest
from tests.fixtures import create_mock_device
# from ascom_mcp.tools.{device_type} import {DeviceType}Tools


class Test{DeviceType}Device(BaseDeviceTest):
    """Test {DeviceType} device meets ASCOM requirements."""
    
    @property
    def device_type(self) -> str:
        return "{DeviceType}"
    
    @property 
    def required_properties(self) -> list[str]:
        """Update this list based on ASCOM spec for {DeviceType}."""
        return [
            # Common properties (keep these)
            "Connected",
            "Description",
            "DriverInfo",
            "InterfaceVersion",
            
            # Add {DeviceType}-specific required properties here
            # Example: "Position", "IsMoving", etc.
        ]
    
    @pytest.fixture
    def mock_device(self):
        """Create mock {DeviceType} device."""
        return create_mock_device(
            "{DeviceType}",
            # Add device-specific capabilities here
            # Example: Position=5000, IsMoving=False
        )


class Test{DeviceType}Tools(BaseToolTest):
    """Test {DeviceType} control tools."""
    
    tool_class = {DeviceType}Tools  # Uncomment when class exists
    device_type = "{DeviceType}"
    
    # Add device-specific tests below
    
    @pytest.mark.asyncio
    async def test_connect_returns_device_info(self, tool_instance, mock_manager):
        """Test connection returns {DeviceType}-specific info."""
        # Setup mock response
        device_info = create_device_info("{DeviceType}")
        mock_{device_type} = create_mock_device(
            "{DeviceType}",
            # Add specific properties
        )
        
        # Test connection
        result = await tool_instance.connect("{device_type}_0")
        
        assert result["success"] == True
        assert result["{device_type}"]["connected"] == True
        # Add assertions for device-specific info
        
    # Example: Test a device-specific operation
    @pytest.mark.asyncio
    async def test_{operation}_success(self, tool_instance, mock_manager):
        """Test {operation} works correctly."""
        # Setup
        mock_{device_type} = self._get_connected_device(mock_manager)
        
        # Execute
        result = await tool_instance.{operation}("{device_type}_0", param1="value")
        
        # Verify
        assert result["success"] == True
        # Add specific assertions
        
    # Example: Test error handling
    @pytest.mark.asyncio
    async def test_{operation}_invalid_parameter(self, tool_instance, mock_manager):
        """Test {operation} validates parameters."""
        result = await tool_instance.{operation}(
            "{device_type}_0",
            invalid_param=-1
        )
        
        assert result["success"] == False
        assert "invalid" in result["error"].lower()
        
    # Helper method
    def _get_connected_device(self, mock_manager):
        """Helper to setup connected device."""
        from ascom_mcp.devices.manager import DeviceInfo, ConnectedDevice
        
        device_info = DeviceInfo({
            "DeviceType": "{DeviceType}",
            "DeviceNumber": 0,
            "DeviceName": "Test {DeviceType}"
        })
        mock_device = create_mock_device("{DeviceType}")
        connected = ConnectedDevice(device_info, mock_device)
        mock_manager.get_connected_device.return_value = connected
        
        return mock_device
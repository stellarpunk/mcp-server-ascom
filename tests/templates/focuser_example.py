"""Example test implementation for Focuser device.

This is a complete example showing how to test a new device type.
Copy this pattern when adding support for other devices.
"""

import pytest
from typing import Dict, Any

from tests.base import BaseToolTest, BaseDeviceTest
from tests.fixtures import create_focuser_mock, create_device_info
# Uncomment when implementing:
# from ascom_mcp.tools.focuser import FocuserTools


class TestFocuserDevice(BaseDeviceTest):
    """Test Focuser device meets ASCOM requirements."""
    
    @property
    def device_type(self) -> str:
        return "Focuser"
    
    @property 
    def required_properties(self) -> list[str]:
        return [
            # Common properties
            "Connected",
            "Description", 
            "DriverInfo",
            "InterfaceVersion",
            
            # Focuser-specific required properties
            "Position",
            "MaxStep",
            "IsMoving",
            "Absolute"
        ]
    
    @pytest.fixture
    def mock_device(self):
        """Create mock Focuser device."""
        return create_focuser_mock()


class TestFocuserTools(BaseToolTest):
    """Test Focuser control tools."""
    
    # Uncomment when class exists:
    # tool_class = FocuserTools
    device_type = "Focuser"
    
    @pytest.mark.asyncio
    async def test_connect_returns_focuser_info(self, tool_instance, mock_manager):
        """Test connection returns focuser-specific info."""
        # Setup
        from ascom_mcp.devices.manager import ConnectedDevice
        
        device_info = create_device_info("Focuser")
        mock_focuser = create_focuser_mock(
            Position=25000,
            MaxStep=50000,
            Temperature=18.5
        )
        connected = ConnectedDevice(device_info, mock_focuser)
        mock_manager.connect_device.return_value = connected
        
        # Execute
        result = await tool_instance.connect("focuser_0")
        
        # Verify
        assert result["success"] == True
        assert result["focuser"]["connected"] == True
        assert result["focuser"]["position"] == 25000
        assert result["focuser"]["max_position"] == 50000
        assert result["focuser"]["temperature"] == 18.5
        
    @pytest.mark.asyncio
    async def test_move_absolute_success(self, tool_instance, mock_manager):
        """Test moving focuser to absolute position."""
        # Setup
        mock_focuser = self._get_connected_focuser(mock_manager)
        mock_focuser.Position = 25000
        mock_focuser.IsMoving = False
        
        # Execute
        result = await tool_instance.move_absolute("focuser_0", position=30000)
        
        # Verify
        assert result["success"] == True
        assert result["message"] == "Moving focuser to position 30000"
        mock_focuser.Move.assert_called_once_with(30000)
        
    @pytest.mark.asyncio
    async def test_move_absolute_validates_range(self, tool_instance, mock_manager):
        """Test move validates position is within range."""
        # Setup
        mock_focuser = self._get_connected_focuser(mock_manager)
        mock_focuser.MaxStep = 50000
        
        # Test beyond max
        result = await tool_instance.move_absolute("focuser_0", position=60000)
        
        assert result["success"] == False
        assert "exceeds maximum" in result["error"]
        mock_focuser.Move.assert_not_called()
        
        # Test negative
        result = await tool_instance.move_absolute("focuser_0", position=-100)
        
        assert result["success"] == False
        assert "must be positive" in result["error"]
        
    @pytest.mark.asyncio
    async def test_move_relative_success(self, tool_instance, mock_manager):
        """Test relative focuser movement."""
        # Setup
        mock_focuser = self._get_connected_focuser(mock_manager)
        mock_focuser.Position = 25000
        mock_focuser.MaxStep = 50000
        
        # Execute - move in
        result = await tool_instance.move_relative("focuser_0", steps=1000)
        
        assert result["success"] == True
        assert result["new_position"] == 26000
        mock_focuser.Move.assert_called_with(26000)
        
        # Execute - move out
        result = await tool_instance.move_relative("focuser_0", steps=-2000)
        
        assert result["new_position"] == 23000
        
    @pytest.mark.asyncio
    async def test_move_while_moving_error(self, tool_instance, mock_manager):
        """Test error when trying to move while already moving."""
        # Setup
        mock_focuser = self._get_connected_focuser(mock_manager)
        mock_focuser.IsMoving = True
        
        # Execute
        result = await tool_instance.move_absolute("focuser_0", position=30000)
        
        # Verify
        assert result["success"] == False
        assert "already moving" in result["error"].lower()
        mock_focuser.Move.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_halt_movement(self, tool_instance, mock_manager):
        """Test halting focuser movement."""
        # Setup
        mock_focuser = self._get_connected_focuser(mock_manager)
        mock_focuser.IsMoving = True
        mock_focuser.CanHalt = True
        
        # Execute
        result = await tool_instance.halt("focuser_0")
        
        # Verify
        assert result["success"] == True
        mock_focuser.Halt.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_status(self, tool_instance, mock_manager):
        """Test getting focuser status."""
        # Setup
        mock_focuser = self._get_connected_focuser(mock_manager)
        mock_focuser.Position = 30000
        mock_focuser.IsMoving = True
        mock_focuser.Temperature = 15.2
        mock_focuser.TempComp = True
        
        # Execute
        result = await tool_instance.get_status("focuser_0")
        
        # Verify
        assert result["success"] == True
        assert result["status"]["position"] == 30000
        assert result["status"]["is_moving"] == True
        assert result["status"]["temperature"] == 15.2
        assert result["status"]["temp_comp_enabled"] == True
        
    # Helper method
    def _get_connected_focuser(self, mock_manager):
        """Helper to setup connected focuser."""
        from ascom_mcp.devices.manager import DeviceInfo, ConnectedDevice
        
        device_info = create_device_info("Focuser")
        mock_focuser = create_focuser_mock()
        connected = ConnectedDevice(device_info, mock_focuser)
        mock_manager.get_connected_device.return_value = connected
        
        return mock_focuser
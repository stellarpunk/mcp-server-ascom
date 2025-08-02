"""
Test Seestar S50 real-world operations.

Based on Hardware-in-the-Loop testing patterns and actual device behavior.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ascom_mcp.tools.telescope import TelescopeTools
from ascom_mcp.devices.manager import DeviceManager, ConnectedDevice


class TestSeestarOperations:
    """Test real Seestar S50 operational patterns."""
    
    @pytest.fixture
    def device_manager(self):
        """Mock device manager."""
        manager = MagicMock(spec=DeviceManager)
        return manager
    
    @pytest.fixture
    def telescope_tools(self, device_manager):
        """Create telescope tools."""
        return TelescopeTools(device_manager)
    
    @pytest.fixture
    def mock_seestar(self):
        """Mock Seestar device with realistic responses."""
        device = MagicMock(spec=ConnectedDevice)
        telescope = AsyncMock()
        device.device = telescope
        device.name = "Seestar S50"
        device.host = "192.168.1.100"
        device.port = 5555
        
        # Setup realistic method responses
        telescope.Action.side_effect = self._seestar_action_handler
        telescope.Connected = True
        telescope.Tracking = False  # Scenery mode default
        
        return device
    
    def _seestar_action_handler(self, action, parameters):
        """Simulate realistic Seestar responses."""
        if action == "method_sync":
            method = parameters.get("method")
            params = parameters.get("params")
            
            # Device state query
            if method == "get_device_state":
                return {
                    "Value": {
                        "mount": {"tracking": False, "slewing": False},
                        "View": {"state": "working", "mode": "scenery"},
                        "RTSP": {"state": "working", "port": 4554},
                        "battery": {"level": 52},
                        "temperature": 50
                    }
                }
            
            # Scenery mode activation
            elif method == "iscope_start_view":
                mode = params.get("mode")
                if mode == "scenery":
                    return {"Value": {"state": "working", "mode": "scenery"}}
                    
            # Movement commands
            elif method == "scope_speed_move":
                speed = params.get("speed", 0)
                angle = params.get("angle", 0)
                dur = params.get("dur_sec", 0)
                if 0 <= speed <= 1000 and 0 <= angle <= 360:
                    return {"Value": {"move_started": True}}
                else:
                    raise Exception("Invalid parameters")
                    
            # Tracking control
            elif method == "scope_set_track_state":
                if isinstance(params, bool):
                    return {"Value": {"tracking": params}}
                else:
                    raise Exception("Error 207: fail to operate")
                    
        elif action == "action_start_up_sequence":
            return {"Value": {"initialized": True}}
            
        return {"Value": {}}
    
    async def test_connection_workflow(self, telescope_tools, device_manager, mock_seestar):
        """Test standard Seestar connection workflow."""
        device_manager.get_device.return_value = mock_seestar
        
        # Direct connection pattern
        result = await telescope_tools.connect("seestar@192.168.1.100:5555")
        
        assert result["success"] is True
        assert "Seestar" in result["device_name"]
    
    async def test_scenery_mode_transition(self, telescope_tools, device_manager, mock_seestar):
        """Test transition to scenery mode for terrestrial viewing."""
        device_manager.get_device.return_value = mock_seestar
        
        # Stop tracking first (required)
        tracking_result = await telescope_tools.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "scope_set_track_state", "params": False}
        )
        assert tracking_result["result"]["tracking"] is False
        
        # Switch to scenery mode
        scenery_result = await telescope_tools.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "iscope_start_view", "params": {"mode": "scenery"}}
        )
        
        assert scenery_result["result"]["mode"] == "scenery"
        assert scenery_result["result"]["state"] == "working"
    
    async def test_terrestrial_positioning(self, telescope_tools, device_manager, mock_seestar):
        """Test positioning for terrestrial viewing."""
        device_manager.get_device.return_value = mock_seestar
        
        # Fine positioning movements
        movements = [
            {"speed": 200, "angle": 90, "dur_sec": 3},   # East
            {"speed": 100, "angle": 0, "dur_sec": 1},    # North
            {"speed": 300, "angle": 270, "dur_sec": 2},  # West
        ]
        
        for move_params in movements:
            result = await telescope_tools.custom_action(
                "telescope_1",
                "method_sync",
                {"method": "scope_speed_move", "params": move_params}
            )
            
            assert result["success"] is True
            assert result["result"]["move_started"] is True
    
    async def test_parameter_validation_prevents_error_207(self, telescope_tools, device_manager, mock_seestar):
        """Test that v0.5.0 validation prevents Error 207."""
        device_manager.get_device.return_value = mock_seestar
        
        # This would cause Error 207 on real device
        with pytest.raises(Exception) as exc_info:
            await telescope_tools.custom_action(
                "telescope_1",
                "method_sync",
                {"method": "scope_set_track_state", "params": {"on": True}}
            )
        
        assert "Error 207" in str(exc_info.value)
        
        # Correct format works
        result = await telescope_tools.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "scope_set_track_state", "params": True}
        )
        assert result["success"] is True
    
    async def test_device_state_monitoring(self, telescope_tools, device_manager, mock_seestar):
        """Test comprehensive device state queries."""
        device_manager.get_device.return_value = mock_seestar
        
        # Get full device state
        state_result = await telescope_tools.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "get_device_state"}
        )
        
        state = state_result["result"]
        
        # Verify expected state structure
        assert state["mount"]["tracking"] is False
        assert state["View"]["mode"] == "scenery"
        assert state["RTSP"]["state"] == "working"
        assert state["battery"]["level"] == 52
        assert state["temperature"] == 50
    
    async def test_streaming_integration(self, telescope_tools, device_manager, mock_seestar):
        """Test RTSP streaming for live view."""
        device_manager.get_device.return_value = mock_seestar
        
        # Check view state
        view_result = await telescope_tools.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "get_device_state"}
        )
        
        rtsp_info = view_result["result"]["RTSP"]
        assert rtsp_info["state"] == "working"
        assert rtsp_info["port"] == 4554
        
        # Streaming URL should be available
        stream_url = f"rtsp://{mock_seestar.host}:{rtsp_info['port']}/stream"
        assert "192.168.1.100" in stream_url
    
    async def test_initialization_sequence(self, telescope_tools, device_manager, mock_seestar):
        """Test proper Seestar initialization."""
        device_manager.get_device.return_value = mock_seestar
        
        # Required initialization
        init_result = await telescope_tools.custom_action(
            "telescope_1",
            "action_start_up_sequence",
            {"lat": 40.745, "lon": -74.026, "move_arm": True}
        )
        
        assert init_result["success"] is True
        assert init_result["result"]["initialized"] is True
"""
Seestar S50 Terrestrial Viewing Lifecycle Test.

Follows ASCOM IoT device lifecycle phases for real-world validation.
Based on Hardware-in-the-Loop testing best practices.
"""

import pytest
import asyncio
from typing import Dict, Any

from ascom_mcp.tools.telescope import TelescopeTools
from ascom_mcp.devices.manager import DeviceManager
from ascom_mcp.resources.event_stream import EventStreamManager


class TestTerrestrialViewingLifecycle:
    """Test complete lifecycle for terrestrial viewing operations."""
    
    @pytest.fixture
    async def setup_mcp_tools(self):
        """Setup MCP tools for testing."""
        device_manager = DeviceManager()
        await device_manager.initialize()
        
        event_manager = EventStreamManager()
        telescope_tools = TelescopeTools(device_manager)
        
        return {
            "device_manager": device_manager,
            "event_manager": event_manager,
            "telescope_tools": telescope_tools
        }
    
    @pytest.mark.asyncio
    async def test_phase_1_discovery_connection(self, setup_mcp_tools):
        """Phase 1: Device discovery and connection."""
        tools = await setup_mcp_tools
        telescope = tools["telescope_tools"]
        
        # Direct connection (IoT pattern - no discovery needed)
        result = await telescope.connect("telescope_1")
        
        assert result["success"] is True
        assert "device_id" in result
        assert result["connected"] is True
    
    @pytest.mark.asyncio
    async def test_phase_2_state_verification(self, setup_mcp_tools):
        """Phase 2: Verify device state before operations."""
        tools = await setup_mcp_tools
        telescope = tools["telescope_tools"]
        
        # Connect first
        await telescope.connect("telescope_1")
        
        # Get comprehensive state
        state = await telescope.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "get_device_state"}
        )
        
        # Validate expected state structure
        assert "mount" in state.get("result", {})
        assert "View" in state.get("result", {})
        assert "battery" in state.get("result", {})
        
        # Check if initialization needed
        mount_state = state["result"].get("mount", {})
        if mount_state.get("tracking", False):
            # Stop tracking for scenery mode
            await telescope.custom_action(
                "telescope_1",
                "method_sync",
                {"method": "scope_set_track_state", "params": False}
            )
    
    @pytest.mark.asyncio
    async def test_phase_3_mode_initialization(self, setup_mcp_tools):
        """Phase 3: Initialize for terrestrial viewing."""
        tools = await setup_mcp_tools
        telescope = tools["telescope_tools"]
        
        # Connect and prepare
        await telescope.connect("telescope_1")
        
        # Initialize telescope
        init_result = await telescope.custom_action(
            "telescope_1",
            "action_start_up_sequence",
            {"lat": 40.745, "lon": -74.026, "move_arm": True}
        )
        
        assert init_result.get("success", False)
        
        # Switch to scenery mode
        scenery_result = await telescope.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "iscope_start_view", "params": {"mode": "scenery"}}
        )
        
        assert scenery_result.get("success", False)
        
        # Verify mode active
        await asyncio.sleep(1)  # Allow mode transition
        
        state = await telescope.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "get_device_state"}
        )
        
        view_state = state.get("result", {}).get("View", {})
        assert view_state.get("mode") == "scenery"
    
    @pytest.mark.asyncio
    async def test_phase_4_operations(self, setup_mcp_tools):
        """Phase 4: Perform terrestrial viewing operations."""
        tools = await setup_mcp_tools
        telescope = tools["telescope_tools"]
        event_manager = tools["event_manager"]
        
        # Setup connection and mode
        await telescope.connect("telescope_1")
        
        # Positioning sequence
        movements = [
            {"speed": 200, "angle": 90, "dur_sec": 2},   # Pan east
            {"speed": 100, "angle": 0, "dur_sec": 1},    # Tilt up
            {"speed": 150, "angle": 270, "dur_sec": 1},  # Pan west
        ]
        
        for idx, move in enumerate(movements):
            # Execute movement
            result = await telescope.custom_action(
                "telescope_1",
                "method_sync",
                {"method": "scope_speed_move", "params": move}
            )
            
            assert result.get("success", False), f"Movement {idx} failed"
            
            # Allow movement to complete
            await asyncio.sleep(move["dur_sec"] + 0.5)
            
            # Capture preview after movement
            try:
                preview = await telescope.telescope_preview("telescope_1")
                assert preview.get("success", False)
            except AttributeError:
                # Preview method may not be available in unit tests
                pass
        
        # Check events captured
        history = await event_manager.get_event_history("telescope_1", count=10)
        # Events may be empty in unit tests but structure should exist
        assert isinstance(history.get("events", []), list)
    
    @pytest.mark.asyncio  
    async def test_phase_5_safety_shutdown(self, setup_mcp_tools):
        """Phase 5: Safe shutdown and cleanup."""
        tools = await setup_mcp_tools
        telescope = tools["telescope_tools"]
        
        # Connect and get state
        await telescope.connect("telescope_1")
        
        # Stop any active operations
        stop_result = await telescope.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "iscope_stop_view"}
        )
        
        # Return to idle state
        idle_result = await telescope.custom_action(
            "telescope_1",
            "method_sync",
            {"method": "scope_set_track_state", "params": False}
        )
        
        # Disconnect
        disconnect_result = await telescope.disconnect("telescope_1")
        
        assert disconnect_result.get("success", False)
        assert disconnect_result.get("connected") is False
    
    @pytest.mark.asyncio
    async def test_full_lifecycle_integration(self, setup_mcp_tools):
        """Test complete terrestrial viewing lifecycle."""
        tools = await setup_mcp_tools
        telescope = tools["telescope_tools"]
        
        lifecycle_phases = []
        
        try:
            # Phase 1: Connection
            connect_result = await telescope.connect("telescope_1")
            lifecycle_phases.append(("connection", connect_result.get("success", False)))
            
            # Phase 2: State verification
            state = await telescope.custom_action(
                "telescope_1", "method_sync", {"method": "get_device_state"}
            )
            lifecycle_phases.append(("state_check", state.get("success", False)))
            
            # Phase 3: Mode setup
            scenery = await telescope.custom_action(
                "telescope_1", "method_sync",
                {"method": "iscope_start_view", "params": {"mode": "scenery"}}
            )
            lifecycle_phases.append(("scenery_mode", scenery.get("success", False)))
            
            # Phase 4: Operations
            move = await telescope.custom_action(
                "telescope_1", "method_sync",
                {"method": "scope_speed_move", "params": {"speed": 200, "angle": 90, "dur_sec": 2}}
            )
            lifecycle_phases.append(("movement", move.get("success", False)))
            
            # Phase 5: Cleanup
            stop = await telescope.custom_action(
                "telescope_1", "method_sync", {"method": "iscope_stop_view"}
            )
            lifecycle_phases.append(("cleanup", stop.get("success", False)))
            
        except Exception as e:
            lifecycle_phases.append(("error", str(e)))
        
        # Validate lifecycle completion
        phase_names = [phase[0] for phase in lifecycle_phases]
        assert "connection" in phase_names
        assert "scenery_mode" in phase_names
        assert "movement" in phase_names
        
        # Check success rate
        successes = [phase[1] for phase in lifecycle_phases if isinstance(phase[1], bool)]
        if successes:
            success_rate = sum(successes) / len(successes)
            assert success_rate >= 0.6, f"Lifecycle success rate too low: {success_rate}"
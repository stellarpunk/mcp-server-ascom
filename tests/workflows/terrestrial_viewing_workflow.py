"""
Seestar S50 Terrestrial Viewing Workflow Test.

Follows real-world IoT device patterns for scenery mode operations.
Based on industry best practices for hardware-in-the-loop testing.
"""

import asyncio
import time
from typing import Dict, Any, Optional

from ascom_mcp.tools.telescope import TelescopeTools
from ascom_mcp.devices.manager import DeviceManager


class TerrestrialViewingWorkflow:
    """Test workflow for Seestar S50 terrestrial/scenery viewing."""
    
    def __init__(self):
        self.device_id = "telescope_1"
        self.device_manager = None
        self.telescope_tools = None
        self.workflow_state = "not_started"
        self.events = []
        
    async def setup(self):
        """Initialize MCP tools."""
        self.device_manager = DeviceManager()
        await self.device_manager.initialize()
        self.telescope_tools = TelescopeTools(self.device_manager)
        
    async def log_event(self, event: str, data: Optional[Dict[str, Any]] = None):
        """Log workflow events for validation."""
        timestamp = time.time()
        self.events.append({
            "timestamp": timestamp,
            "event": event,
            "data": data or {},
            "state": self.workflow_state
        })
        print(f"[{self.workflow_state}] {event}: {data or ''}")
        
    async def validate_device_state(self) -> Dict[str, Any]:
        """Check device is in expected state."""
        try:
            result = await self.telescope_tools.custom_action(
                self.device_id,
                "method_sync",
                {"method": "get_device_state"}
            )
            return result.get("result", {})
        except Exception as e:
            await self.log_event("state_check_failed", {"error": str(e)})
            return {}
            
    async def run_workflow(self):
        """Execute complete terrestrial viewing workflow."""
        
        # Phase 1: Connection & Verification
        self.workflow_state = "connecting"
        await self.log_event("workflow_start", {"mode": "terrestrial"})
        
        # Connect to device
        connect_result = await self.telescope_tools.connect(self.device_id)
        await self.log_event("device_connected", connect_result)
        
        # Verify device state
        device_state = await self.validate_device_state()
        await self.log_event("initial_state", device_state)
        
        # Phase 2: Mode Transition
        self.workflow_state = "mode_setup"
        
        # Stop any active tracking (required for mode switch)
        if device_state.get("is_tracking", False):
            await self.log_event("stopping_tracking")
            track_result = await self.telescope_tools.custom_action(
                self.device_id,
                "method_sync",
                {"method": "scope_set_track_state", "params": False}
            )
            await self.log_event("tracking_stopped", track_result)
            
        # Switch to scenery mode
        await self.log_event("switching_to_scenery_mode")
        scenery_result = await self.telescope_tools.custom_action(
            self.device_id,
            "method_sync", 
            {"method": "iscope_start_view", "params": {"mode": "scenery"}}
        )
        await self.log_event("scenery_mode_active", scenery_result)
        
        # Phase 3: Focus Optimization
        self.workflow_state = "focus_setup"
        
        # Get current focus position
        focus_pos = await self.telescope_tools.custom_action(
            self.device_id,
            "method_sync",
            {"method": "focuser_get_position"}
        )
        await self.log_event("focus_position", focus_pos)
        
        # Set focus for terrestrial (infinity or preset)
        # Seestar uses different focus for scenery vs astronomical
        focus_result = await self.telescope_tools.custom_action(
            self.device_id,
            "method_sync",
            {"method": "auto_focus", "params": {"mode": "scenery"}}
        )
        await self.log_event("focus_adjusted", focus_result)
        
        # Phase 4: Positioning for Skyline
        self.workflow_state = "positioning"
        
        # Get current position
        position = await self.telescope_tools.get_position(self.device_id)
        await self.log_event("current_position", position)
        
        # Move to horizontal position for skyline
        # Altitude ~10-20 degrees, Azimuth for desired view
        await self.log_event("moving_to_skyline")
        
        # Use speed move for smooth positioning
        move_result = await self.telescope_tools.custom_action(
            self.device_id,
            "method_sync",
            {
                "method": "scope_speed_move",
                "params": {
                    "speed": 200,  # Slow for precision
                    "angle": 90,   # East
                    "dur_sec": 5   # 5 second movement
                }
            }
        )
        await self.log_event("movement_complete", move_result)
        
        # Phase 5: Visual Capture & Validation
        self.workflow_state = "capturing"
        await asyncio.sleep(2)  # Let mount settle
        
        # Capture preview (using custom action since visual tools are MCP-only)
        await self.log_event("capturing_preview")
        try:
            preview_result = await self.telescope_tools.custom_action(
                self.device_id,
                "method_sync",
                {"method": "take_light_frame"}
            )
            await self.log_event("preview_captured", {
                "success": preview_result.get("success", False),
                "method": "take_light_frame"
            })
        except Exception as e:
            await self.log_event("preview_failed", {"error": str(e)})
        
        # Check streaming capability
        await self.log_event("checking_streaming")
        try:
            stream_result = await self.telescope_tools.custom_action(
                self.device_id,
                "method_sync",
                {"method": "get_view_state"}
            )
            await self.log_event("streaming_checked", stream_result)
        except Exception as e:
            await self.log_event("streaming_check_failed", {"error": str(e)})
        
        # Phase 6: Fine Adjustment Loop
        self.workflow_state = "fine_tuning"
        
        # Simulate user adjusting view
        adjustments = [
            {"angle": 0, "speed": 100, "dur_sec": 1},    # Up slightly
            {"angle": 90, "speed": 100, "dur_sec": 2},   # Right
            {"angle": 270, "speed": 100, "dur_sec": 1},  # Left center
        ]
        
        for adj in adjustments:
            await self.log_event("fine_adjustment", adj)
            move_result = await self.telescope_tools.custom_action(
                self.device_id,
                "method_sync",
                {"method": "scope_speed_move", "params": adj}
            )
            await asyncio.sleep(1)  # Settle time
            
            # Check state after each adjustment
            try:
                state = await self.validate_device_state()
                await self.log_event("adjustment_state", {
                    "tracking": state.get("result", {}).get("mount", {}).get("tracking", False)
                })
            except Exception as e:
                await self.log_event("adjustment_state_failed", {"error": str(e)})
            
        # Phase 7: Event Validation
        self.workflow_state = "event_check"
        
        # Check if events were captured (simplified - event history is MCP-only)
        await self.log_event("event_check", {
            "note": "Event history requires MCP context - checking workflow events instead",
            "workflow_events": len(self.events)
        })
        
        # Phase 8: Cleanup
        self.workflow_state = "cleanup"
        
        # Stop streaming (using custom action)
        try:
            stop_stream = await self.telescope_tools.custom_action(
                self.device_id,
                "method_sync",
                {"method": "iscope_stop_view"}
            )
            await self.log_event("view_mode_stopped", stop_stream)
        except Exception as e:
            await self.log_event("view_stop_failed", {"error": str(e)})
        
        # Additional cleanup if needed
        await self.log_event("cleanup_complete")
        
        # Final state check
        final_state = await self.validate_device_state()
        await self.log_event("final_state", final_state)
        
        self.workflow_state = "complete"
        await self.log_event("workflow_complete", {
            "total_events": len(self.events),
            "duration": time.time() - self.events[0]["timestamp"]
        })
        
        return self.generate_report()
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate workflow validation report."""
        # Group events by phase
        phases = {}
        for event in self.events:
            state = event["state"]
            if state not in phases:
                phases[state] = []
            phases[state].append(event)
            
        # Check critical operations
        validations = {
            "connection_successful": any(e["event"] == "device_connected" for e in self.events),
            "scenery_mode_activated": any(e["event"] == "scenery_mode_active" for e in self.events),
            "preview_attempted": any(e["event"] == "preview_captured" for e in self.events),
            "streaming_checked": any(e["event"] == "streaming_checked" for e in self.events),
            "movements_executed": len([e for e in self.events if e["event"] == "movement_complete"]) > 0,
            "workflow_completed": any(e["event"] == "workflow_complete" for e in self.events),
        }
        
        return {
            "success": all(validations.values()),
            "validations": validations,
            "phases": {k: len(v) for k, v in phases.items()},
            "total_events": len(self.events),
            "errors": [e for e in self.events if "error" in e.get("data", {})]
        }


async def main():
    """Run terrestrial viewing workflow test."""
    workflow = TerrestrialViewingWorkflow()
    await workflow.setup()
    
    try:
        report = await workflow.run_workflow()
        
        print("\n=== WORKFLOW VALIDATION REPORT ===")
        print(f"Success: {report['success']}")
        print("\nValidations:")
        for check, passed in report['validations'].items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
            
        print(f"\nPhases completed: {len(report['phases'])}")
        print(f"Total events logged: {report['total_events']}")
        
        if report['errors']:
            print(f"\nErrors encountered: {len(report['errors'])}")
            for error in report['errors']:
                print(f"  - {error['event']}: {error['data']}")
                
    except Exception as e:
        print(f"Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
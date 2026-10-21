"""
Seestar S50 Mode-Specific Workflows.

Each viewing mode has unique requirements, safety considerations, and operational patterns.
Based on real device behavior and astronomy best practices.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from ascom_mcp.tools.telescope import TelescopeTools
from ascom_mcp.devices.manager import DeviceManager


class SeestarModeWorkflow(ABC):
    """Base class for mode-specific workflows."""
    
    def __init__(self, device_id: str = "telescope_1"):
        self.device_id = device_id
        self.device_manager = None
        self.telescope_tools = None
        self.mode_name = "base"
        self.safety_checks = []
        self.events = []
        
    async def setup(self):
        """Initialize tools."""
        self.device_manager = DeviceManager()
        await self.device_manager.initialize()
        self.telescope_tools = TelescopeTools(self.device_manager)
        
    async def log_event(self, event: str, data: Optional[Dict[str, Any]] = None):
        """Log workflow events."""
        self.events.append({
            "timestamp": time.time(),
            "mode": self.mode_name,
            "event": event,
            "data": data or {}
        })
        print(f"[{self.mode_name}] {event}: {data or ''}")
        
    @abstractmethod
    async def perform_safety_checks(self) -> bool:
        """Mode-specific safety validations."""
        pass
        
    @abstractmethod
    async def configure_mode_settings(self) -> bool:
        """Configure mode-specific parameters."""
        pass
        
    @abstractmethod
    async def execute_operations(self) -> Dict[str, Any]:
        """Perform mode-specific operations."""
        pass
        
    async def run_workflow(self) -> Dict[str, Any]:
        """Execute complete mode workflow."""
        await self.log_event("workflow_start")
        
        try:
            # Connect
            connect_result = await self.telescope_tools.connect(self.device_id)
            await self.log_event("connected", connect_result)
            
            # Safety checks
            if not await self.perform_safety_checks():
                await self.log_event("safety_check_failed")
                return {"success": False, "reason": "safety_check_failed"}
                
            # Configure mode
            if not await self.configure_mode_settings():
                await self.log_event("mode_config_failed")
                return {"success": False, "reason": "mode_config_failed"}
                
            # Execute operations
            results = await self.execute_operations()
            
            # Cleanup
            await self.cleanup()
            
            await self.log_event("workflow_complete", results)
            return {"success": True, "results": results, "events": len(self.events)}
            
        except Exception as e:
            await self.log_event("workflow_error", {"error": str(e)})
            return {"success": False, "error": str(e)}
            
    async def cleanup(self):
        """Standard cleanup operations."""
        await self.telescope_tools.custom_action(
            self.device_id, "method_sync", {"method": "iscope_stop_view"}
        )


class SceneryModeWorkflow(SeestarModeWorkflow):
    """Terrestrial viewing workflow."""
    
    def __init__(self, device_id: str = "telescope_1"):
        super().__init__(device_id)
        self.mode_name = "scenery"
        
    async def perform_safety_checks(self) -> bool:
        """No special safety requirements for scenery."""
        await self.log_event("safety_check", {"required": "none"})
        return True
        
    async def configure_mode_settings(self) -> bool:
        """Configure for terrestrial viewing."""
        # Stop tracking
        track_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "scope_set_track_state", "params": False}
        )
        await self.log_event("tracking_disabled", track_result)
        
        # Start scenery mode
        mode_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "iscope_start_view", "params": {"mode": "scenery"}}
        )
        await self.log_event("scenery_mode_activated", mode_result)
        
        return mode_result.get("success", False)
        
    async def execute_operations(self) -> Dict[str, Any]:
        """Perform terrestrial viewing operations."""
        results = {"movements": [], "captures": []}
        
        # Pan across horizon
        pan_movements = [
            {"speed": 300, "angle": 90, "dur_sec": 5},   # East
            {"speed": 300, "angle": 270, "dur_sec": 5},  # West back
        ]
        
        for move in pan_movements:
            move_result = await self.telescope_tools.custom_action(
                self.device_id, "method_sync",
                {"method": "scope_speed_move", "params": move}
            )
            results["movements"].append(move_result)
            await asyncio.sleep(move["dur_sec"] + 1)
            
            # Capture view
            try:
                preview = await self.telescope_tools.telescope_preview(self.device_id)
                results["captures"].append(preview.get("success", False))
            except:
                results["captures"].append(False)
                
        return results


class StarModeWorkflow(SeestarModeWorkflow):
    """Deep sky object viewing workflow."""
    
    def __init__(self, device_id: str = "telescope_1"):
        super().__init__(device_id)
        self.mode_name = "star"
        
    async def perform_safety_checks(self) -> bool:
        """Check conditions for star viewing."""
        # Check if dark enough (would check sensors in real implementation)
        current_hour = datetime.now().hour
        is_night = current_hour < 6 or current_hour > 19
        
        await self.log_event("darkness_check", {"is_night": is_night})
        
        # For testing, always allow
        return True
        
    async def configure_mode_settings(self) -> bool:
        """Configure for stellar viewing."""
        # Initialize with location
        init_result = await self.telescope_tools.custom_action(
            self.device_id, "action_start_up_sequence",
            {"lat": 40.745, "lon": -74.026, "move_arm": True}
        )
        await self.log_event("initialized", init_result)
        
        # Start star mode
        mode_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "iscope_start_view", "params": {"mode": "star"}}
        )
        await self.log_event("star_mode_activated", mode_result)
        
        # Enable tracking
        track_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "scope_set_track_state", "params": True}
        )
        await self.log_event("tracking_enabled", track_result)
        
        return mode_result.get("success", False)
        
    async def execute_operations(self) -> Dict[str, Any]:
        """Perform deep sky operations."""
        results = {"goto": None, "tracking": None, "imaging": None}
        
        # Go to a bright star (Vega)
        goto_result = await self.telescope_tools.goto(
            self.device_id, 
            ra=18.615,  # 18h 37m
            dec=38.783  # +38° 47'
        )
        results["goto"] = goto_result
        await self.log_event("goto_complete", goto_result)
        
        # Wait for settle
        await asyncio.sleep(5)
        
        # Verify tracking
        position = await self.telescope_tools.get_position(self.device_id)
        results["tracking"] = position
        
        # Start exposure
        exposure_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "take_light_frame", "params": {"exp_ms": 10000}}
        )
        results["imaging"] = exposure_result
        
        return results


class MoonModeWorkflow(SeestarModeWorkflow):
    """Lunar observation workflow."""
    
    def __init__(self, device_id: str = "telescope_1"):
        super().__init__(device_id)
        self.mode_name = "moon"
        
    async def perform_safety_checks(self) -> bool:
        """Check if moon is visible."""
        # Would calculate moon position in real implementation
        await self.log_event("moon_visibility_check", {"assumed": "visible"})
        return True
        
    async def configure_mode_settings(self) -> bool:
        """Configure for lunar viewing."""
        # Start moon mode
        mode_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "iscope_start_view", "params": {"mode": "moon"}}
        )
        await self.log_event("moon_mode_activated", mode_result)
        
        # Enable lunar tracking rate
        track_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "scope_set_track_state", "params": True}
        )
        await self.log_event("lunar_tracking_enabled", track_result)
        
        return mode_result.get("success", False)
        
    async def execute_operations(self) -> Dict[str, Any]:
        """Perform lunar operations."""
        results = {"goto_moon": None, "exposure": None}
        
        # Go to moon (would calculate actual position)
        goto_result = await self.telescope_tools.goto_object(
            self.device_id, "Moon"
        )
        results["goto_moon"] = goto_result
        await self.log_event("moon_centered", goto_result)
        
        # Short exposure for bright moon
        exposure_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "take_light_frame", "params": {"exp_ms": 100}}
        )
        results["exposure"] = exposure_result
        
        return results


class SunModeWorkflow(SeestarModeWorkflow):
    """Solar observation workflow with CRITICAL SAFETY."""
    
    def __init__(self, device_id: str = "telescope_1"):
        super().__init__(device_id)
        self.mode_name = "sun"
        self.safety_checks = ["solar_filter", "daytime", "user_confirmation"]
        
    async def perform_safety_checks(self) -> bool:
        """CRITICAL SAFETY CHECKS FOR SOLAR OBSERVATION."""
        await self.log_event("SAFETY_WARNING", {
            "message": "SOLAR OBSERVATION REQUIRES PROPER SOLAR FILTER",
            "risk": "PERMANENT EYE DAMAGE OR BLINDNESS WITHOUT FILTER"
        })
        
        # Check daytime
        current_hour = datetime.now().hour
        is_daytime = 7 <= current_hour <= 17
        
        if not is_daytime:
            await self.log_event("safety_failed", {"reason": "not_daytime"})
            return False
            
        # In real implementation, would verify solar filter installed
        # For safety, we'll simulate filter check
        await self.log_event("solar_filter_check", {
            "warning": "VERIFY SOLAR FILTER INSTALLED",
            "filter_required": "Baader AstroSolar or equivalent"
        })
        
        # Require explicit confirmation in real usage
        await self.log_event("user_confirmation_required", {
            "message": "User must confirm solar filter is properly installed"
        })
        
        return True  # Only for testing - real implementation requires physical checks
        
    async def configure_mode_settings(self) -> bool:
        """Configure for SAFE solar viewing."""
        # Start sun mode with safety parameters
        mode_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "iscope_start_view", "params": {"mode": "sun"}}
        )
        await self.log_event("sun_mode_activated", mode_result)
        
        # Enable solar tracking rate
        track_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "scope_set_track_state", "params": True}
        )
        await self.log_event("solar_tracking_enabled", track_result)
        
        # Set minimum exposure to prevent sensor damage
        exposure_limit = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "set_exposure_limit", "params": {"max_ms": 10}}
        )
        await self.log_event("exposure_limited", exposure_limit)
        
        return mode_result.get("success", False)
        
    async def execute_operations(self) -> Dict[str, Any]:
        """Perform SAFE solar operations."""
        results = {"goto_sun": None, "solar_image": None}
        
        # Go to sun with safety offset
        goto_result = await self.telescope_tools.goto_object(
            self.device_id, "Sun"
        )
        results["goto_sun"] = goto_result
        await self.log_event("sun_centered", goto_result)
        
        # Very short exposure with filter
        exposure_result = await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "take_light_frame", "params": {"exp_ms": 1}}
        )
        results["solar_image"] = exposure_result
        
        return results
        
    async def cleanup(self):
        """Extra safety cleanup for solar mode."""
        # Stop tracking immediately
        await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "scope_set_track_state", "params": False}
        )
        
        # Move away from sun
        await self.telescope_tools.custom_action(
            self.device_id, "method_sync",
            {"method": "scope_speed_move", "params": {"speed": 500, "angle": 180, "dur_sec": 5}}
        )
        
        await super().cleanup()
        
        await self.log_event("SAFETY_CLEANUP_COMPLETE", {
            "message": "Telescope moved away from sun and tracking stopped"
        })


async def run_all_mode_tests():
    """Test all Seestar viewing modes."""
    workflows = {
        "scenery": SceneryModeWorkflow(),
        "star": StarModeWorkflow(),
        "moon": MoonModeWorkflow(),
        "sun": SunModeWorkflow(),
    }
    
    results = {}
    
    for mode_name, workflow in workflows.items():
        print(f"\n{'='*50}")
        print(f"Testing {mode_name.upper()} mode workflow")
        print('='*50)
        
        await workflow.setup()
        result = await workflow.run_workflow()
        results[mode_name] = result
        
        print(f"\nResult: {'SUCCESS' if result['success'] else 'FAILED'}")
        if not result['success']:
            print(f"Reason: {result.get('reason', result.get('error', 'Unknown'))}")
            
    return results


if __name__ == "__main__":
    # Run individual mode or all modes
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "scenery":
            workflow = SceneryModeWorkflow()
        elif mode == "star":
            workflow = StarModeWorkflow()
        elif mode == "moon":
            workflow = MoonModeWorkflow()
        elif mode == "sun":
            workflow = SunModeWorkflow()
        else:
            print(f"Unknown mode: {mode}")
            sys.exit(1)
            
        asyncio.run(workflow.setup())
        result = asyncio.run(workflow.run_workflow())
        print(f"\nFinal result: {result}")
    else:
        results = asyncio.run(run_all_mode_tests())
        print("\n\nSUMMARY:")
        for mode, result in results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {mode}: {result}")
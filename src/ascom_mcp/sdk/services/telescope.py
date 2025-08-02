"""
Telescope movement and positioning service.

Provides safe, type-checked telescope control with visual feedback.
"""

import asyncio
from datetime import datetime
from typing import Any

from ..models.commands import GotoParams, MoveParams, PresetParams, TrackingParams
from ..models.responses import (
    CoordinateResponse,
    FrameCapture,
    TelescopeStatus,
    ViewStatusWithPreview,
)


class TelescopeService:
    """Telescope control with visual feedback."""

    def __init__(self, client):
        self.client = client

    async def get_position(self) -> CoordinateResponse:
        """Get current telescope position."""
        response = await self.client.execute_action("scope_get_equ_coord")
        return CoordinateResponse(**response.model_dump())

    async def goto(self, ra: float, dec: float) -> CoordinateResponse:
        """
        Go to RA/Dec coordinates.
        
        Args:
            ra: Right Ascension in hours (0-24)
            dec: Declination in degrees (-90 to +90)
        """
        params = GotoParams(ra_hour=ra, dec_deg=dec)
        response = await self.client.execute_action(
            "scope_goto",
            {"ra_hour": params.ra_hour, "dec_deg": params.dec_deg}
        )
        return CoordinateResponse(**response.model_dump())

    async def goto_with_preview(
        self,
        ra: float,
        dec: float
    ) -> dict[str, Any]:
        """
        Go to coordinates with safety preview.
        
        Returns current view and calculated path before moving.
        """
        # Capture current position and view
        current_pos = await self.get_position()
        current_frame = await self.client.imaging.capture_frame()

        # Calculate movement
        ra_diff = ra - current_pos.ra
        dec_diff = dec - current_pos.dec

        return {
            "current_position": current_pos,
            "target_position": {"ra": ra, "dec": dec},
            "movement": {"ra_delta": ra_diff, "dec_delta": dec_diff},
            "current_view": current_frame,
            "safety_check": {
                "large_movement": abs(ra_diff) > 2 or abs(dec_diff) > 30,
                "near_sun": False,  # Would check ephemeris in real implementation
                "below_horizon": dec < -90 + self.client._latitude  # Approximate
            }
        }

    async def move_direction(
        self,
        direction: str,
        duration: float = 3.0,
        speed: int = 300
    ) -> CoordinateResponse:
        """
        Move telescope in a direction.
        
        Note: Seestar movement is counterintuitive!
        - North/South = horizontal pan
        - East/West = vertical tilt
        
        Args:
            direction: One of "north", "south", "east", "west"
            duration: Movement duration in seconds
            speed: Movement speed (0-1000)
        """
        angle_map = {
            "north": 0,
            "east": 90,
            "south": 180,
            "west": 270
        }
        angle = angle_map.get(direction.lower())
        if angle is None:
            raise ValueError(f"Invalid direction: {direction}")

        params = MoveParams(speed=speed, angle=angle, dur_sec=duration)
        response = await self.client.execute_action(
            "scope_speed_move",
            params.model_dump()
        )

        # Get new position after movement
        if response.success:
            return await self.get_position()
        return CoordinateResponse(**response.model_dump())

    async def set_tracking(self, enabled: bool) -> bool:
        """
        Enable/disable tracking (with Error 207 prevention).
        
        Args:
            enabled: True to enable, False to disable
        """
        # Use validated params to ensure correct format
        params = TrackingParams(enabled=enabled)

        # CRITICAL: Pass boolean directly, not object!
        response = await self.client.execute_action(
            "scope_set_track_state",
            params.to_seestar_params()  # Returns direct boolean
        )
        return response.success

    async def get_tracking(self) -> bool:
        """Get current tracking state."""
        response = await self.client.execute_action("scope_get_track_state")
        return response.model_dump().get("tracking", False)

    async def goto_preset(self, preset_name: str) -> CoordinateResponse:
        """
        Go to a named preset position.
        
        Args:
            preset_name: Preset ID (e.g., "manhattan_skyline", "zenith")
        """
        params = PresetParams(preset_id=preset_name)
        response = await self.client.execute_action(
            "goto_preset",
            params.model_dump()
        )

        if response.success:
            return await self.get_position()
        return CoordinateResponse(**response.model_dump())

    async def where_am_i(self) -> ViewStatusWithPreview:
        """
        Get current position with visual preview.
        
        Returns complete status including coordinates and current view.
        """
        # Get all status info in parallel
        position_task = self.get_position()
        tracking_task = self.get_tracking()
        view_task = self.client.viewing.get_status()
        frame_task = self.client.imaging.capture_frame()

        position, tracking, view_status, frame = await asyncio.gather(
            position_task,
            tracking_task,
            view_task,
            frame_task
        )

        # Combine into comprehensive status
        preview = ViewStatusWithPreview(
            **view_status.model_dump(),
            preview_frame=FrameCapture(
                timestamp=datetime.now(),
                image_data=frame
            ),
            mjpeg_url=self.client.streaming.get_mjpeg_url()
        )

        # Add position info
        preview.ra = position.ra
        preview.dec = position.dec
        preview.altitude = position.alt
        preview.azimuth = position.az
        preview.tracking = tracking

        return preview

    async def quick_look(
        self,
        direction: str,
        duration: float = 2.0,
        return_to_start: bool = True
    ) -> FrameCapture:
        """
        Briefly look in a direction and capture view.
        
        Args:
            direction: Direction to look
            duration: How long to look
            return_to_start: Whether to return to original position
            
        Returns:
            Captured frame from the direction
        """
        # Save current position if returning
        start_pos = None
        if return_to_start:
            start_pos = await self.get_position()

        # Move and capture
        await self.move_direction(direction, duration)
        frame = await self.client.imaging.capture_frame()

        # Return to start if requested
        if return_to_start and start_pos:
            await self.goto(start_pos.ra, start_pos.dec)

        return FrameCapture(
            timestamp=datetime.now(),
            image_data=frame
        )

    async def get_status(self) -> TelescopeStatus:
        """Get complete telescope status."""
        # Get multiple status values
        position = await self.get_position()
        tracking = await self.get_tracking()

        return TelescopeStatus(
            connected=self.client._connected,
            tracking=tracking,
            slewing=False,  # Would check actual slew status
            parked=False,   # Seestar doesn't have park
            ra=position.ra,
            dec=position.dec,
            altitude=position.alt or 0,
            azimuth=position.az or 0
        )

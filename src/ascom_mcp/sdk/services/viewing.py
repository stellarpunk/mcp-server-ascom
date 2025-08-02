"""
Viewing mode control service.

Manages different observation modes including scenery for terrestrial viewing.
"""


from ..models.commands import ViewParams
from ..models.responses import ViewStatus


class ViewingService:
    """Control viewing modes."""

    def __init__(self, client):
        self.client = client

    async def start(
        self,
        mode: str = "star",
        target_name: str | None = None
    ) -> ViewStatus:
        """
        Start viewing mode.
        
        Args:
            mode: One of "star", "moon", "sun", "scenery", "planet"
            target_name: Optional target for goto+view
            
        Returns:
            View status
        """
        params = ViewParams(mode=mode, target_name=target_name)

        # Safety check for solar mode
        if mode == "sun":
            # In production, would verify solar filter is attached
            pass

        response = await self.client.execute_action(
            "iscope_start_view",
            params.model_dump(exclude_none=True)
        )

        if response.success:
            return await self.get_status()

        # Return error state
        return ViewStatus(
            active=False,
            mode=mode,
            target_name=target_name
        )

    async def stop(self) -> bool:
        """Stop current viewing mode."""
        response = await self.client.execute_action("iscope_stop_view")
        return response.success

    async def get_status(self) -> ViewStatus:
        """Get current viewing status."""
        response = await self.client.execute_action("get_view_state")

        if response.success:
            data = response.model_dump()
            return ViewStatus(
                active=data.get("viewing", False),
                mode=data.get("mode"),
                target_name=data.get("target_name"),
                exposure_time_ms=data.get("exposure_ms"),
                gain=data.get("gain"),
                stacking=data.get("stacking", False),
                stack_count=data.get("stack_count", 0)
            )

        return ViewStatus(active=False)

    async def start_scenery_mode(self) -> ViewStatus:
        """
        Start scenery mode for terrestrial viewing.
        
        Optimized settings for landscape/cityscape observation.
        """
        return await self.start(mode="scenery")

    async def start_solar_mode(self, verify_filter: bool = True) -> ViewStatus:
        """
        Start solar observation mode.
        
        Args:
            verify_filter: Whether to verify solar filter is attached
            
        Returns:
            View status
            
        Raises:
            RuntimeError: If solar filter not detected (when verify_filter=True)
        """
        if verify_filter:
            # In production, would check filter wheel position
            # or use camera to detect filter
            pass

        return await self.start(mode="sun")

    async def is_safe_for_mode(self, mode: str) -> bool:
        """
        Check if it's safe to use a viewing mode.
        
        Args:
            mode: Viewing mode to check
            
        Returns:
            True if safe to proceed
        """
        if mode == "sun":
            # Check for solar filter
            filter_pos = await self.client.focus.get_filter_position()
            # Assuming position 2 is solar filter (would verify with real hardware)
            return filter_pos == 2

        return True

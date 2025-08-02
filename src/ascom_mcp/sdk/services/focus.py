"""
Focus control service.

Manages focus position and autofocus operations.
"""

from ..models.commands import FilterParams, FocusParams
from ..models.responses import FilterStatus, FocusPosition


class FocusService:
    """Focus and filter control."""

    def __init__(self, client):
        self.client = client

    async def get_position(self) -> FocusPosition:
        """Get current focus position."""
        response = await self.client.execute_action("get_focuser_position")

        if response.success:
            data = response.model_dump()
            return FocusPosition(
                position=data.get("position", 0),
                moving=data.get("moving", False),
                temperature=data.get("temperature")
            )

        return FocusPosition(position=0)

    async def set_position(self, position: int) -> FocusPosition:
        """
        Set focus position.
        
        Args:
            position: Focus position (0-3000)
                Stars: 1800-2000
                Moon: 1700-1900  
                Terrestrial: 500-1500
                Manhattan (~2mi): 1200-1350
        """
        params = FocusParams(step=position)
        response = await self.client.execute_action(
            "move_focuser",
            {"step": params.step}
        )

        if response.success:
            return await self.get_position()

        return FocusPosition(position=position)

    async def auto_focus(self) -> bool:
        """
        Start automatic focus.
        
        Note: API has typo - 'focuse' not 'focus'
        """
        response = await self.client.execute_action("start_auto_focuse")
        return response.success

    async def stop_auto_focus(self) -> bool:
        """Stop automatic focus."""
        response = await self.client.execute_action("stop_auto_focuse")
        return response.success

    async def focus_for_distance(self, distance_type: str) -> FocusPosition:
        """
        Set focus for typical distance.
        
        Args:
            distance_type: One of "stars", "moon", "terrestrial", "close"
            
        Returns:
            New focus position
        """
        position_map = {
            "stars": 1900,      # Middle of star range
            "moon": 1800,       # Moon is closer than stars
            "terrestrial": 1250,  # ~2 miles
            "close": 800        # Nearby objects
        }

        position = position_map.get(distance_type.lower())
        if position is None:
            raise ValueError(f"Unknown distance type: {distance_type}")

        return await self.set_position(position)

    async def get_filter_position(self) -> int:
        """Get current filter wheel position."""
        response = await self.client.execute_action("get_wheel_position")

        if response.success:
            return response.model_dump().get("position", 0)
        return 0

    async def set_filter(self, position: int) -> FilterStatus:
        """
        Set filter wheel position.
        
        Args:
            position: Filter position
                0 = Clear/Luminance
                1 = UV/IR Cut
                2 = Light Pollution
        """
        params = FilterParams(pos=position)
        response = await self.client.execute_action(
            "set_wheel_position",
            {"pos": params.pos}
        )

        if response.success:
            return FilterStatus.from_position(position)

        return FilterStatus.from_position(0)

    async def set_filter_by_name(self, name: str) -> FilterStatus:
        """
        Set filter by name.
        
        Args:
            name: Filter name (clear, uv, lp, etc.)
        """
        name_map = {
            "clear": 0,
            "luminance": 0,
            "uv": 1,
            "uvir": 1,
            "cut": 1,
            "lp": 2,
            "lpf": 2,
            "light pollution": 2
        }

        position = name_map.get(name.lower())
        if position is None:
            raise ValueError(f"Unknown filter: {name}")

        return await self.set_filter(position)

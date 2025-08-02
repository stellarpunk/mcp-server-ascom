"""
Device status service.

Provides comprehensive device state information.
"""

from typing import Any

from ..models.responses import DeviceState


class StatusService:
    """Device status queries."""

    def __init__(self, client):
        self.client = client

    async def get_device_state(self) -> DeviceState:
        """Get overall device state."""
        response = await self.client.execute_action("get_device_state")

        if response.success:
            data = response.model_dump()

            # Extract relevant fields
            pi_status = data.get("pi_status", {})

            return DeviceState(
                connected=self.client._connected,
                initialized=self.client._initialized,
                battery_level=pi_status.get("battery_capacity"),
                temperature_celsius=pi_status.get("temp"),
                free_space_gb=pi_status.get("free_space_gb"),
                firmware_version=data.get("firmware_version"),
                startup_complete=self.client._initialized
            )

        # Return minimal state on error
        return DeviceState(
            connected=self.client._connected,
            initialized=self.client._initialized
        )

    async def test_connection(self) -> bool:
        """Test connection to telescope."""
        response = await self.client.execute_action("test_connection")
        return response.success

    async def get_time(self) -> str | None:
        """Get device time."""
        response = await self.client.execute_action("pi_get_time")

        if response.success:
            return response.model_dump().get("time")
        return None

    async def get_detailed_status(self) -> dict[str, Any]:
        """
        Get comprehensive status information.
        
        Combines multiple status queries for complete picture.
        """
        # Get all status info
        device_state = await self.get_device_state()
        telescope_status = await self.client.telescope.get_status()
        view_status = await self.client.viewing.get_status()
        focus_position = await self.client.focus.get_position()

        return {
            "device": device_state.model_dump(),
            "telescope": telescope_status.model_dump(),
            "viewing": view_status.model_dump(),
            "focus": focus_position.model_dump(),
            "streaming": {
                "mjpeg_url": self.client.streaming.get_mjpeg_url(),
                "active": self.client.streaming._streaming
            }
        }

    async def check_ready_for_operation(self) -> dict[str, bool]:
        """
        Check if telescope is ready for various operations.
        
        Returns:
            Dictionary of operation readiness states
        """
        device_state = await self.get_device_state()

        return {
            "basic_operations": self.client.is_ready,
            "solar_viewing": False,  # Would check filter
            "long_exposure": device_state.battery_level > 30 if device_state.battery_level else False,
            "temperature_ok": not device_state.temperature_warning,
            "storage_available": device_state.free_space_gb > 1 if device_state.free_space_gb else True,
            "initialized": device_state.startup_complete
        }

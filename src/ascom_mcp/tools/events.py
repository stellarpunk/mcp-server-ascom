"""
Event management tools for ASCOM MCP server.

Provides tools for subscribing to and managing device events.
"""

import json
from typing import Any, Optional

from ascom_mcp.ascom_logging import StructuredLogger
from ascom_mcp.devices.manager import DeviceManager
from ascom_mcp.resources.event_stream import EventStreamManager

logger = StructuredLogger("ascom.tools.events")


class EventTools:
    """Event management tools for ASCOM devices."""

    def __init__(self, device_manager: DeviceManager, event_manager: EventStreamManager):
        """Initialize event tools.

        Args:
            device_manager: Device manager instance
            event_manager: Event stream manager instance
        """
        self.device_manager = device_manager
        self.event_manager = event_manager
        self._event_handlers = {}

    async def get_event_history(
        self,
        device_id: str,
        count: Optional[int] = 50,
        event_types: Optional[list[str]] = None,
        since_timestamp: Optional[float] = None,
    ) -> dict[str, Any]:
        """Get historical events for a device.

        Args:
            device_id: Device identifier
            count: Maximum number of events to return
            event_types: Filter by specific event types
            since_timestamp: Get events after this Unix timestamp

        Returns:
            Event history and metadata
        """
        try:
            # Verify device exists
            device_info = await self.device_manager.get_device_info(device_id)
            if not device_info:
                return {
                    "success": False,
                    "error": f"Device '{device_id}' not found",
                }

            # Get events
            events = await self.event_manager.get_events(
                device_id=device_id,
                since=since_timestamp,
                event_types=event_types,
                limit=count,
            )

            return {
                "success": True,
                "device_id": device_id,
                "device_name": device_info.name,
                "event_count": len(events["events"]),
                "events": events["events"],
                "available_types": events.get("available_types", []),
            }

        except Exception as e:
            logger.error(f"Failed to get event history: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def clear_event_history(self, device_id: str) -> dict[str, Any]:
        """Clear event history for a device.

        Args:
            device_id: Device identifier

        Returns:
            Operation result
        """
        try:
            # Verify device exists
            device_info = await self.device_manager.get_device_info(device_id)
            if not device_info:
                return {
                    "success": False,
                    "error": f"Device '{device_id}' not found",
                }

            # Clear events
            await self.event_manager.clear_device_events(device_id)

            return {
                "success": True,
                "message": f"Cleared event history for {device_info.name}",
            }

        except Exception as e:
            logger.error(f"Failed to clear event history: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_event_types(self) -> dict[str, Any]:
        """Get available event types and descriptions.

        Returns:
            Dictionary of event types and their descriptions
        """
        try:
            event_types = self.event_manager.get_event_types()
            
            return {
                "success": True,
                "event_types": event_types,
                "message": "Event types describe the various notifications from ASCOM devices",
            }

        except Exception as e:
            logger.error(f"Failed to get event types: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def setup_device_events(self, device_id: str) -> None:
        """Set up event handling for a device (internal use).

        This is called when a device is connected to start
        capturing its events.

        Args:
            device_id: Device identifier
        """
        try:
            # Get device info
            device_info = await self.device_manager.get_device_info(device_id)
            if not device_info:
                return

            # Store device metadata in event manager
            await self.event_manager.set_device_metadata(
                device_id,
                {
                    "name": device_info.name,
                    "type": device_info.device_type,
                    "unique_id": device_info.unique_id,
                },
            )

            # For Seestar devices, we'll hook into the eventbus
            # This will be done in the telescope connection code
            logger.info(f"Event handling prepared for {device_info.name}")

        except Exception as e:
            logger.error(f"Failed to setup device events: {e}")

    async def handle_device_event(self, device_id: str, event_data: dict) -> None:
        """Handle an event from a device (internal use).

        This is called by device-specific code when events occur.

        Args:
            device_id: Device identifier
            event_data: Raw event data from device
        """
        try:
            await self.event_manager.add_event(device_id, event_data)
        except Exception as e:
            logger.error(f"Failed to handle device event: {e}", device_id=device_id)
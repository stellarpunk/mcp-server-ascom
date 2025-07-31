"""
Discovery tools for ASCOM devices.

Provides device discovery and information gathering capabilities.
"""

import logging
from typing import Any

from ..devices.manager import DeviceManager

logger = logging.getLogger(__name__)


class DiscoveryTools:
    """Tools for discovering ASCOM devices."""

    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager

    async def discover_devices(self, timeout: float = 5.0) -> dict[str, Any]:
        """
        Discover ASCOM devices on the network.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            Dictionary containing discovered devices
        """
        try:
            logger.info(f"Starting device discovery with timeout {timeout}s")

            # Perform discovery
            devices = await self.device_manager.discover_devices(timeout)

            # Format response
            device_list = []
            for device in devices:
                device_dict = device.to_dict()
                # Add quick connect hint
                device_dict["connect_hint"] = (
                    f"Use '{device.type.lower()}_connect' with device_id='{device.id}'"
                )
                device_list.append(device_dict)

            return {
                "success": True,
                "count": len(devices),
                "devices": device_list,
                "message": f"Found {len(devices)} ASCOM device(s)"
                if devices
                else "No ASCOM devices found on network",
            }

        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Discovery failed. Check network connection and ensure ASCOM devices are powered on.",
            }

    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        """
        Get detailed information about a device.

        Args:
            device_id: Device ID from discovery

        Returns:
            Detailed device information
        """
        try:
            logger.info(f"Getting info for device {device_id}")

            # Get device info from manager
            info = await self.device_manager.get_device_info(device_id)

            # Add capabilities based on device type
            if info["type"].lower() == "telescope":
                info["capabilities"] = [
                    "goto",
                    "goto_object",
                    "park",
                    "tracking",
                    "position_reporting",
                    "slew_rates",
                ]
            elif info["type"].lower() == "camera":
                info["capabilities"] = [
                    "capture",
                    "binning",
                    "cooling",
                    "gain_control",
                    "offset_control",
                    "subframe",
                ]
            elif info["type"].lower() == "focuser":
                info["capabilities"] = [
                    "move_absolute",
                    "move_relative",
                    "temperature_compensation",
                    "position_reporting",
                ]
            elif info["type"].lower() == "filterwheel":
                info["capabilities"] = [
                    "filter_selection",
                    "filter_names",
                    "position_reporting",
                ]

            return {"success": True, "device": info}

        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Could not get info for device {device_id}",
            }

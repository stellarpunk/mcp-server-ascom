"""Base class for ASCOM device tools."""

from abc import ABC, abstractmethod
from typing import Any

from ..devices.manager import DeviceManager


class BaseDeviceTools(ABC):
    """Base class for all device tool implementations.

    Provides common functionality and interface for device tools.
    """

    def __init__(self, device_manager: DeviceManager):
        """Initialize with device manager.

        Args:
            device_manager: Device manager instance
        """
        self.device_manager = device_manager

    @abstractmethod
    async def connect(self, device_id: str) -> dict[str, Any]:
        """Connect to device.

        Args:
            device_id: Device ID from discovery

        Returns:
            Standard response dict with success status
        """
        pass

    @abstractmethod
    async def disconnect(self, device_id: str) -> dict[str, Any]:
        """Disconnect from device.

        Args:
            device_id: Connected device ID

        Returns:
            Standard response dict with success status
        """
        pass

    def _success_response(self, message: str, **data) -> dict[str, Any]:
        """Create standard success response.

        Args:
            message: Success message
            **data: Additional data to include

        Returns:
            Standard success response dict
        """
        response = {"success": True, "message": message}
        response.update(data)
        return response

    def _error_response(self, error: str, **data) -> dict[str, Any]:
        """Create standard error response.

        Args:
            error: Error message
            **data: Additional data to include

        Returns:
            Standard error response dict
        """
        response = {"success": False, "error": error}
        response.update(data)
        return response

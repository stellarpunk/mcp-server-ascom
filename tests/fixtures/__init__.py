"""Test fixtures for ASCOM MCP Server."""

from .common import (
    camera_capabilities,
    filterwheel_capabilities,
    focuser_capabilities,
    standard_device_properties,
    telescope_capabilities,
)
from .device_factory import create_device_info, create_mock_device

__all__ = [
    "create_mock_device",
    "create_device_info",
    "standard_device_properties",
    "telescope_capabilities",
    "camera_capabilities",
    "focuser_capabilities",
    "filterwheel_capabilities",
]

"""Test fixtures for ASCOM MCP Server."""

from .device_factory import create_mock_device, create_device_info
from .common import (
    standard_device_properties,
    telescope_capabilities,
    camera_capabilities,
    focuser_capabilities,
    filterwheel_capabilities
)

__all__ = [
    'create_mock_device',
    'create_device_info',
    'standard_device_properties',
    'telescope_capabilities',
    'camera_capabilities', 
    'focuser_capabilities',
    'filterwheel_capabilities'
]
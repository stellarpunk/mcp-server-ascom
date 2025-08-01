"""Unit tests for device resolver."""

import os
from unittest.mock import patch

import pytest

from ascom_mcp.devices.device_resolver import DeviceResolver
from ascom_mcp.devices.manager import DeviceInfo


class TestDeviceResolver:
    """Test DeviceResolver class."""
    
    def test_parse_connection_string_full(self):
        """Test parsing full connection string with name."""
        result = DeviceResolver.parse_connection_string("seestar@192.168.1.100:5555")
        assert result == ("seestar", "192.168.1.100", 5555)
        
    def test_parse_connection_string_no_name(self):
        """Test parsing connection string without name."""
        result = DeviceResolver.parse_connection_string("192.168.1.100:5555")
        assert result == ("Direct Connection", "192.168.1.100", 5555)
        
    def test_parse_connection_string_invalid(self):
        """Test parsing invalid connection strings."""
        assert DeviceResolver.parse_connection_string("telescope_1") is None
        assert DeviceResolver.parse_connection_string("192.168.1.100") is None
        assert DeviceResolver.parse_connection_string("seestar@192.168.1.100") is None
        
    def test_create_device_info_from_connection(self):
        """Test creating DeviceInfo from connection parameters."""
        device_info = DeviceResolver.create_device_info_from_connection(
            device_id="telescope_1",
            name="Test Telescope",
            host="localhost",
            port=5555,
            device_type="Telescope",
            device_number=1
        )
        
        assert device_info.id == "telescope_1"
        assert device_info.name == "Test Telescope"
        assert device_info.host == "localhost"
        assert device_info.port == 5555
        assert device_info.type == "Telescope"
        assert device_info.number == 1
        
    def test_parse_device_id_type_standard(self):
        """Test parsing standard device ID format."""
        device_type, device_number = DeviceResolver.parse_device_id_type("telescope_1")
        assert device_type == "Telescope"
        assert device_number == 1
        
        device_type, device_number = DeviceResolver.parse_device_id_type("camera_0")
        assert device_type == "Camera"
        assert device_number == 0
        
    def test_parse_device_id_type_no_underscore(self):
        """Test parsing device ID without underscore."""
        device_type, device_number = DeviceResolver.parse_device_id_type("seestar")
        assert device_type == "Telescope"  # Default
        assert device_number == 1  # Default
        
    def test_parse_device_id_type_invalid_number(self):
        """Test parsing device ID with invalid number."""
        device_type, device_number = DeviceResolver.parse_device_id_type("telescope_abc")
        assert device_type == "Telescope"
        assert device_number == 1  # Default when parse fails
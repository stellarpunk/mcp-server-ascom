"""Factory functions for creating mock ASCOM devices."""

from typing import Dict, Any, Optional
from unittest.mock import MagicMock
from datetime import datetime

from ascom_mcp.devices.manager import DeviceInfo


def create_mock_device(
    device_type: str,
    device_number: int = 0,
    **capabilities: Any
) -> MagicMock:
    """Create a mock ASCOM device with standard properties.
    
    Args:
        device_type: Type of device (Telescope, Camera, etc.)
        device_number: Device number (default 0)
        **capabilities: Device-specific capabilities
        
    Returns:
        Mock device with ASCOM standard properties
        
    Example:
        telescope = create_mock_device(
            "Telescope",
            CanSlew=True,
            CanPark=True,
            RightAscension=12.5
        )
    """
    mock = MagicMock()
    
    # Standard ASCOM properties every device must have
    mock.Connected = False
    mock.Description = f"Mock {device_type}"
    mock.DriverInfo = f"Mock {device_type} Driver v1.0"
    mock.DriverVersion = "1.0.0"
    mock.InterfaceVersion = 3
    mock.Name = f"Mock {device_type} {device_number}"
    mock.SupportedActions = []
    
    # Device state
    mock._connected = False
    
    # Make Connected property work properly
    def get_connected():
        return mock._connected
        
    def set_connected(value):
        mock._connected = bool(value)
        
    type(mock).Connected = property(get_connected, set_connected)
    
    # Add device-specific capabilities
    for key, value in capabilities.items():
        setattr(mock, key, value)
        
    return mock


def create_device_info(
    device_type: str,
    device_number: int = 0,
    host: str = "localhost",
    port: int = 11111,
    **extra_fields: Any
) -> DeviceInfo:
    """Create a DeviceInfo object for testing.
    
    Args:
        device_type: Type of device
        device_number: Device number
        host: Device host
        port: Device port
        **extra_fields: Additional fields
        
    Returns:
        DeviceInfo instance
    """
    data = {
        "DeviceType": device_type,
        "DeviceNumber": device_number,
        "DeviceName": f"Mock {device_type} {device_number}",
        "Host": host,
        "Port": port,
        "UniqueID": f"mock-{device_type.lower()}-{device_number:03d}",
        "ApiVersion": 1
    }
    data.update(extra_fields)
    
    return DeviceInfo(data)


def create_telescope_mock(**overrides) -> MagicMock:
    """Create a mock telescope with standard capabilities."""
    defaults = {
        # Movement
        "CanSlew": True,
        "CanSlewAsync": True,
        "CanSlewAltAz": True,
        "CanSlewAltAzAsync": True,
        "Slewing": False,
        
        # Parking
        "CanPark": True,
        "CanSetPark": True,
        "AtPark": False,
        
        # Tracking
        "CanSetTracking": True,
        "Tracking": True,
        "TrackingRate": 0,  # Sidereal
        "TrackingRates": [0, 1, 2, 3],  # Sidereal, Lunar, Solar, King
        
        # Position
        "RightAscension": 0.0,
        "Declination": 0.0,
        "Altitude": 45.0,
        "Azimuth": 180.0,
        "SiderealTime": 0.0,
        
        # Site info
        "SiteLatitude": 40.0,
        "SiteLongitude": -74.0,
        "SiteElevation": 10.0,
        
        # Limits
        "CanSetDeclinationRate": False,
        "CanSetRightAscensionRate": False,
        "CanFindHome": True,
        "AtHome": False
    }
    defaults.update(overrides)
    return create_mock_device("Telescope", **defaults)


def create_camera_mock(**overrides) -> MagicMock:
    """Create a mock camera with standard capabilities."""
    defaults = {
        # State
        "CameraState": 0,  # Idle
        "ImageReady": False,
        "IsPulseGuiding": False,
        
        # Sensor info
        "SensorType": 1,  # Color
        "SensorName": "Mock CMOS Sensor",
        "PixelSizeX": 4.63,
        "PixelSizeY": 4.63,
        "CameraXSize": 4144,
        "CameraYSize": 2822,
        
        # Binning
        "BinX": 1,
        "BinY": 1,
        "MaxBinX": 4,
        "MaxBinY": 4,
        "CanAsymmetricBin": True,
        
        # Subframe
        "StartX": 0,
        "StartY": 0,
        "NumX": 4144,
        "NumY": 2822,
        
        # Cooling
        "CanSetCCDTemperature": True,
        "CanGetCoolerPower": True,
        "CCDTemperature": 20.0,
        "SetCCDTemperature": -10.0,
        "CoolerOn": False,
        "CoolerPower": 0.0,
        "HeatSinkTemperature": 25.0,
        
        # Exposure
        "CanAbortExposure": True,
        "CanStopExposure": True,
        "ExposureMin": 0.001,
        "ExposureMax": 3600.0,
        "ExposureResolution": 0.001,
        "LastExposureDuration": 0.0,
        "LastExposureStartTime": "",
        
        # Other
        "CanPulseGuide": True,
        "Gain": 100,
        "GainMin": 0,
        "GainMax": 600,
        "Offset": 30,
        "OffsetMin": 0,
        "OffsetMax": 100,
        
        # Methods
        "StartExposure": MagicMock(),
        "StopExposure": MagicMock(),
        "AbortExposure": MagicMock()
    }
    defaults.update(overrides)
    return create_mock_device("Camera", **defaults)


def create_focuser_mock(**overrides) -> MagicMock:
    """Create a mock focuser with standard capabilities."""
    defaults = {
        # Position
        "Position": 25000,
        "MaxStep": 50000,
        "MaxIncrement": 50000,
        "Absolute": True,
        "IsMoving": False,
        
        # Temperature
        "Temperature": 20.0,
        "TempComp": False,
        "TempCompAvailable": True,
        
        # Capabilities
        "CanHalt": True,
        "CanStepSize": False,
        "StepSize": 1.0,
        
        # Methods
        "Move": MagicMock(),
        "Halt": MagicMock()
    }
    defaults.update(overrides)
    return create_mock_device("Focuser", **defaults)


def create_filterwheel_mock(**overrides) -> MagicMock:
    """Create a mock filter wheel with standard capabilities."""
    defaults = {
        # Position
        "Position": 0,
        "Names": ["Red", "Green", "Blue", "Luminance", "Ha", "OIII", "SII"],
        "FocusOffsets": [0, 0, 0, 0, -50, -50, -50],
        
        # Methods
        "SetPosition": MagicMock()
    }
    defaults.update(overrides)
    return create_mock_device("FilterWheel", **defaults)
"""Common fixture data for ASCOM devices."""

from typing import Any

# Standard properties every ASCOM device must have
standard_device_properties = {
    "Connected": False,
    "Description": str,
    "DriverInfo": str,
    "DriverVersion": str,
    "InterfaceVersion": int,
    "Name": str,
    "SupportedActions": list,
}


# Device-specific capability definitions
telescope_capabilities = {
    "required": ["RightAscension", "Declination", "CanSlew", "Slewing", "Tracking"],
    "optional": [
        "CanPark",
        "AtPark",
        "CanFindHome",
        "AtHome",
        "CanSetTracking",
        "CanSlewAltAz",
        "Altitude",
        "Azimuth",
        "SiteLatitude",
        "SiteLongitude",
        "SiteElevation",
        "SiderealTime",
    ],
}


camera_capabilities = {
    "required": [
        "CameraState",
        "ImageReady",
        "SensorType",
        "PixelSizeX",
        "PixelSizeY",
        "CameraXSize",
        "CameraYSize",
        "StartExposure",
    ],
    "optional": [
        "CanAbortExposure",
        "CanSetCCDTemperature",
        "CCDTemperature",
        "CoolerOn",
        "BinX",
        "BinY",
        "MaxBinX",
        "MaxBinY",
        "Gain",
        "Offset",
        "CanPulseGuide",
    ],
}


focuser_capabilities = {
    "required": ["Position", "MaxStep", "IsMoving", "Move"],
    "optional": [
        "Absolute",
        "MaxIncrement",
        "Temperature",
        "TempComp",
        "TempCompAvailable",
        "CanHalt",
        "StepSize",
    ],
}


filterwheel_capabilities = {
    "required": ["Position", "Names"],
    "optional": ["FocusOffsets"],
}


dome_capabilities = {
    "required": ["CanSetAzimuth", "CanSetShutter", "ShutterStatus", "Slewing"],
    "optional": [
        "CanPark",
        "CanFindHome",
        "CanSyncAzimuth",
        "Azimuth",
        "AtHome",
        "AtPark",
    ],
}


rotator_capabilities = {
    "required": ["Position", "IsMoving", "CanReverse"],
    "optional": ["CanMoveMechanical", "MechanicalPosition", "Reverse", "StepSize"],
}


# Test data generators
def generate_discovery_response(device_types: list[str]) -> list[dict[str, Any]]:
    """Generate a mock discovery response with multiple device types."""
    devices = []
    for i, device_type in enumerate(device_types):
        devices.append(
            {
                "DeviceType": device_type,
                "DeviceNumber": 0,
                "DeviceName": f"Test {device_type}",
                "UniqueID": f"test-{device_type.lower()}-001",
                "Host": "localhost",
                "Port": 11111 + i,
                "ApiVersion": 1,
            }
        )
    return devices


def generate_error_response(
    error_message: str, error_code: int = 0x400
) -> dict[str, Any]:
    """Generate standard ASCOM error response."""
    return {"Value": None, "ErrorNumber": error_code, "ErrorMessage": error_message}

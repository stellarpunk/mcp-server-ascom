"""
Custom exceptions for ASCOM MCP server.
"""


class AscomMCPError(Exception):
    """Base exception for ASCOM MCP errors."""

    pass


class DeviceNotFoundError(AscomMCPError):
    """Device not found in available or connected devices."""

    pass


class ConnectionError(AscomMCPError):
    """Error connecting to or communicating with device."""

    pass


class InvalidParameterError(AscomMCPError):
    """Invalid parameter provided to tool."""

    pass


class DeviceNotConnectedError(AscomMCPError):
    """Attempted operation on device that is not connected."""

    pass


class OperationNotSupportedError(AscomMCPError):
    """Device does not support requested operation."""

    pass


class DeviceBusyError(AscomMCPError):
    """Device is busy with another operation."""

    pass


class SafetyError(AscomMCPError):
    """Operation blocked for safety reasons."""

    pass

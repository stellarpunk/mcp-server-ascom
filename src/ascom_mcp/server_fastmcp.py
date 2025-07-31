#!/usr/bin/env python3
"""
ASCOM MCP Server implemented with FastMCP from the official SDK.

This is a cleaner, more maintainable implementation compared to the low-level API.
FastMCP is now the recommended approach for MCP servers in Python.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP, Context

from . import __version__
from .devices.manager import DeviceManager
from .tools.camera import CameraTools
from .tools.discovery import DiscoveryTools
from .tools.telescope import TelescopeTools
from .logging import StructuredLogger

# Structured logger (logs to stderr per MCP spec)
logger = StructuredLogger("ascom.server")

# Create the FastMCP server
mcp = FastMCP("ASCOM MCP Server")

# Global device manager (initialized at startup)
device_manager: DeviceManager | None = None
discovery_tools: DiscoveryTools | None = None
telescope_tools: TelescopeTools | None = None
camera_tools: CameraTools | None = None


# Server lifecycle management
@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Manage server startup and shutdown."""
    global device_manager, discovery_tools, telescope_tools, camera_tools
    
    logger.info(f"Starting ASCOM MCP Server v{__version__} (FastMCP)")
    
    # Initialize device manager and tools
    device_manager = DeviceManager()
    await device_manager.initialize()
    
    discovery_tools = DiscoveryTools(device_manager)
    telescope_tools = TelescopeTools(device_manager)
    camera_tools = CameraTools(device_manager)
    
    logger.info("ASCOM MCP Server initialized successfully")
    
    try:
        yield
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down ASCOM MCP Server")
        if device_manager:
            await device_manager.shutdown()
        logger.info("Server shutdown complete")


async def ensure_initialized():
    """Ensure all global tools are initialized."""
    global device_manager, discovery_tools, telescope_tools, camera_tools
    
    if device_manager is None:
        device_manager = DeviceManager()
        await device_manager.initialize()
    
    if discovery_tools is None:
        discovery_tools = DiscoveryTools(device_manager)
    
    if telescope_tools is None:
        telescope_tools = TelescopeTools(device_manager)
        
    if camera_tools is None:
        camera_tools = CameraTools(device_manager)


# Discovery tools
@mcp.tool()
async def discover_ascom_devices(timeout: float = 5.0) -> dict[str, Any]:
    """Discover ASCOM devices on the network.
    
    Args:
        timeout: Discovery timeout in seconds (default: 5.0)
        
    Returns:
        Dictionary with discovered devices
    """
    await ensure_initialized()
    
    logger.debug("tool_called", tool="discover_ascom_devices", timeout=timeout)
    result = await discovery_tools.discover_devices(timeout=timeout)
    logger.info("devices_discovered", count=result.get("count", 0))
    return result


@mcp.tool()
async def get_device_info(device_id: str) -> dict[str, Any]:
    """Get detailed information about a specific ASCOM device.
    
    Args:
        device_id: Device ID from discovery
        
    Returns:
        Device information dictionary
    """
    await ensure_initialized()
    return await discovery_tools.get_device_info(device_id=device_id)


# Telescope tools
@mcp.tool()
async def telescope_connect(device_id: str) -> dict[str, Any]:
    """Connect to an ASCOM telescope.
    
    Args:
        device_id: Device ID from discovery
        
    Returns:
        Connection status dictionary
    """
    await ensure_initialized()
    return await telescope_tools.connect(device_id=device_id)


@mcp.tool()
async def telescope_disconnect(device_id: str) -> dict[str, Any]:
    """Disconnect from an ASCOM telescope.
    
    Args:
        device_id: Connected telescope device ID
        
    Returns:
        Disconnection status dictionary
    """
    await ensure_initialized()
    return await telescope_tools.disconnect(device_id=device_id)


@mcp.tool()
async def telescope_goto(device_id: str, ra: float, dec: float) -> dict[str, Any]:
    """Slew telescope to specific coordinates.
    
    Args:
        device_id: Connected telescope device ID
        ra: Right Ascension in hours (0-24)
        dec: Declination in degrees (-90 to +90)
        
    Returns:
        Slew status dictionary
    """
    await ensure_initialized()
    return await telescope_tools.goto(
        device_id=device_id,
        ra=ra,
        dec=dec
    )


@mcp.tool()
async def telescope_goto_object(device_id: str, object_name: str) -> dict[str, Any]:
    """Slew telescope to a named celestial object.
    
    Args:
        device_id: Connected telescope device ID
        object_name: Name of celestial object (e.g., 'M31', 'Orion Nebula')
        
    Returns:
        Slew status dictionary
    """
    await ensure_initialized()
    return await telescope_tools.goto_object(
        device_id=device_id,
        object_name=object_name
    )


@mcp.tool()
async def telescope_get_position(device_id: str) -> dict[str, Any]:
    """Get current telescope position.
    
    Args:
        device_id: Connected telescope device ID
        
    Returns:
        Position information dictionary
    """
    await ensure_initialized()
    return await telescope_tools.get_position(device_id=device_id)


@mcp.tool()
async def telescope_park(device_id: str) -> dict[str, Any]:
    """Park telescope at home position.
    
    Args:
        device_id: Connected telescope device ID
        
    Returns:
        Park status dictionary
    """
    await ensure_initialized()
    return await telescope_tools.park(device_id=device_id)


@mcp.tool()
async def telescope_custom_action(
    device_id: str, 
    action: str, 
    parameters: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute custom ASCOM action (e.g., Seestar-specific commands).
    
    Args:
        device_id: Connected telescope device ID
        action: Action name (e.g., 'method_sync', 'goto_preset')
        parameters: Action parameters (varies by action)
        
    Returns:
        Action result dictionary
        
    Examples:
        # Seestar focus control
        telescope_custom_action(device_id, "method_sync", 
            {"method": "get_focuser_position"})
        
        # Seestar movement
        telescope_custom_action(device_id, "method_sync",
            {"method": "scope_speed_move", 
             "params": {"speed": 300, "angle": 90, "dur_sec": 3}})
    """
    await ensure_initialized()
    return await telescope_tools.custom_action(
        device_id=device_id,
        action=action,
        parameters=parameters
    )


# Camera tools
@mcp.tool()
async def camera_connect(device_id: str) -> dict[str, Any]:
    """Connect to an ASCOM camera.
    
    Args:
        device_id: Device ID from discovery
        
    Returns:
        Connection status dictionary
    """
    await ensure_initialized()
    return await camera_tools.connect(device_id=device_id)


@mcp.tool()
async def camera_capture(
    device_id: str,
    exposure_seconds: float,
    light_frame: bool = True
) -> dict[str, Any]:
    """Capture an image with the camera.
    
    Args:
        device_id: Connected camera device ID
        exposure_seconds: Exposure time in seconds
        light_frame: True for light frame, False for dark (default: True)
        
    Returns:
        Capture result dictionary
    """
    await ensure_initialized()
    return await camera_tools.capture(
        device_id=device_id,
        exposure_seconds=exposure_seconds,
        light_frame=light_frame
    )


@mcp.tool()
async def camera_get_status(device_id: str) -> dict[str, Any]:
    """Get current camera status.
    
    Args:
        device_id: Connected camera device ID
        
    Returns:
        Camera status dictionary
    """
    await ensure_initialized()
    return await camera_tools.get_status(device_id=device_id)


# Resources
@mcp.resource("ascom://server/info")
async def get_server_info() -> str:
    """Information about the ASCOM MCP server."""
    info = {
        "name": "ascom-mcp-server",
        "version": __version__,
        "description": "MCP server for ASCOM astronomy equipment control",
        "ascom_version": "Alpaca v1.0",
        "implementation": "FastMCP",
        "capabilities": [
            "telescope", "camera", "focuser",
            "filterwheel", "dome", "rotator"
        ]
    }
    return json.dumps(info, indent=2)


@mcp.resource("ascom://devices/connected")
async def get_connected_devices() -> str:
    """List of currently connected ASCOM devices."""
    if device_manager:
        devices = await device_manager.get_connected_devices()
        return json.dumps({"devices": devices}, indent=2)
    return json.dumps({"devices": []}, indent=2)


@mcp.resource("ascom://devices/available")
async def get_available_devices() -> str:
    """List of available ASCOM devices from discovery."""
    if device_manager:
        devices = await device_manager.get_available_devices()
        return json.dumps({"devices": devices}, indent=2)
    return json.dumps({"devices": []}, indent=2)


def create_server():
    """Create and return the ASCOM MCP server instance.
    
    This function exists for compatibility with the existing API.
    """
    return mcp


def run():
    """Synchronous wrapper for entry point."""
    import argparse
    import sys
    import logging
    
    # Handle command line arguments
    parser = argparse.ArgumentParser(
        description="ASCOM MCP Server - Control astronomy equipment through AI"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mcp-server-ascom {__version__}"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Set logging level"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port for HTTP transports (default: 3000)"
    )
    
    args = parser.parse_args()
    
    # Update logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Set lifespan
    mcp.lifespan = server_lifespan
    
    # Log startup
    logger.info("server_starting", transport=args.transport, log_level=args.log_level)
    
    # Run the server
    if args.transport == "stdio":
        logger.debug("Starting stdio transport")
        try:
            logger.debug("Calling mcp.run()...")
            mcp.run(transport="stdio")
            logger.debug("mcp.run() returned")
        except Exception as e:
            logger.error("Error running stdio transport", error=str(e))
            import traceback
            traceback.print_exc()
    elif args.transport == "sse":
        logger.debug("Starting SSE transport", port=args.port)
        mcp.run(transport="sse", port=args.port)
    elif args.transport == "streamable-http":
        logger.debug("Starting streamable-http transport", port=args.port)
        mcp.run(transport="streamable-http", port=args.port)


if __name__ == "__main__":
    run()
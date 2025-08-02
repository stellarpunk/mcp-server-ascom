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
import time
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError

from . import __version__
from .ascom_logging import StructuredLogger
from .config import config
from .devices.manager import DeviceManager
from .devices.seestar_event_bridge import SeestarEventBridge
from .resources.event_stream import EventStreamManager
from .tools.camera import CameraTools
from .tools.discovery import DiscoveryTools
from .tools.events import EventTools
from .tools.telescope import TelescopeTools

# Structured logger (logs to stderr per MCP spec)
logger = StructuredLogger("ascom.server")

# Create the FastMCP server
mcp = FastMCP("ASCOM MCP Server")

# Global device manager (initialized at startup)
device_manager: DeviceManager | None = None
event_manager: EventStreamManager | None = None
event_bridge: SeestarEventBridge | None = None
discovery_tools: DiscoveryTools | None = None
telescope_tools: TelescopeTools | None = None
camera_tools: CameraTools | None = None
event_tools: EventTools | None = None


# Server lifecycle management
@asynccontextmanager
async def server_lifespan(server: FastMCP):
    """Manage server startup and shutdown."""
    global device_manager, event_manager, event_bridge, discovery_tools, telescope_tools, camera_tools, event_tools

    logger.info(f"Starting ASCOM MCP Server v{__version__} (FastMCP)")
    logger.debug("Lifespan: Initializing components...")

    # Initialize device manager and tools
    device_manager = DeviceManager()
    logger.debug("Created DeviceManager")
    await device_manager.initialize()
    logger.debug("DeviceManager initialized")

    event_manager = EventStreamManager()
    logger.debug("Created EventStreamManager")
    
    event_bridge = SeestarEventBridge(event_manager)
    logger.debug("Created SeestarEventBridge")
    
    event_bridge.setup_event_loop()  # Capture asyncio event loop for sync->async bridge
    logger.debug("Set up event loop for event bridge")
    
    # Register event callbacks
    device_manager.register_event_callback("on_device_connected", event_bridge.connect_to_seestar)
    logger.debug("Registered on_device_connected callback")
    
    # Note: SSE consumer will be started automatically when telescope connects
    # via the on_device_connected callback
    
    discovery_tools = DiscoveryTools(device_manager)
    telescope_tools = TelescopeTools(device_manager)
    camera_tools = CameraTools(device_manager)
    event_tools = EventTools(device_manager, event_manager)

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
    global device_manager, event_manager, event_bridge, discovery_tools, telescope_tools, camera_tools, event_tools

    logger.debug("ensure_initialized called")
    
    if device_manager is None:
        logger.debug("Creating DeviceManager in ensure_initialized")
        device_manager = DeviceManager()
        await device_manager.initialize()

    if event_manager is None:
        logger.debug("Creating EventStreamManager in ensure_initialized")
        event_manager = EventStreamManager()
        
    if event_bridge is None:
        logger.debug("Creating SeestarEventBridge in ensure_initialized")
        event_bridge = SeestarEventBridge(event_manager)
        event_bridge.setup_event_loop()  # Capture asyncio event loop
        logger.debug("Setting up event loop for event bridge")
        # Register event callbacks
        device_manager.register_event_callback("on_device_connected", event_bridge.connect_to_seestar)
        logger.debug("Registered on_device_connected callback in ensure_initialized")

    if discovery_tools is None:
        discovery_tools = DiscoveryTools(device_manager)

    if telescope_tools is None:
        telescope_tools = TelescopeTools(device_manager)

    if camera_tools is None:
        camera_tools = CameraTools(device_manager)
        
    if event_tools is None:
        event_tools = EventTools(device_manager, event_manager)


# Discovery tools
@mcp.tool()
async def discover_ascom_devices(ctx: Context, timeout: float = 5.0) -> dict[str, Any]:
    """Discover ASCOM devices on the network.

    Args:
        ctx: FastMCP context for logging and request metadata
        timeout: Discovery timeout in seconds (default: 5.0)

    Returns:
        Dictionary with discovered devices
    """
    await ensure_initialized()

    await ctx.debug(f"tool_called: discover_ascom_devices with timeout={timeout}")
    try:
        result = await discovery_tools.discover_devices(timeout=timeout)
        await ctx.info(f"devices_discovered: count={result.get('count', 0)}")
        return result
    except Exception as e:
        await ctx.error(f"discovery_failed: {str(e)}")
        raise ToolError(
            f"Device discovery failed: {str(e)}",
            code="discovery_failed",
            recoverable=True,
            details={"suggestions": ["Check network connectivity", "Ensure devices are powered on"]}
        )


@mcp.tool()
async def get_device_info(ctx: Context, device_id: str) -> dict[str, Any]:
    """Get detailed information about a specific ASCOM device.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Device ID from discovery

    Returns:
        Device information dictionary
    """
    await ensure_initialized()
    await ctx.info(f"getting_device_info: device_id={device_id}")
    try:
        return await discovery_tools.get_device_info(device_id=device_id)
    except Exception as e:
        await ctx.error(f"device_info_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot get info for device '{device_id}': {str(e)}",
            code="device_not_found",
            recoverable=True
        )


# Telescope tools
@mcp.tool()
async def telescope_connect(ctx: Context, device_id: str) -> dict[str, Any]:
    """Connect to an ASCOM telescope.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Device ID from discovery

    Returns:
        Connection status dictionary
    """
    await ensure_initialized()
    await ctx.info(f"connecting_telescope: device_id={device_id}")
    try:
        return await telescope_tools.connect(device_id=device_id)
    except Exception as e:
        await ctx.error(f"telescope_connect_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot connect to telescope '{device_id}': {str(e)}",
            code="connection_failed",
            recoverable=True,
            details={"suggestions": [
                "Check if seestar_alp is running (python root_app.py)",
                "Try using simulator mode",
                "Verify device ID from discovery"
            ]}
        )


@mcp.tool()
async def telescope_disconnect(ctx: Context, device_id: str) -> dict[str, Any]:
    """Disconnect from an ASCOM telescope.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Connected telescope device ID

    Returns:
        Disconnection status dictionary
    """
    await ensure_initialized()
    await ctx.info(f"disconnecting_telescope: device_id={device_id}")
    try:
        return await telescope_tools.disconnect(device_id=device_id)
    except Exception as e:
        await ctx.error(f"telescope_disconnect_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot disconnect telescope '{device_id}': {str(e)}",
            code="disconnect_failed",
            recoverable=True
        )


@mcp.tool()
async def telescope_goto(ctx: Context, device_id: str, ra: float, dec: float) -> dict[str, Any]:
    """Slew telescope to specific coordinates.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Connected telescope device ID
        ra: Right Ascension in hours (0-24)
        dec: Declination in degrees (-90 to +90)

    Returns:
        Slew status dictionary
    """
    await ensure_initialized()
    await ctx.info(f"telescope_goto: device_id={device_id}, ra={ra}, dec={dec}")
    try:
        return await telescope_tools.goto(device_id=device_id, ra=ra, dec=dec)
    except Exception as e:
        await ctx.error(f"telescope_goto_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot slew telescope: {str(e)}",
            code="slew_failed",
            recoverable=True
        )


@mcp.tool()
async def telescope_goto_object(ctx: Context, device_id: str, object_name: str) -> dict[str, Any]:
    """Slew telescope to a named celestial object.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Connected telescope device ID
        object_name: Name of celestial object (e.g., 'M31', 'Orion Nebula')

    Returns:
        Slew status dictionary
    """
    await ensure_initialized()
    await ctx.info(f"telescope_goto_object: device_id={device_id}, object={object_name}")
    try:
        return await telescope_tools.goto_object(
            device_id=device_id, object_name=object_name
        )
    except Exception as e:
        await ctx.error(f"telescope_goto_object_failed: device_id={device_id}, object={object_name}, error={str(e)}")
        raise ToolError(
            f"Cannot slew to object '{object_name}': {str(e)}",
            code="object_lookup_failed",
            recoverable=True,
            details={"suggestions": ["Check object name spelling", "Try catalog designation (e.g., M31, NGC 224)"]}
        )


@mcp.tool()
async def telescope_get_position(ctx: Context, device_id: str) -> dict[str, Any]:
    """Get current telescope position.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Connected telescope device ID

    Returns:
        Position information dictionary
    """
    await ensure_initialized()
    await ctx.debug(f"getting_telescope_position: device_id={device_id}")
    try:
        return await telescope_tools.get_position(device_id=device_id)
    except Exception as e:
        await ctx.error(f"get_position_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot get telescope position: {str(e)}",
            code="position_read_failed",
            recoverable=True
        )


@mcp.tool()
async def telescope_park(ctx: Context, device_id: str) -> dict[str, Any]:
    """Park telescope at home position.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Connected telescope device ID

    Returns:
        Park status dictionary
    """
    await ensure_initialized()
    await ctx.info(f"parking_telescope: device_id={device_id}")
    try:
        return await telescope_tools.park(device_id=device_id)
    except Exception as e:
        await ctx.error(f"telescope_park_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot park telescope: {str(e)}",
            code="park_failed",
            recoverable=True
        )


@mcp.tool()
async def telescope_custom_action(
    ctx: Context, device_id: str, action: str, parameters: str | dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute custom ASCOM action (e.g., Seestar-specific commands).

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Connected telescope device ID
        action: Action name (e.g., 'method_sync', 'goto_preset')
        parameters: Action parameters as JSON string or dict (varies by action)

    Returns:
        Action result dictionary

    Examples:
        # Seestar focus control
        telescope_custom_action(device_id, "method_sync",
            '{"method": "get_focuser_position"}')

        # Seestar movement
        telescope_custom_action(device_id, "method_sync",
            '{"method": "scope_speed_move", "params": {"speed": 300, "angle": 90, "dur_sec": 3}}')
    """
    await ensure_initialized()
    await ctx.info(f"telescope_custom_action: device_id={device_id}, action={action}")
    
    # Handle string parameters (workaround for MCP/Claude JSON serialization issue)
    if isinstance(parameters, str):
        try:
            import json
            parameters = json.loads(parameters)
            await ctx.debug("Parsed string parameters to dict")
        except json.JSONDecodeError as e:
            await ctx.error(f"Invalid JSON in parameters: {e}")
            raise ToolError(
                f"Invalid JSON in parameters: {e}",
                code="invalid_json",
                recoverable=True
            )
    
    # NEW: Validate Seestar commands based on OpenAPI findings
    if action == "method_sync" and isinstance(parameters, dict):
        method = parameters.get("method")
        if method:
            try:
                from .validation import SeestarValidator, ValidationError
                
                # Validate parameters against known formats
                validated = SeestarValidator.validate_command(
                    method, 
                    parameters.get("params")
                )
                
                # Update parameters with validated version
                parameters = validated
                await ctx.debug(f"Validated command: {method}")
                
            except ValidationError as e:
                # Provide helpful error message with correct format
                await ctx.error(f"Parameter validation failed: {e}")
                raise ToolError(
                    str(e),
                    code="invalid_parameters",
                    recoverable=True,
                    details={
                        "method": method,
                        "correct_format": e.correct_format,
                        "hint": "Check parameter format in documentation"
                    }
                )
    
    try:
        return await telescope_tools.custom_action(
            device_id=device_id, action=action, parameters=parameters
        )
    except Exception as e:
        await ctx.error(f"custom_action_failed: device_id={device_id}, action={action}, error={str(e)}")
        raise ToolError(
            f"Custom action '{action}' failed: {str(e)}",
            code="custom_action_failed",
            recoverable=True
        )


# Visual feedback tools
@mcp.tool()
async def telescope_preview(ctx: Context, device_id: str) -> dict[str, Any]:
    """Get current telescope view as an image.
    
    Captures the current view through the telescope for visual feedback.
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        
    Returns:
        Dictionary with base64 encoded JPEG image and metadata
    """
    await ensure_initialized()
    await ctx.info(f"Capturing preview from {device_id}")
    
    try:
        # Use custom action to get current image
        result = await telescope_tools.custom_action(
            device_id,
            "method_sync",
            {"method": "get_current_img"}
        )
        
        # Extract image data
        if result.get("success") and result.get("result"):
            import base64
            image_data = result["result"].get("image_data", "")
            
            return {
                "success": True,
                "image": image_data,  # Base64 encoded
                "format": "jpeg",
                "timestamp": result["result"].get("Timestamp")
            }
            
        # Fallback to MJPEG capture
        await ctx.warning("Direct capture failed, trying MJPEG stream")
        
        # Would implement MJPEG frame grab here
        return {
            "success": False,
            "error": "Preview capture not available",
            "mjpeg_url": f"http://seestar.local:5432/img/live_stacking"
        }
        
    except Exception as e:
        await ctx.error(f"Preview failed: {e}")
        raise ToolError(f"Failed to capture preview: {e}")


@mcp.tool()
async def telescope_where_am_i(ctx: Context, device_id: str) -> dict[str, Any]:
    """Get current telescope position with visual preview.
    
    Returns comprehensive status including coordinates, tracking state,
    and a preview image of the current view.
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        
    Returns:
        Dictionary with position, status, and preview image
    """
    await ensure_initialized()
    await ctx.info("Getting telescope position and preview")
    
    try:
        # Get position
        position_task = telescope_tools.custom_action(
            device_id,
            "method_sync", 
            {"method": "scope_get_equ_coord"}
        )
        
        # Get tracking state
        tracking_task = telescope_tools.custom_action(
            device_id,
            "method_sync",
            {"method": "scope_get_track_state"}
        )
        
        # Get preview
        preview_task = telescope_preview(ctx, device_id)
        
        # Run in parallel
        position, tracking, preview = await asyncio.gather(
            position_task,
            tracking_task,
            preview_task,
            return_exceptions=True
        )
        
        # Handle results
        result = {
            "success": True,
            "device_id": device_id
        }
        
        if isinstance(position, dict) and position.get("success"):
            pos_data = position.get("result", {})
            result.update({
                "ra": pos_data.get("ra"),
                "dec": pos_data.get("dec"),
                "alt": pos_data.get("alt"),
                "az": pos_data.get("az")
            })
            
        if isinstance(tracking, dict) and tracking.get("success"):
            track_data = tracking.get("result", {})
            result["tracking"] = track_data.get("tracking", False)
            
        if isinstance(preview, dict) and preview.get("success"):
            result["preview"] = preview
            
        return result
        
    except Exception as e:
        await ctx.error(f"Status check failed: {e}")
        raise ToolError(f"Failed to get telescope status: {e}")


@mcp.tool()
async def telescope_start_streaming(ctx: Context, device_id: str) -> dict[str, Any]:
    """Start video streaming and return MJPEG URL.
    
    Enables live video streaming from the telescope.
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        
    Returns:
        Dictionary with streaming URL and status
    """
    await ensure_initialized()
    await ctx.info("Starting video stream")
    
    try:
        # Start streaming
        result = await telescope_tools.custom_action(
            device_id,
            "method_sync",
            {"method": "begin_streaming"}
        )
        
        if result.get("success"):
            # Get device info for host
            device = await device_manager.get_device(device_id)
            host = device.host if device else "seestar.local"
            
            return {
                "success": True,
                "streaming": True,
                "mjpeg_url": f"http://{host}:5432/img/live_stacking",
                "frame_status_url": f"http://{host}:7556/1/vid/status",
                "message": "Streaming started. Open mjpeg_url in browser for live view."
            }
            
        return {
            "success": False,
            "error": result.get("error", "Failed to start streaming")
        }
        
    except Exception as e:
        await ctx.error(f"Streaming failed: {e}")
        raise ToolError(f"Failed to start streaming: {e}")


# Camera tools
@mcp.tool()
async def camera_connect(ctx: Context, device_id: str) -> dict[str, Any]:
    """Connect to an ASCOM camera.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Device ID from discovery

    Returns:
        Connection status dictionary
    """
    await ensure_initialized()
    await ctx.info(f"connecting_camera: device_id={device_id}")
    try:
        return await camera_tools.connect(device_id=device_id)
    except Exception as e:
        await ctx.error(f"camera_connect_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot connect to camera '{device_id}': {str(e)}",
            code="connection_failed",
            recoverable=True
        )


@mcp.tool()
async def camera_capture(
    ctx: Context, device_id: str, exposure_seconds: float, light_frame: bool = True
) -> dict[str, Any]:
    """Capture an image with the camera.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Connected camera device ID
        exposure_seconds: Exposure time in seconds
        light_frame: True for light frame, False for dark (default: True)

    Returns:
        Capture result dictionary
    """
    await ensure_initialized()
    await ctx.info(f"camera_capture: device_id={device_id}, exposure={exposure_seconds}, light_frame={light_frame}")
    try:
        return await camera_tools.capture(
            device_id=device_id, exposure_seconds=exposure_seconds, light_frame=light_frame
        )
    except Exception as e:
        await ctx.error(f"camera_capture_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Camera capture failed: {str(e)}",
            code="capture_failed",
            recoverable=True
        )


@mcp.tool()
async def camera_get_status(ctx: Context, device_id: str) -> dict[str, Any]:
    """Get current camera status.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Connected camera device ID

    Returns:
        Camera status dictionary
    """
    await ensure_initialized()
    await ctx.debug(f"getting_camera_status: device_id={device_id}")
    try:
        return await camera_tools.get_status(device_id=device_id)
    except Exception as e:
        await ctx.error(f"camera_status_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot get camera status: {str(e)}",
            code="status_read_failed",
            recoverable=True
        )


# Event tools
@mcp.tool()
async def get_event_history(
    ctx: Context,
    device_id: str,
    count: int = 50,
    event_types: list[str] | None = None,
    since_timestamp: float | None = None,
) -> dict[str, Any]:
    """Get historical events for a device.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Device identifier
        count: Maximum number of events to return (default: 50)
        event_types: Filter by specific event types
        since_timestamp: Get events after this Unix timestamp

    Returns:
        Event history and metadata
    """
    await ensure_initialized()
    await ctx.info(f"getting_event_history: device_id={device_id}, count={count}")
    try:
        return await event_tools.get_event_history(
            device_id=device_id,
            count=count,
            event_types=event_types,
            since_timestamp=since_timestamp,
        )
    except Exception as e:
        await ctx.error(f"get_event_history_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot get event history: {str(e)}",
            code="event_history_failed",
            recoverable=True
        )


@mcp.tool()
async def clear_event_history(ctx: Context, device_id: str) -> dict[str, Any]:
    """Clear event history for a device.

    Args:
        ctx: FastMCP context for logging and request metadata
        device_id: Device identifier

    Returns:
        Operation result
    """
    await ensure_initialized()
    await ctx.info(f"clearing_event_history: device_id={device_id}")
    try:
        return await event_tools.clear_event_history(device_id=device_id)
    except Exception as e:
        await ctx.error(f"clear_event_history_failed: device_id={device_id}, error={str(e)}")
        raise ToolError(
            f"Cannot clear event history: {str(e)}",
            code="clear_history_failed",
            recoverable=True
        )


@mcp.tool()
async def get_event_types(ctx: Context) -> dict[str, Any]:
    """Get available event types and descriptions.

    Args:
        ctx: FastMCP context for logging and request metadata

    Returns:
        Dictionary of event types and their descriptions
    """
    await ensure_initialized()
    await ctx.debug("getting_event_types")
    try:
        return await event_tools.get_event_types()
    except Exception as e:
        await ctx.error(f"get_event_types_failed: error={str(e)}")
        raise ToolError(
            f"Cannot get event types: {str(e)}",
            code="event_types_failed",
            recoverable=True
        )



# Resources
@mcp.resource("ascom://health")
async def health_check() -> str:
    """Health check endpoint with device and simulator status."""
    await ensure_initialized()
    
    health_data = {
        "status": "healthy",
        "version": __version__,
        "server": "ASCOM MCP Server",
        "implementation": "FastMCP 2.0",
        "devices": {
            "available": len(device_manager._available_devices) if device_manager else 0,
            "connected": len(device_manager._connected_devices) if device_manager else 0,
        },
        "known_devices": [
            {"host": host, "port": port, "name": name} 
            for host, port, name in config.known_devices
        ],
        "simulator_status": "Check ASCOM_SIMULATOR_DEVICES env var for simulator configuration"
    }
    return json.dumps(health_data, indent=2)

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
            "telescope",
            "camera",
            "focuser",
            "filterwheel",
            "dome",
            "rotator",
        ],
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


@mcp.resource("ascom://telescope/{device_id}/live-preview")
async def get_live_preview_url(device_id: str) -> str:
    """Get URL for live telescope view (MJPEG stream).
    
    Returns the URL where you can view live video from the telescope.
    Open this URL in a web browser to see real-time telescope feed.
    
    Args:
        device_id: Connected telescope device ID
        
    Returns:
        JSON with streaming URLs and status
    """
    await ensure_initialized()
    
    if device_manager:
        device = await device_manager.get_device(device_id)
        if device:
            host = device.host
            return json.dumps({
                "device_id": device_id,
                "mjpeg_url": f"http://{host}:5432/img/live_stacking",
                "frame_status_url": f"http://{host}:7556/1/vid/status",
                "web_ui_url": f"http://{host}:5432",
                "instructions": "Open mjpeg_url in browser for live view"
            }, indent=2)
    
    # Fallback
    return json.dumps({
        "device_id": device_id,
        "mjpeg_url": "http://seestar.local:5432/img/live_stacking",
        "error": "Device not found, using default URL"
    }, indent=2)


@mcp.resource("ascom://events/{device_id}/stream")
async def get_event_stream(device_id: str, ctx: Context) -> str:
    """Get the current event stream for a device.
    
    This resource provides the latest events from an ASCOM device.
    The resource will be automatically updated when new events arrive,
    triggering notifications to subscribed clients.
    
    Args:
        device_id: Device identifier
        ctx: FastMCP context
        
    Returns:
        JSON with current event state and recent events
    """
    await ensure_initialized()
    
    try:
        # Get current events (last 50 by default)
        events = await event_manager.get_events(device_id, limit=50)
        
        # Add server metadata
        events["server_time"] = time.time()
        events["resource_uri"] = f"ascom://events/{device_id}/stream"
        
        return json.dumps(events, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to get event stream: {e}")
        return json.dumps({
            "device_id": device_id,
            "status": "error",
            "error": str(e),
            "events": []
        }, indent=2)


def create_server():
    """Create and return the ASCOM MCP server instance.

    This function exists for compatibility with the existing API.
    """
    return mcp


def run():
    """Synchronous wrapper for entry point."""
    import argparse

    # Handle command line arguments
    parser = argparse.ArgumentParser(
        description="ASCOM MCP Server - Control astronomy equipment through AI"
    )
    parser.add_argument(
        "--version", action="version", version=f"mcp-server-ascom {__version__}"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Set logging level",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port for HTTP transports (default: 3000)",
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
        logger.debug(f"Starting SSE transport on port {args.port}")
        mcp.run(transport="sse", port=args.port)
    elif args.transport == "streamable-http":
        logger.debug(f"Starting streamable-http transport on port {args.port}")
        mcp.run(transport="streamable-http", port=args.port)


if __name__ == "__main__":
    run()

"""
Enhanced telescope tools with helper methods for common operations.

Based on OpenAPI analysis and 41 simulator-verified commands.
"""

from typing import Any, Dict, Optional
from fastmcp import Context
from ..server_fastmcp import mcp, telescope_custom_action


# ============================================================================
# Tracking & Movement Helpers (Prevent Error 207!)
# ============================================================================

@mcp.tool()
async def telescope_set_tracking(
    ctx: Context,
    device_id: str,
    enabled: bool
) -> dict[str, Any]:
    """
    Set telescope tracking state with correct parameter format.
    
    This helper prevents the common Error 207 caused by incorrect
    tracking parameter format.
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        enabled: True to enable tracking, False to disable
        
    Returns:
        Operation result
    """
    await ctx.info(f"Setting tracking: {enabled}")
    
    # Use validated format - direct boolean, NOT {"on": true}!
    return await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {"method": "scope_set_track_state", "params": enabled}
    )


@mcp.tool()
async def telescope_move_direction(
    ctx: Context,
    device_id: str,
    direction: str,
    duration: float = 3.0,
    speed: int = 300
) -> dict[str, Any]:
    """
    Move telescope in a specific direction.
    
    Note: Seestar movement is counterintuitive!
    - North/South = horizontal pan
    - East/West = vertical tilt
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        direction: One of "north", "south", "east", "west"
        duration: Movement duration in seconds (default: 3.0)
        speed: Movement speed 0-1000 (default: 300)
        
    Returns:
        Operation result
    """
    # Map directions to angles (counterintuitive!)
    direction_map = {
        "north": 0,    # Horizontal pan
        "east": 90,    # UP (vertical)
        "south": 180,  # Horizontal pan
        "west": 270    # DOWN (vertical)
    }
    
    angle = direction_map.get(direction.lower())
    if angle is None:
        raise ValueError(f"Invalid direction '{direction}'. Use: north, south, east, west")
    
    await ctx.info(f"Moving {direction} for {duration}s at speed {speed}")
    
    return await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {
            "method": "scope_speed_move",
            "params": {
                "speed": speed,
                "angle": angle,
                "dur_sec": duration
            }
        }
    )


# ============================================================================
# Focus Control Helpers
# ============================================================================

@mcp.tool()
async def telescope_auto_focus(
    ctx: Context,
    device_id: str
) -> dict[str, Any]:
    """
    Start automatic focus sequence.
    
    Note: Method name has typo in API: 'focuse' not 'focus'
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        
    Returns:
        Operation result
    """
    await ctx.info("Starting auto-focus")
    
    return await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {"method": "start_auto_focuse"}  # API typo!
    )


@mcp.tool()
async def telescope_set_focus(
    ctx: Context,
    device_id: str,
    position: int
) -> dict[str, Any]:
    """
    Set focus to specific position.
    
    Common ranges:
    - Stars: 1800-2000
    - Moon: 1700-1900
    - Terrestrial: 500-1500
    - Manhattan (~2mi): 1200-1350
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        position: Focus position (0-3000)
        
    Returns:
        Operation result
    """
    if not 0 <= position <= 3000:
        raise ValueError(f"Focus position must be 0-3000, got {position}")
    
    await ctx.info(f"Setting focus position: {position}")
    
    return await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {"method": "move_focuser", "params": {"step": position}}
    )


# ============================================================================
# Imaging Helpers
# ============================================================================

@mcp.tool()
async def telescope_start_preview(
    ctx: Context,
    device_id: str,
    mode: str = "star"
) -> dict[str, Any]:
    """
    Start preview/live view mode.
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        mode: View mode - "star", "moon", "sun", "scenery", "planet"
        
    Returns:
        Operation result
    """
    valid_modes = ["star", "moon", "sun", "scenery", "planet"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Use: {', '.join(valid_modes)}")
    
    await ctx.info(f"Starting {mode} preview")
    
    return await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {"method": "iscope_start_view", "params": {"mode": mode}}
    )


@mcp.tool()
async def telescope_start_stacking(
    ctx: Context,
    device_id: str,
    target_name: str,
    mode: str = "star"
) -> dict[str, Any]:
    """
    Start image stacking session.
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        target_name: Name for the stacking session
        mode: Stacking mode (default: "star")
        
    Returns:
        Operation result
    """
    await ctx.info(f"Starting {mode} stacking: {target_name}")
    
    return await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {
            "method": "iscope_start_stack",
            "params": {
                "mode": mode,
                "target_name": target_name
            }
        }
    )


# ============================================================================
# Status & Information Helpers
# ============================================================================

@mcp.tool()
async def telescope_get_full_status(
    ctx: Context,
    device_id: str
) -> dict[str, Any]:
    """
    Get comprehensive telescope status including position, tracking, etc.
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        
    Returns:
        Complete status information
    """
    await ctx.info("Getting full telescope status")
    
    # Get device state
    device_state = await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {"method": "get_device_state"}
    )
    
    # Get coordinates
    coords = await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {"method": "scope_get_equ_coord"}
    )
    
    # Get focus position
    focus = await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {"method": "get_focuser_position"}
    )
    
    # Combine results
    return {
        "device_state": device_state.get("Value"),
        "coordinates": coords.get("Value"),
        "focus_position": focus.get("Value"),
        "timestamp": ctx.request_id  # Use request ID as timestamp
    }


# ============================================================================
# Safety & Initialization
# ============================================================================

@mcp.tool()
async def telescope_safe_startup(
    ctx: Context,
    device_id: str,
    latitude: float,
    longitude: float,
    move_arm: bool = True
) -> dict[str, Any]:
    """
    Perform safe telescope startup sequence.
    
    This is REQUIRED before most operations!
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        latitude: Observer latitude (-90 to 90)
        longitude: Observer longitude (-180 to 180)
        move_arm: Whether to move telescope arm during startup
        
    Returns:
        Startup result
    """
    await ctx.info("Performing safe startup sequence")
    
    # First set location
    await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {
            "method": "set_user_location",
            "params": {"lat": latitude, "lon": longitude}
        }
    )
    
    # Then run startup sequence
    return await telescope_custom_action(
        ctx,
        device_id,
        "action_start_up_sequence",
        {
            "lat": latitude,
            "lon": longitude,
            "time_zone": "UTC",  # Can be customized
            "move_arm": move_arm
        }
    )


# ============================================================================
# Filter Wheel Helpers
# ============================================================================

@mcp.tool()
async def telescope_set_filter(
    ctx: Context,
    device_id: str,
    filter_name: str
) -> dict[str, Any]:
    """
    Set filter wheel position by name.
    
    Common filters:
    - Position 0: Clear/Luminance
    - Position 1: UV/IR Cut
    - Position 2: Light Pollution
    
    Args:
        ctx: FastMCP context
        device_id: Connected telescope device ID
        filter_name: Filter name or position (0-2)
        
    Returns:
        Operation result
    """
    # Map filter names to positions
    filter_map = {
        "clear": 0,
        "luminance": 0,
        "l": 0,
        "uv/ir cut": 1,
        "uvir": 1,
        "cut": 1,
        "light pollution": 2,
        "lp": 2,
        "lpf": 2,
    }
    
    # Try to parse as number first
    try:
        position = int(filter_name)
    except ValueError:
        # Look up by name
        position = filter_map.get(filter_name.lower())
        if position is None:
            raise ValueError(
                f"Unknown filter '{filter_name}'. "
                f"Use position (0-2) or name: {', '.join(filter_map.keys())}"
            )
    
    if not 0 <= position <= 2:
        raise ValueError(f"Filter position must be 0-2, got {position}")
    
    await ctx.info(f"Setting filter position: {position}")
    
    return await telescope_custom_action(
        ctx,
        device_id,
        "method_sync",
        {"method": "set_wheel_position", "params": {"pos": position}}
    )
"""
Example of how the ASCOM MCP server would look with FastMCP 2.0

This is much cleaner than the low-level API!
"""

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# Create the FastMCP server instance
mcp = FastMCP("ascom-mcp-server")

# Discovery tools
@mcp.tool()
async def discover_ascom_devices(timeout: float = 5.0) -> str:
    """Discover ASCOM devices on the network."""
    # This would call the discovery logic
    return "Found 2 devices: Telescope-1, Camera-1"

@mcp.tool()
async def get_device_info(device_id: str) -> str:
    """Get detailed information about a specific ASCOM device."""
    return f"Device {device_id}: Connected, Ready"

# Telescope tools
@mcp.tool()
async def telescope_connect(device_id: str) -> str:
    """Connect to an ASCOM telescope."""
    return f"Connected to telescope {device_id}"

@mcp.tool()
async def telescope_goto(device_id: str, ra: float, dec: float) -> str:
    """Slew telescope to specific coordinates.
    
    Args:
        device_id: Connected telescope device ID
        ra: Right Ascension in hours (0-24)
        dec: Declination in degrees (-90 to +90)
    """
    return f"Slewing telescope to RA={ra}h, Dec={dec}°"

@mcp.tool()
async def telescope_goto_object(device_id: str, object_name: str) -> str:
    """Slew telescope to a named celestial object.
    
    Args:
        device_id: Connected telescope device ID
        object_name: Name of celestial object (e.g., 'M31', 'Orion Nebula')
    """
    return f"Slewing telescope to {object_name}"

# Resources
@mcp.resource("ascom://server/info")
async def get_server_info() -> str:
    """Information about the ASCOM MCP server."""
    return """{
        "name": "ascom-mcp-server",
        "version": "0.3.0",
        "description": "MCP server for ASCOM astronomy equipment control",
        "ascom_version": "Alpaca v1.0"
    }"""

@mcp.resource("ascom://devices/connected")
async def get_connected_devices() -> str:
    """List of currently connected ASCOM devices."""
    return '{"devices": []}'

# Run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
#!/usr/bin/env python3
"""
DEPRECATED: This module uses the low-level MCP Server API.

As of v0.3.0, we have migrated to FastMCP from the official MCP SDK.
Please use server_fastmcp.py instead.

This file is kept for backward compatibility but will be removed in v0.4.0.

Original description:
MCP Server for ASCOM astronomy equipment control.

This server bridges Model Context Protocol to ASCOM Alpaca devices,
enabling AI assistants to control telescopes, cameras, and other
astronomical equipment through natural language.
"""

import asyncio
import json
import logging
import os
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    Implementation,
    InitializeRequest,
    InitializeResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    ResourcesCapability,
    ServerCapabilities,
    Tool,
    ToolsCapability,
)

from . import __version__
from .constants import (
    MCP_PROTOCOL_VERSION,
    SERVER_NAME,
    SUPPORTED_PROTOCOL_VERSIONS,
)
from .devices.manager import DeviceManager
from .tools.camera import CameraTools
from .tools.discovery import DiscoveryTools
from .tools.telescope import TelescopeTools
from .utils.content import (
    create_error_content,
    create_structured_content,
    create_text_content,
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AscomMCPServer(Server):
    """ASCOM MCP Server implementation."""

    def __init__(self):
        super().__init__(SERVER_NAME)
        self.device_manager: DeviceManager | None = None
        self.discovery_tools: DiscoveryTools | None = None
        self.telescope_tools: TelescopeTools | None = None
        self.camera_tools: CameraTools | None = None
        self.negotiated_protocol_version: str = MCP_PROTOCOL_VERSION
        
        # Register MCP protocol handlers
        @self.list_tools()
        async def _list_tools() -> list[Tool]:
            # Initialize if needed
            if self.device_manager is None:
                await self._ensure_initialized()
            # Return the tools directly
            return self._get_tools_list()
        
        @self.list_resources()
        async def _list_resources() -> list[Resource]:
            # Return the resources directly
            return self._get_resources_list()
        
        @self.call_tool()
        async def _call_tool(name: str, arguments: dict[str, Any] | None) -> list[Any]:
            # Initialize if needed
            if self.device_manager is None:
                await self._ensure_initialized()
            # Call the tool and return the content
            return await self._execute_tool(name, arguments)
    
    async def _ensure_initialized(self):
        """Ensure device manager and tools are initialized."""
        if self.device_manager is None:
            self.device_manager = DeviceManager()
            await self.device_manager.initialize()
            
            self.discovery_tools = DiscoveryTools(self.device_manager)
            self.telescope_tools = TelescopeTools(self.device_manager)
            self.camera_tools = CameraTools(self.device_manager)
    
    def _get_tools_list(self) -> list[Tool]:
        """Get the list of available tools."""
        return [
            # Discovery tools
            Tool(
                name="discover_ascom_devices",
                description="Discover ASCOM devices on the network",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timeout": {
                            "type": "number",
                            "description": "Discovery timeout in seconds",
                            "default": 5.0
                        }
                    }
                }
            ),
            Tool(
                name="get_device_info",
                description="Get detailed information about a specific ASCOM device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Device ID from discovery"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            # Telescope tools
            Tool(
                name="telescope_connect",
                description="Connect to an ASCOM telescope",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Device ID from discovery"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            Tool(
                name="telescope_disconnect",
                description="Disconnect from an ASCOM telescope",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            Tool(
                name="telescope_goto",
                description="Slew telescope to specific coordinates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        },
                        "ra": {
                            "type": "number",
                            "description": "Right Ascension in hours (0-24)"
                        },
                        "dec": {
                            "type": "number",
                            "description": "Declination in degrees (-90 to +90)"
                        }
                    },
                    "required": ["device_id", "ra", "dec"]
                }
            ),
            Tool(
                name="telescope_goto_object",
                description="Slew telescope to a named celestial object",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        },
                        "object_name": {
                            "type": "string",
                            "description": (
                                "Name of celestial object "
                                "(e.g., 'M31', 'Orion Nebula')"
                            )
                        }
                    },
                    "required": ["device_id", "object_name"]
                }
            ),
            Tool(
                name="telescope_get_position",
                description="Get current telescope position",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            Tool(
                name="telescope_park",
                description="Park telescope at home position",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            # Camera tools
            Tool(
                name="camera_connect",
                description="Connect to an ASCOM camera",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Device ID from discovery"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            Tool(
                name="camera_capture",
                description="Capture an image with the camera",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected camera device ID"
                        },
                        "exposure_seconds": {
                            "type": "number",
                            "description": "Exposure time in seconds"
                        },
                        "light_frame": {
                            "type": "boolean",
                            "description": "True for light frame, False for dark",
                            "default": True
                        }
                    },
                    "required": ["device_id", "exposure_seconds"]
                }
            ),
            Tool(
                name="camera_get_status",
                description="Get current camera status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected camera device ID"
                        }
                    },
                    "required": ["device_id"]
                }
            )
        ]
    
    def _get_resources_list(self) -> list[Resource]:
        """Get the list of available resources."""
        return [
            Resource(
                uri="ascom://server/info",
                name="Server Information",
                description="Information about the ASCOM MCP server",
                mimeType="application/json"
            ),
            Resource(
                uri="ascom://devices/connected",
                name="Connected Devices",
                description="List of currently connected ASCOM devices",
                mimeType="application/json"
            ),
            Resource(
                uri="ascom://devices/available",
                name="Available Devices",
                description="List of available ASCOM devices from discovery",
                mimeType="application/json"
            )
        ]
    
    async def _execute_tool(self, tool_name: str, args: dict[str, Any] | None) -> list[Any]:
        """Execute a tool and return the content."""
        args = args or {}
        
        try:
            # Discovery tools
            if tool_name == "discover_ascom_devices":
                result = await self.discovery_tools.discover_devices(
                    timeout=args.get("timeout", 5.0)
                )
            elif tool_name == "get_device_info":
                result = await self.discovery_tools.get_device_info(
                    device_id=args["device_id"]
                )
            # Telescope tools
            elif tool_name == "telescope_connect":
                result = await self.telescope_tools.connect(
                    device_id=args["device_id"]
                )
            elif tool_name == "telescope_disconnect":
                result = await self.telescope_tools.disconnect(
                    device_id=args["device_id"]
                )
            elif tool_name == "telescope_goto":
                result = await self.telescope_tools.goto(
                    device_id=args["device_id"],
                    ra=args["ra"],
                    dec=args["dec"]
                )
            elif tool_name == "telescope_goto_object":
                result = await self.telescope_tools.goto_object(
                    device_id=args["device_id"],
                    object_name=args["object_name"]
                )
            elif tool_name == "telescope_get_position":
                result = await self.telescope_tools.get_position(
                    device_id=args["device_id"]
                )
            elif tool_name == "telescope_park":
                result = await self.telescope_tools.park(
                    device_id=args["device_id"]
                )
            # Camera tools
            elif tool_name == "camera_connect":
                result = await self.camera_tools.connect(
                    device_id=args["device_id"]
                )
            elif tool_name == "camera_capture":
                result = await self.camera_tools.capture(
                    device_id=args["device_id"],
                    exposure_seconds=args["exposure_seconds"],
                    light_frame=args.get("light_frame", True)
                )
            elif tool_name == "camera_get_status":
                result = await self.camera_tools.get_status(
                    device_id=args["device_id"]
                )
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # Create content for the result
            if isinstance(result, dict):
                # Check if error response
                if not result.get("success", True):
                    content = create_error_content(
                        error_type=result.get("error_type", "tool_error"),
                        message=result.get("error", "Unknown error"),
                        details=result
                    )
                else:
                    # Success - return structured content
                    content = create_structured_content(
                        result,
                        text_fallback=self._create_fallback_text(tool_name, result)
                    )
            else:
                # Simple text result
                content = [create_text_content(str(result))]

            return content

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            # Use structured error content
            content = create_error_content(
                error_type="tool_execution_error",
                message=str(e),
                details={"tool": tool_name, "exception": type(e).__name__}
            )
            return content

    async def handle_initialize(self, request: InitializeRequest) -> InitializeResult:
        """Handle initialization request with version negotiation."""
        logger.info(
            f"Initializing ASCOM MCP Server "
            f"(client protocol: {request.params.protocolVersion})"
        )

        # Version negotiation - find best matching version
        client_version = str(request.params.protocolVersion)
        if client_version in SUPPORTED_PROTOCOL_VERSIONS:
            self.negotiated_protocol_version = client_version
        else:
            # Use latest if client version is unknown
            self.negotiated_protocol_version = MCP_PROTOCOL_VERSION
            logger.warning(
                f"Unknown client protocol version {client_version}, "
                f"using {MCP_PROTOCOL_VERSION}"
            )

        # Initialize device manager and tools
        self.device_manager = DeviceManager()
        await self.device_manager.initialize()

        self.discovery_tools = DiscoveryTools(self.device_manager)
        self.telescope_tools = TelescopeTools(self.device_manager)
        self.camera_tools = CameraTools(self.device_manager)

        logger.info(
            f"ASCOM MCP Server initialized successfully "
            f"(negotiated protocol: {self.negotiated_protocol_version})"
        )

        return InitializeResult(
            protocolVersion=self.negotiated_protocol_version,
            capabilities=ServerCapabilities(
                tools=ToolsCapability(listChanged=True),  # Support tool list updates
                # Support resource subscriptions
                resources=ResourcesCapability(subscribe=True)
            ),
            serverInfo=Implementation(
                name=SERVER_NAME,
                version=__version__
            )
        )

    async def handle_list_resources(
        self, request: ListResourcesRequest
    ) -> ListResourcesResult:
        """Handle list resources request."""
        resources = [
            Resource(
                uri="ascom://server/info",
                name="Server Information",
                description="Information about the ASCOM MCP server",
                mimeType="application/json"
            ),
            Resource(
                uri="ascom://devices/connected",
                name="Connected Devices",
                description="List of currently connected ASCOM devices",
                mimeType="application/json"
            ),
            Resource(
                uri="ascom://devices/available",
                name="Available Devices",
                description="List of available ASCOM devices from discovery",
                mimeType="application/json"
            )
        ]

        return ListResourcesResult(resources=resources)

    async def handle_read_resource(
        self, request: ReadResourceRequest
    ) -> ReadResourceResult:
        """Handle read resource request."""
        uri = request.uri

        if uri == "ascom://server/info":
            from . import __version__
            content = {
                "name": "ascom-mcp-server",
                "version": __version__,
                "description": "MCP server for ASCOM astronomy equipment control",
                "ascom_version": "Alpaca v1.0",
                "capabilities": [
                    "telescope", "camera", "focuser",
                    "filterwheel", "dome", "rotator"
                ]
            }
            return ReadResourceResult(
                contents=[create_text_content(
                    text=json.dumps(content, indent=2)
                )]
            )

        elif uri == "ascom://devices/connected":
            devices = await self.device_manager.get_connected_devices()
            return ReadResourceResult(
                contents=[create_text_content(
                    text=json.dumps({"devices": devices}, indent=2)
                )]
            )

        elif uri == "ascom://devices/available":
            devices = await self.device_manager.get_available_devices()
            return ReadResourceResult(
                contents=[create_text_content(
                    text=json.dumps({"devices": devices}, indent=2)
                )]
            )

        else:
            raise ValueError(f"Unknown resource: {uri}")

    async def handle_list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """Handle list tools request."""
        tools = [
            # Discovery tools
            Tool(
                name="discover_ascom_devices",
                description="Discover ASCOM devices on the network",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timeout": {
                            "type": "number",
                            "description": "Discovery timeout in seconds",
                            "default": 5.0
                        }
                    }
                }
            ),
            Tool(
                name="get_device_info",
                description="Get detailed information about a specific ASCOM device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Device ID from discovery"
                        }
                    },
                    "required": ["device_id"]
                }
            ),

            # Telescope tools
            Tool(
                name="telescope_connect",
                description="Connect to an ASCOM telescope",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Device ID from discovery"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            Tool(
                name="telescope_disconnect",
                description="Disconnect from an ASCOM telescope",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            Tool(
                name="telescope_goto",
                description="Slew telescope to specific coordinates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        },
                        "ra": {
                            "type": "number",
                            "description": "Right Ascension in hours (0-24)"
                        },
                        "dec": {
                            "type": "number",
                            "description": "Declination in degrees (-90 to +90)"
                        }
                    },
                    "required": ["device_id", "ra", "dec"]
                }
            ),
            Tool(
                name="telescope_goto_object",
                description="Slew telescope to a named celestial object",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        },
                        "object_name": {
                            "type": "string",
                            "description": (
                                "Name of celestial object "
                                "(e.g., 'M31', 'Orion Nebula')"
                            )
                        }
                    },
                    "required": ["device_id", "object_name"]
                }
            ),
            Tool(
                name="telescope_get_position",
                description="Get current telescope position",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            Tool(
                name="telescope_park",
                description="Park telescope at home position",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected telescope device ID"
                        }
                    },
                    "required": ["device_id"]
                }
            ),

            # Camera tools
            Tool(
                name="camera_connect",
                description="Connect to an ASCOM camera",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Device ID from discovery"
                        }
                    },
                    "required": ["device_id"]
                }
            ),
            Tool(
                name="camera_capture",
                description="Capture an image with the camera",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected camera device ID"
                        },
                        "exposure_seconds": {
                            "type": "number",
                            "description": "Exposure time in seconds"
                        },
                        "light_frame": {
                            "type": "boolean",
                            "description": "True for light frame, False for dark",
                            "default": True
                        }
                    },
                    "required": ["device_id", "exposure_seconds"]
                }
            ),
            Tool(
                name="camera_get_status",
                description="Get current camera status",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "Connected camera device ID"
                        }
                    },
                    "required": ["device_id"]
                }
            )
        ]

        return ListToolsResult(tools=tools)

    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool call request."""
        tool_name = request.params.name
        args = request.params.arguments or {}

        try:
            # Discovery tools
            if tool_name == "discover_ascom_devices":
                result = await self.discovery_tools.discover_devices(
                    timeout=args.get("timeout", 5.0)
                )
            elif tool_name == "get_device_info":
                result = await self.discovery_tools.get_device_info(
                    device_id=args["device_id"]
                )

            # Telescope tools
            elif tool_name == "telescope_connect":
                result = await self.telescope_tools.connect(
                    device_id=args["device_id"]
                )
            elif tool_name == "telescope_disconnect":
                result = await self.telescope_tools.disconnect(
                    device_id=args["device_id"]
                )
            elif tool_name == "telescope_goto":
                result = await self.telescope_tools.goto(
                    device_id=args["device_id"],
                    ra=args["ra"],
                    dec=args["dec"]
                )
            elif tool_name == "telescope_goto_object":
                result = await self.telescope_tools.goto_object(
                    device_id=args["device_id"],
                    object_name=args["object_name"]
                )
            elif tool_name == "telescope_get_position":
                result = await self.telescope_tools.get_position(
                    device_id=args["device_id"]
                )
            elif tool_name == "telescope_park":
                result = await self.telescope_tools.park(
                    device_id=args["device_id"]
                )

            # Camera tools
            elif tool_name == "camera_connect":
                result = await self.camera_tools.connect(
                    device_id=args["device_id"]
                )
            elif tool_name == "camera_capture":
                result = await self.camera_tools.capture(
                    device_id=args["device_id"],
                    exposure_seconds=args["exposure_seconds"],
                    light_frame=args.get("light_frame", True)
                )
            elif tool_name == "camera_get_status":
                result = await self.camera_tools.get_status(
                    device_id=args["device_id"]
                )
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            # Create content for the result
            if isinstance(result, dict):
                # Check if error response
                if not result.get("success", True):
                    content = create_error_content(
                        error_type=result.get("error_type", "tool_error"),
                        message=result.get("error", "Unknown error"),
                        details=result
                    )
                else:
                    # Success - return structured content
                    content = create_structured_content(
                        result,
                        text_fallback=self._create_fallback_text(tool_name, result)
                    )
            else:
                # Simple text result
                content = [create_text_content(str(result))]

            # Note: structuredContent field is available in CallToolResult but
            # we use content blocks for broader compatibility
            return CallToolResult(content=content)

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            # Use structured error content
            content = create_error_content(
                error_type="tool_execution_error",
                message=str(e),
                details={"tool": tool_name, "exception": type(e).__name__}
            )
            return CallToolResult(
                content=content,
                isError=True
            )

    def _create_fallback_text(self, tool_name: str, result: dict[str, Any]) -> str:
        """Create human-readable fallback text for tool results."""
        if tool_name == "discover_ascom_devices":
            devices = result.get("devices", [])
            count = len(devices)
            if count == 0:
                return "No devices found"
            elif count == 1:
                return f"Found 1 device: {devices[0].get('name', 'Unknown')}"
            else:
                return f"Found {count} devices"
        elif tool_name == "telescope_connect":
            return f"Connected to {result.get('device_name', 'telescope')}"
        elif tool_name == "telescope_goto":
            ra = result.get('ra', '?')
            dec = result.get('dec', '?')
            return f"Slewing to RA {ra}h, Dec {dec}°"
        elif tool_name == "telescope_goto_object":
            return f"Slewing to {result.get('object_name', 'target')}"
        else:
            return f"Tool '{tool_name}' completed"

    async def cleanup(self):
        """Cleanup on server shutdown."""
        logger.info("Shutting down ASCOM MCP Server")
        if self.device_manager:
            await self.device_manager.shutdown()
        logger.info("Server shutdown complete")


def create_server():
    """Create and return the ASCOM MCP server instance."""
    return AscomMCPServer()


async def main():
    """Main entry point for running the server."""
    import argparse

    from mcp.server.stdio import stdio_server

    # Handle command line arguments
    parser = argparse.ArgumentParser(
        description="ASCOM MCP Server - Control astronomy equipment through AI"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mcp-server-ascom {__import__('ascom_mcp').__version__}"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Set logging level"
    )

    args = parser.parse_args()

    # Update logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info(f"Starting ASCOM MCP Server v{__import__('ascom_mcp').__version__}")
    logger.info("Use --help for options")

    server = create_server()

    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version=__version__,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


def run():
    """Synchronous wrapper for entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())

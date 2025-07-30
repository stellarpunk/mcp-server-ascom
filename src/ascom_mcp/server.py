#!/usr/bin/env python3
"""
MCP Server for ASCOM astronomy equipment control.

This server bridges Model Context Protocol to ASCOM Alpaca devices,
enabling AI assistants to control telescopes, cameras, and other
astronomical equipment through natural language.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from mcp import Server
from mcp.types import (
    InitializeRequest,
    InitializeResult,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
    ListToolsRequest,
    ListToolsResult,
    CallToolRequest,
    CallToolResult,
    TextContent,
    Resource,
    Tool,
    ServerCapabilities,
    Implementation,
    LATEST_PROTOCOL_VERSION
)

from .tools.discovery import DiscoveryTools
from .tools.telescope import TelescopeTools
from .tools.camera import CameraTools
from .devices.manager import DeviceManager
from .utils.errors import AscomMCPError

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AscomMCPServer(Server):
    """ASCOM MCP Server implementation."""
    
    def __init__(self):
        super().__init__("ascom-mcp-server")
        self.device_manager: Optional[DeviceManager] = None
        self.discovery_tools: Optional[DiscoveryTools] = None
        self.telescope_tools: Optional[TelescopeTools] = None
        self.camera_tools: Optional[CameraTools] = None
        
    async def handle_initialize(self, request: InitializeRequest) -> InitializeResult:
        """Handle initialization request."""
        logger.info("Initializing ASCOM MCP Server")
        
        # Initialize device manager and tools
        self.device_manager = DeviceManager()
        await self.device_manager.initialize()
        
        self.discovery_tools = DiscoveryTools(self.device_manager)
        self.telescope_tools = TelescopeTools(self.device_manager)
        self.camera_tools = CameraTools(self.device_manager)
        
        logger.info("ASCOM MCP Server initialized successfully")
        
        return InitializeResult(
            protocolVersion=LATEST_PROTOCOL_VERSION,
            capabilities=ServerCapabilities(
                tools=True,
                resources=True
            ),
            serverInfo=Implementation(
                name="ascom-mcp-server",
                version="0.1.0"
            )
        )
        
    async def handle_list_resources(self, request: ListResourcesRequest) -> ListResourcesResult:
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
        
    async def handle_read_resource(self, request: ReadResourceRequest) -> ReadResourceResult:
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
                contents=[TextContent(
                    uri=uri,
                    text=json.dumps(content, indent=2),
                    mimeType="application/json"
                )]
            )
            
        elif uri == "ascom://devices/connected":
            devices = await self.device_manager.get_connected_devices()
            return ReadResourceResult(
                contents=[TextContent(
                    uri=uri,
                    text=json.dumps({"devices": devices}, indent=2),
                    mimeType="application/json"
                )]
            )
            
        elif uri == "ascom://devices/available":
            devices = await self.device_manager.get_available_devices()
            return ReadResourceResult(
                contents=[TextContent(
                    uri=uri,
                    text=json.dumps({"devices": devices}, indent=2),
                    mimeType="application/json"
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
                            "description": "Name of celestial object (e.g., 'M31', 'Orion Nebula')"
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
        tool_name = request.name
        args = request.arguments
        
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
                
            return CallToolResult(
                content=[TextContent(text=json.dumps(result, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            error_result = {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
            return CallToolResult(
                content=[TextContent(text=json.dumps(error_result, indent=2))],
                isError=True
            )
            
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
    import sys
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
            read_stream=read_stream,
            write_stream=write_stream,
            # Run initialization in server.run()
            initialize_fn=server.handle_initialize
        )


if __name__ == "__main__":
    asyncio.run(main())
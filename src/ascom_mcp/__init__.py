"""MCP Server for ASCOM astronomy equipment control."""

__version__ = "0.1.0"

from .server import create_server

__all__ = ["create_server", "__version__"]
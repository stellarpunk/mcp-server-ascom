"""
ASCOM MCP Resources.

This module provides resource handlers for the ASCOM MCP server,
including event streams and device state resources.
"""

from .event_stream import EventStreamManager

__all__ = ["EventStreamManager"]
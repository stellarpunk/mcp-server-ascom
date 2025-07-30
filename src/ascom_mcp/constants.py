"""
Protocol constants and configuration for ASCOM MCP Server.

Following MCP 2025-06-18 specification and preparing for future updates.
"""

# Protocol versions
MCP_PROTOCOL_VERSION = "2025-06-18"  # Current MCP specification in our package
# Note: We support older versions for compatibility
SUPPORTED_PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]

# Server metadata
SERVER_NAME = "ascom-mcp-server"
SERVER_DESCRIPTION = "MCP server for ASCOM astronomy equipment control"

# Content types
CONTENT_TYPE_TEXT = "text"
CONTENT_TYPE_IMAGE = "image"
CONTENT_TYPE_RESOURCE = "resource"

# Error codes (following MCP best practices)
ERROR_DEVICE_NOT_FOUND = "device_not_found"
ERROR_CONNECTION_FAILED = "connection_failed"
ERROR_INVALID_COORDINATES = "invalid_coordinates"
ERROR_OPERATION_FAILED = "operation_failed"

# Security configuration (optional features)
OAUTH_ENABLED = False  # Set to True to enable OAuth 2.0
OAUTH_ISSUER = "https://auth.example.com"  # Update for your OAuth provider
OAUTH_AUDIENCE = "ascom-mcp-server"

# Future features (when MCP spec supports them)
STRUCTURED_CONTENT_ENABLED = False  # Use structuredContent field when available
ELICITATION_ENABLED = False  # Request user input when supported

# Tool response patterns
MAX_STRUCTURED_CONTENT_SIZE = 1048576  # 1MB - larger results use resource links
DISCOVERY_TIMEOUT_DEFAULT = 5.0
DISCOVERY_TIMEOUT_MAX = 30.0

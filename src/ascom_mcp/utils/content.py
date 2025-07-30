"""
Content creation utilities for MCP 2025-06-18 specification.

Provides helper functions for creating structured content, text content,
and resource links following best practices.
"""

from typing import Any

from mcp.types import ImageContent, TextContent

from ..constants import CONTENT_TYPE_TEXT


def create_text_content(text: str, mime_type: str = "text/plain") -> TextContent:
    """
    Create a TextContent object following MCP 2025-06-18 spec.

    Args:
        text: The text content
        mime_type: MIME type of the content (default: text/plain)

    Returns:
        TextContent object with proper type field
    """
    return TextContent(
        type=CONTENT_TYPE_TEXT,
        text=text
    )


def create_structured_content(
    data: dict[str, Any],
    text_fallback: str | None = None,
    include_text: bool = True
) -> list[TextContent | ImageContent]:
    """
    Create structured content with JSON data and optional text fallback.

    Following MCP 2025-06-18 best practices for structured tool outputs.

    Args:
        data: Structured data as dictionary
        text_fallback: Optional human-readable summary
        include_text: Whether to include text representation

    Returns:
        List of content blocks
    """
    import json

    content_blocks = []

    # Add structured JSON content
    json_text = json.dumps(data, indent=2)
    content_blocks.append(create_text_content(json_text, "application/json"))

    # Add human-readable fallback if requested
    if include_text and text_fallback:
        content_blocks.append(create_text_content(text_fallback))

    return content_blocks


def create_error_content(
    error_type: str,
    message: str,
    details: dict[str, Any] | None = None
) -> list[TextContent | ImageContent]:
    """
    Create structured error content following MCP best practices.

    Tool-level errors should be in structured content, not protocol errors.

    Args:
        error_type: Type of error (e.g., "device_not_found")
        message: Human-readable error message
        details: Additional error details

    Returns:
        List of content blocks with error information
    """
    error_data = {
        "error": {
            "type": error_type,
            "message": message,
        }
    }

    if details:
        error_data["error"]["details"] = details

    return create_structured_content(
        error_data,
        text_fallback=f"Error: {message}",
        include_text=True
    )


# Note: Resource links will be implemented when MCP types support ResourceContent
# For now, all content is returned inline as TextContent

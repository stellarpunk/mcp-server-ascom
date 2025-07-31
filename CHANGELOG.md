# Changelog

## [0.3.0] - 2025-01-30

FastMCP. Structured logging. Half the code.

### Changed
- Migrated to FastMCP from low-level Server API
- Default entry point uses FastMCP implementation
- Reduced codebase: 600 → 300 lines

### Added
- Structured JSON logging to stderr
- OpenTelemetry-compatible log format
- Comprehensive test script: test_v030.py

### Fixed
- "Method not found" errors in Claude Desktop
- Decorator return type mismatches
- Protocol compliance issues

### Migration
From v0.2.x: No API changes. Internal improvements only.

Key files changed:
- `server.py` → `server_fastmcp.py` (new implementation)
- `__main__.py` (imports FastMCP version)
- `logging.py` (new structured logger)

## [0.2.6] - 2025-01-30

### Fixed
- Decorator functions return lists, not Result objects
- UV cache issues with local development

## [0.2.5] - 2025-01-30

### Fixed
- Added missing method registration in __init__
- Integration tests verify all MCP methods

## [0.2.4] - 2025-01-30

### Fixed
- tools/list and resources/list registration
- Claude Desktop compatibility

## [0.2.3] - 2025-01-29

### Added
- Initial PyPI release
- Full MCP protocol support

## [0.2.2] - 2025-07-30

### Fixed
- Removed `initialize_fn` parameter - MCP API changed

## [0.2.1] - 2025-07-30

### Fixed
- CLI entry point - added synchronous wrapper for `mcp-server-ascom` command
- Removed deprecated license classifier per modern packaging standards

## [0.2.0] - 2025-07-30

MCP 2025-06-18. Modern. Fast. Secure.

### Added
- MCP 2025-06-18 protocol support
- Structured JSON responses with text fallbacks
- Version negotiation (2025-06-18, 2025-03-26, 2024-11-05)
- Optional OAuth 2.0 security (disabled by default)
- Security module with JWT support
- Content creation utilities
- Human-readable error suggestions
- Helper script for MCP Inspector

### Changed
- Protocol: 2024-11-05 → 2025-06-18
- Responses: text-only → structured JSON + fallback
- Errors: basic → contextual with fixes
- Writing: verbose → concise

### Fixed
- TextContent type field
- alpyca/alpaca import confusion
- Virtual environment with uv

## [0.1.0] - 2025-07-30

Initial release.

- ASCOM Alpaca device control
- Discovery, telescope, camera tools
- Natural language ("Point at M31")
- Full test coverage
- GitHub Actions CI/CD
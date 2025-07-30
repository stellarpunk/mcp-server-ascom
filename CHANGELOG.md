# Changelog

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
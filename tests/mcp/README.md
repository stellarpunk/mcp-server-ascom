# MCP Protocol Tests

This directory contains tests that validate the MCP-to-ASCOM protocol translation.

## Test Organization

### test_ascom_endpoint_mapping.py
Validates that each MCP tool correctly maps to the corresponding ASCOM Alpaca HTTP endpoint:
- `telescope_connect` → `PUT /api/v1/telescope/{n}/connected`
- `telescope_goto` → `PUT /api/v1/telescope/{n}/slewtocoordinates`
- `telescope_get_position` → `GET /api/v1/telescope/{n}/rightascension` + `declination`
- etc.

### test_ascom_compliance.py
Ensures we follow ASCOM standards:
- Parameter naming (RightAscension not ra)
- Error response format
- Required ClientID/ClientTransactionID
- Coordinate validation rules

### test_telescope_patterns.py
Example patterns for AI to learn telescope control:
- Standard workflow: discover → connect → control → disconnect
- Error handling patterns
- Seestar-specific custom actions

### test_camera_patterns.py
Example patterns for AI to learn camera control:
- Imaging workflow: connect → check state → capture → download
- Temperature control for cooled cameras
- Multi-camera coordination

### test_resource_patterns.py
How to use MCP resources for monitoring:
- Server info and capabilities
- Connected device tracking
- Available device listing

### test_protocol.py
Core MCP protocol functionality:
- Tool registration
- Resource registration
- In-process client testing

## Key Concepts

1. **MCP Tools** are high-level operations that AI can call
2. **ASCOM Endpoints** are the HTTP APIs we call on devices like seestar_alp
3. Our tests verify the correct translation between these layers

## Running Tests

```bash
# Run all MCP tests
pytest tests/mcp/ -v

# Run specific test file
pytest tests/mcp/test_ascom_endpoint_mapping.py -v

# Run with coverage
pytest tests/mcp/ --cov=ascom_mcp.tools --cov=ascom_mcp.devices
```

## For AI Developers

These tests serve as documentation for how to properly use the MCP server:

1. Look at `test_telescope_patterns.py` for complete workflows
2. Check `test_ascom_compliance.py` to understand parameter formats
3. Use `test_ascom_endpoint_mapping.py` to see the exact HTTP calls made

The tests show the exact sequence and parameters needed for successful telescope/camera control.
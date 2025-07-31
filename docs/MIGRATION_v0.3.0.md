# Migration Guide: v0.2.x to v0.3.0

This guide helps you migrate from ASCOM MCP Server v0.2.x to v0.3.0, which introduces FastMCP from the official MCP SDK.

## Breaking Changes

### 1. Server Implementation Changed

The server has been completely rewritten using FastMCP:

**Before (v0.2.x):**
```python
from ascom_mcp.server import AscomMCPServer, create_server

server = AscomMCPServer()
```

**After (v0.3.0):**
```python
from ascom_mcp.server_fastmcp import mcp, create_server

# The 'mcp' object is the FastMCP instance
server = create_server()  # Returns the FastMCP instance
```

### 2. Tool Registration Pattern

FastMCP uses decorators instead of manual registration:

**Before (v0.2.x):**
```python
server.tools["discover_ascom_devices"] = discover_devices_tool
```

**After (v0.3.0):**
```python
@mcp.tool()
async def discover_ascom_devices(timeout: float = 5.0) -> dict[str, Any]:
    """Discover ASCOM devices on the network."""
    # Implementation
```

### 3. Device IDs Case Sensitivity

Device IDs now preserve the case from ASCOM discovery:

- `telescope_0` → `Telescope_0`
- `camera_0` → `Camera_0`

Update any hardcoded device IDs in your code.

## New Features

### 1. Structured Logging

v0.3.0 includes structured JSON logging to stderr:

```python
from ascom_mcp.logging import StructuredLogger

logger = StructuredLogger("my_module")
logger.info("device_connected", device_id="Telescope_0", status="ready")
```

Output:
```json
{
  "timestamp": "2025-01-30T20:00:00.000Z",
  "level": "info",
  "logger": "my_module",
  "event": "device_connected",
  "device_id": "Telescope_0",
  "status": "ready"
}
```

### 2. Cleaner Programmatic API

```python
from ascom_mcp.server_fastmcp import mcp

# List available tools
tools = await mcp.list_tools()

# Call a tool
content, result = await mcp.call_tool(
    "discover_ascom_devices",
    {"timeout": 5.0}
)
```

### 3. Improved Async Handling

The blocking `alpaca` discovery is now properly wrapped:

```python
# Internally uses asyncio.to_thread() to prevent blocking
devices = await discovery_tools.discover_devices(timeout=5.0)
```

## Installation

### For Users

No changes needed - install normally:

```bash
pip install mcp-server-ascom==0.3.0
# or
uvx mcp-server-ascom
```

### For Developers

The development dependencies remain the same:

```bash
pip install -e ".[dev]"
```

## Claude Desktop Configuration

No changes needed to your configuration. The server maintains the same interface:

```json
{
  "mcpServers": {
    "ascom": {
      "command": "uvx",
      "args": ["mcp-server-ascom"]
    }
  }
}
```

## Testing Your Migration

1. **Verify Installation:**
   ```bash
   mcp-server-ascom --version
   # Should show: mcp-server-ascom 0.3.0
   ```

2. **Test Discovery:**
   ```python
   from ascom_mcp.server_fastmcp import mcp
   
   content, result = await mcp.call_tool(
       "discover_ascom_devices",
       {"timeout": 5.0}
   )
   print(f"Found {result.get('count', 0)} devices")
   ```

3. **Check Device IDs:**
   Ensure your code handles the new capitalized device IDs.

## Deprecation Notices

- `ascom_mcp.server` module is deprecated and will be removed in v0.4.0
- Use `ascom_mcp.server_fastmcp` instead

## Need Help?

- Report issues: [GitHub Issues](https://github.com/your-org/mcp-server-ascom/issues)
- Documentation: [README.md](../README.md)
- Examples: [examples/fastmcp_example.py](../examples/fastmcp_example.py)
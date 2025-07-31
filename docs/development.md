# Development Guide

## Architecture

ASCOM MCP Server v0.3.0+ uses **FastMCP** from the official SDK:

- Decorator API: `@mcp.tool()`, `@mcp.resource()`
- Lifecycle management built-in
- Production defaults
- Half the boilerplate

## Key Design Decisions

### 1. FastMCP vs Low-Level API

Why FastMCP:

- 300 lines vs 600
- Built-in validation
- Recommended by MCP team
- Protocol compliance automatic

### 2. Structured Logging

MCP requires stderr logging. We use JSON:

```python
from ascom_mcp.logging import StructuredLogger

logger = StructuredLogger("ascom.telescope")
logger.info("telescope_connected", device_id="telescope_0", ra=5.5)
```

Works with OpenTelemetry, Grafana, DataDog.

### 3. Testing Strategy

Three levels:

1. **Unit**: Mock ASCOM devices
2. **Integration**: Test MCP protocol
3. **Smoke**: Verify Claude Desktop

## Common Pitfalls

1. **Never log to stdout** - Breaks protocol
2. **Use FastMCP** - Not low-level API
3. **Test stdio first** - Catches most issues
4. **Clear UV cache** - `uv cache clean`

## Running Tests

```bash
# All tests
pytest

# FastMCP specific
pytest tests/integration/test_fastmcp_server.py

# Quick smoke test
python test_v030.py
```

## Debugging

Claude Desktop logs:
```bash
tail -f ~/Library/Logs/Claude/mcp-server-ascom.log
```

Debug mode:
```bash
LOG_LEVEL=DEBUG mcp-server-ascom
```
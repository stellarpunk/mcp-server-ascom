# Release v0.3.0 - FastMCP 2.0 Migration

## 🚀 Major Changes

### FastMCP 2.0 Migration
Complete migration to FastMCP 2.0 with significant improvements:
- **50% less code** - Removed 500+ lines of boilerplate
- **Direct Context methods** - `await ctx.info()` instead of `ctx.logger.info()`
- **Built-in protocol compliance** - Automatic schema validation
- **Simplified testing** - New Client API for cleaner tests

### Testing Architecture
Streamlined to two-layer approach:
- **Unit tests** (`tests/unit/`) - Core logic with mocked devices
- **MCP tests** (`tests/mcp/`) - Protocol validation
- All 37 tests passing ✅

### Code Organization
- Moved examples to `examples/` directory
- Organized workflows and discovery patterns
- Cleaned up root directory

## 🔧 Technical Improvements

### Context Pattern
```python
# Before (FastMCP 1.x)
ctx.logger.info("message", extra={"key": "value"})

# After (FastMCP 2.0)  
await ctx.info("message", key="value")
```

### Error Handling
```python
raise ToolError(
    "Device not found",
    code="device_not_found",
    recoverable=True
)
```

### Simplified Testing
```python
async with Client(mcp) as client:
    result = await client.call_tool("discover_ascom_devices", {})
```

## 📝 Documentation Updates

- Updated all CLAUDE.md files with correct patterns
- Simplified testing documentation
- Added clear examples structure
- Fixed Context usage throughout

## 🐛 Bug Fixes

- Fixed deprecation warnings
- Corrected Context logging patterns
- Removed circular import issues
- Fixed test fixture patterns

## 💔 Breaking Changes

None - API remains compatible

## 🔜 Next Steps

1. Test with real Seestar hardware
2. Add more device type examples
3. Enhance custom action documentation

## Installation

```bash
pip install mcp-server-ascom==0.3.0
```

Or with uvx:
```bash
uvx mcp-server-ascom
```

## Contributors

Thanks to all contributors who helped with this release!
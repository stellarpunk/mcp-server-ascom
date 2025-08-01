# CLAUDE.md - ASCOM MCP Server

Bridge ASCOM devices to Claude via MCP (Model Context Protocol).

## Quick Start

```bash
# Activate venv
source .venv/bin/activate

# Run server
python -m ascom_mcp

# Run tests
pytest tests/unit/ -v    # Unit tests (37/37 ✅)
pytest tests/mcp/ -v     # MCP protocol tests
```

## Architecture

Our server is a "USB cable" between MCP and ASCOM:

```
Claude → MCP Protocol → Our Server → HTTP/Alpaca → seestar_alp → Telescope
         (FastMCP 2.0)    (Translation)   (ASCOM)     (Community)   (Hardware)
```

## FastMCP 2.0 Patterns

### 1. Context Parameter (Required)
```python
@mcp.tool()
async def telescope_goto(ctx: Context, device_id: str, ra: float, dec: float):
    await ctx.info(f"Slewing to RA={ra}, Dec={dec}")  # Direct logging
    # NOT ctx.logger.info() - that's wrong!
```

### 2. ToolError for User-Friendly Errors
```python
raise ToolError(
    "Device not found. Run discovery first.",
    code="device_not_found",
    recoverable=True,
    details={"suggestions": ["Try: discover_ascom_devices"]}
)
```

### 3. Structured Logging
```python
await ctx.debug("tool_called: telescope_goto")
await ctx.info(f"connected: device_id={device_id}")
await ctx.error(f"failed: {str(e)}")
```

## Key Commands

### Discovery & Connection
```python
# Discover devices
discover_ascom_devices(timeout=5.0)

# Connect (use device_id from discovery)
telescope_connect(device_id="Telescope_0")

# Initialize telescope (CRITICAL for Seestar!)
telescope_custom_action(
    device_id="Telescope_0",
    action="action_start_up_sequence",
    parameters={"lat": 40.745, "lon": -74.0256, "move_arm": True}
)
```

### Basic Operations
```python
# Go to coordinates
telescope_goto(device_id="Telescope_0", ra=5.5, dec=-5.0)

# Go to object
telescope_goto_object(device_id="Telescope_0", object_name="M31")

# Get position
telescope_get_position(device_id="Telescope_0")

# Park telescope
telescope_park(device_id="Telescope_0")
```

### Seestar-Specific
```python
# Movement (counterintuitive!)
# North/South = horizontal pan, East/West = vertical tilt
telescope_custom_action(
    device_id="Telescope_0",
    action="method_sync",
    parameters={
        "method": "scope_speed_move",
        "params": {"speed": 400, "angle": 180, "dur_sec": 3}  # South = pan north
    }
)

# View modes
telescope_custom_action(
    device_id="Telescope_0", 
    action="method_sync",
    parameters={
        "method": "iscope_start_view",
        "params": {"mode": "scenery"}  # or "star", "moon", "sun"
    }
)
```

## Environment Variables

```bash
# Skip discovery with known devices
export ASCOM_KNOWN_DEVICES="localhost:5555:seestar_alp"

# Use simulator
export ASCOM_SIMULATOR_DEVICES="localhost:4700:seestar_simulator"

# Debug logging
export LOG_LEVEL=DEBUG

# Discovery timeout
export ASCOM_DISCOVERY_TIMEOUT=10
```

## Testing

### Test Structure
```
tests/
├── unit/     # Core logic (37 tests, all pass)
├── mcp/      # Protocol validation
│   ├── test_protocol.py              # Basic MCP tests
│   ├── test_ascom_endpoint_mapping.py # HTTP mapping
│   ├── test_ascom_compliance.py       # ASCOM standards
│   └── test_*_patterns.py            # Usage examples
```

### Running Tests
```bash
# Fast unit tests
pytest tests/unit/ -v

# MCP protocol tests  
pytest tests/mcp/ -v

# With coverage
pytest --cov=ascom_mcp
```

## Common Issues

### "Device not found"
- Run `discover_ascom_devices` first
- Check seestar_alp is running: `cd ../seestar_alp && python root_app.py`
- Verify ports: Backend API on 5555

### Tests hanging
- MCP tests use mocked discovery - no network calls
- If hanging, check for unmocked network operations

### Context errors
- All tools need Context as first parameter
- Use `await ctx.info()` not `ctx.logger.info()`

## Safety Notes

1. **Always initialize Seestar** with `action_start_up_sequence` after connecting
2. **Solar observation** requires explicit mode change and safety protocols
3. **Park before disconnect** to protect equipment

## Development Workflow

```bash
# 1. Make changes
vim src/ascom_mcp/server_fastmcp.py

# 2. Run tests
pytest tests/unit/ -v        # Fast feedback
pytest tests/mcp/ -v         # Protocol validation

# 3. Test with simulator
export ASCOM_SIMULATOR_DEVICES="localhost:4700:seestar_simulator"
python -m ascom_mcp

# 4. Test with real device
cd ../seestar_alp && python root_app.py  # Terminal 1
python -m ascom_mcp                      # Terminal 2
```

## Release Process

```bash
# Update version
python scripts/release.py --version X.Y.Z

# Build and publish
python -m build
twine upload dist/*
```

## Key Files

- `src/ascom_mcp/server_fastmcp.py` - Main server with all tools
- `src/ascom_mcp/tools/` - Tool implementations
- `src/ascom_mcp/devices/` - Device management
- `tests/conftest.py` - Shared test fixtures
- `.multitailrc` - Log monitoring config

## Documentation

- `README.md` - User guide
- `docs/development.md` - Developer guide
- `docs/PRODUCTION_DEPLOYMENT.md` - Deployment guide
- `tests/README.md` - Testing guide
- `tests/mcp/README.md` - MCP patterns for AI
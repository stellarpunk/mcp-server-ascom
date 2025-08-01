# ASCOM MCP Server Testing Guide

## Overview

This directory contains comprehensive tests for the ASCOM MCP server using FastMCP 2.0 patterns. We follow a simplified two-layer testing architecture that validates both the implementation logic and the MCP protocol translation.

## Testing Philosophy

Our MCP server acts as a "USB cable" between MCP clients (like Claude) and ASCOM Alpaca devices:

```
Claude/Client → MCP Protocol → Our Server → HTTP/Alpaca → seestar_alp → Telescope
```

Tests validate both ends of this translation layer.

## Test Structure

```
tests/
├── unit/                    # Core logic testing
│   ├── test_discovery_tools.py
│   ├── test_telescope_tools.py
│   ├── test_camera_tools.py
│   ├── test_device_manager.py
│   └── test_simulator_discovery.py
├── mcp/                     # MCP protocol validation
│   ├── test_protocol.py     # Basic protocol tests
│   ├── test_ascom_endpoint_mapping.py  # HTTP endpoint validation
│   ├── test_ascom_compliance.py        # ASCOM standard compliance
│   ├── test_telescope_patterns.py      # Telescope workflow examples
│   ├── test_camera_patterns.py         # Camera workflow examples
│   ├── test_resource_patterns.py       # Resource access patterns
│   └── README.md           # MCP testing documentation
├── conftest.py             # Shared fixtures
├── base.py                 # Base test classes
└── utils.py                # Test utilities
```

## Running Tests

### Quick Start
```bash
# Run all unit tests (fast, no external dependencies)
pytest tests/unit/ -v

# Run MCP protocol tests
pytest tests/mcp/ -v

# Run specific test file
pytest tests/unit/test_telescope_tools.py -v

# Run with coverage
pytest --cov=ascom_mcp --cov-report=html
```

### Test Categories

#### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test core business logic
- **Dependencies**: None (all mocked)
- **Speed**: Very fast (<2 seconds)
- **Example**: Verify coordinate validation, error handling

```python
async def test_goto_invalid_ra():
    tools = TelescopeTools(mock_manager)
    result = await tools.goto("telescope_1", ra=25.0, dec=0.0)  # RA > 24
    assert result["success"] is False
```

#### 2. MCP Tests (`tests/mcp/`)
- **Purpose**: Validate MCP protocol implementation
- **Dependencies**: In-process FastMCP server
- **Speed**: Fast (<10 seconds)
- **Example**: Verify tool registration, parameter handling

```python
async def test_telescope_goto_endpoint():
    async with Client(mcp) as client:
        result = await client.call_tool("telescope_goto", {
            "device_id": "Telescope_1",
            "ra": 5.5,
            "dec": -5.0
        })
        # Verify the tool works through MCP protocol
```

## Key Testing Patterns

### 1. FastMCP 2.0 Context
All tools receive a Context as first parameter:

```python
@mcp.tool()
async def telescope_goto(ctx: Context, device_id: str, ra: float, dec: float):
    await ctx.info(f"Slewing to RA={ra}, Dec={dec}")
    # ... implementation
```

### 2. Mock Fixtures
Common fixtures in `conftest.py`:

```python
@pytest.fixture
def mock_telescope():
    """Mock ASCOM telescope with standard properties."""
    telescope = MagicMock()
    telescope.CanSlew = True
    telescope.Slewing = False
    telescope.RightAscension = 0.0
    telescope.Declination = 0.0
    return telescope

@pytest.fixture  
def mock_device_discovery():
    """Mock device discovery to avoid network operations."""
    # Returns pre-configured test devices
```

### 3. Testing MCP Tools
MCP tests use the FastMCP Client API:

```python
async with Client(mcp) as client:
    # List tools/resources
    tools = await client.list_tools()
    resources = await client.list_resources()
    
    # Call tools
    result = await client.call_tool("discover_ascom_devices", {"timeout": 5.0})
    
    # Read resources
    info = await client.read_resource("ascom://server/info")
```

### 4. Error Testing
Validate proper error handling with ToolError:

```python
# ToolError provides helpful context
raise ToolError(
    "Device not found",
    code="device_not_found",
    recoverable=True,
    details={"suggestions": ["Run discovery first"]}
)
```

## Environment Variables

```bash
# v0.4.0 Direct device configuration (no discovery needed!)
export ASCOM_DIRECT_DEVICES="telescope_1:seestar.local:5555:Seestar S50"

# Known devices (skip discovery)
export ASCOM_KNOWN_DEVICES="localhost:5555:seestar_alp"

# Simulator devices
export ASCOM_SIMULATOR_DEVICES="localhost:4700:seestar_simulator"

# Debug logging
export LOG_LEVEL=DEBUG

# Discovery timeout (only when discovery is used)
export ASCOM_DISCOVERY_TIMEOUT=10
```

## Common Issues and Solutions

### Import Errors
- Ensure virtual environment is activated
- Install package in editable mode: `pip install -e .`

### Async Test Issues  
- All async tests need `@pytest.mark.asyncio`
- Use `AsyncMock` for async methods, not `MagicMock`

### Hanging Tests
- Tests should mock network operations
- Use the `mock_device_discovery` fixture
- Set short timeouts in test calls

### FastMCP Client API
- `list_tools()` returns Tool objects with `.name` attribute
- `list_resources()` returns Resource objects with `.uri` attribute  
- `call_tool()` returns result with `.content[0].text` for JSON

## Best Practices

1. **Test Independence**: Each test should be self-contained
2. **Clear Names**: `test_telescope_goto_invalid_coordinates` not `test_goto_fail`
3. **Mock at Boundaries**: Mock external dependencies, not internal logic
4. **Fast Tests**: Unit tests should complete in milliseconds
5. **Helpful Errors**: Test error messages and recovery suggestions

## Integration with Real Devices

For testing with actual seestar_alp:

```bash
# Terminal 1: Start seestar_alp
cd ../seestar_alp
python root_app.py

# Terminal 2: Run integration tests
export ASCOM_KNOWN_DEVICES="localhost:5555:seestar_alp"
pytest tests/mcp/test_telescope_patterns.py -v
```

## Contributing

When adding tests:
1. Choose appropriate layer (unit vs mcp)
2. Use existing fixtures and patterns
3. Document complex test scenarios
4. Ensure tests are deterministic
5. Update this README for new patterns
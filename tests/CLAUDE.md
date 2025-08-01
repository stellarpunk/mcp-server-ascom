# Test Suite Context

## Testing Architecture

Two-layer testing approach:
- **Unit tests** (tests/unit/): Core business logic, mocked devices
- **MCP tests** (tests/mcp/): Protocol validation and usage patterns

## Test Structure
```
tests/
├── unit/                    # Core logic tests (37 tests, all pass)
│   ├── test_discovery_tools.py
│   ├── test_telescope_tools.py
│   ├── test_camera_tools.py
│   ├── test_device_manager.py
│   └── test_simulator_discovery.py
├── mcp/                     # MCP protocol tests
│   ├── test_protocol.py              # Tool/resource registration
│   ├── test_ascom_endpoint_mapping.py # HTTP endpoint validation
│   ├── test_ascom_compliance.py       # ASCOM standard compliance
│   ├── test_telescope_patterns.py     # Telescope usage examples
│   ├── test_camera_patterns.py        # Camera usage examples
│   └── test_resource_patterns.py      # Resource access patterns
├── conftest.py             # Shared fixtures
├── base.py                 # Base test classes
└── utils.py                # Test utilities
```

## Key Fixtures

### `mock_context` - FastMCP Context
```python
@pytest.fixture
def mock_context():
    ctx = MagicMock(spec=Context)
    # NO ctx.logger - use direct methods!
    return ctx
```

### `mock_telescope` - ASCOM Device
```python
@pytest.fixture
def mock_telescope():
    telescope = MagicMock()
    # Properties are sync
    telescope.Connected = True
    telescope.CanSlew = True
    telescope.Slewing = False
    # Methods are async
    telescope.SlewToCoordinatesAsync = AsyncMock()
    return telescope
```

### `mock_device_discovery` - Skip network calls
```python
@pytest.fixture
def mock_device_discovery():
    """Mock discovery to avoid network operations."""
    # Returns pre-configured test devices
```

## Test Patterns

### FastMCP 2.0 Context
```python
# ✅ CORRECT - Direct Context methods
async def test_with_context(ctx: Context):
    await ctx.info("Starting operation")
    await ctx.debug(f"Details: {data}")
    await ctx.error(f"Failed: {error}")

# ❌ WRONG - No ctx.logger!
ctx.logger.info("This is wrong")
```

### ToolError Pattern
```python
raise ToolError(
    "Device not found. Run discovery first.",
    code="device_not_found", 
    recoverable=True,
    details={"suggestions": ["Try: discover_ascom_devices"]}
)
```

### Testing Layers
```python
# Unit test - tool functions directly
async def test_discovery_logic():
    tools = DiscoveryTools(mock_manager)
    result = await tools.discover_devices()
    assert result["success"] is True

# MCP test - through FastMCP Client
async def test_discovery_through_mcp():
    async with Client(mcp) as client:
        result = await client.call_tool("discover_ascom_devices", {"timeout": 5.0})
        data = json.loads(result.content[0].text)
        assert data["success"] is True
```

## Running Tests

```bash
# Activate venv first!
source .venv/bin/activate

# Unit tests (37/37 passing ✅)
pytest tests/unit/ -v

# MCP protocol tests
pytest tests/mcp/ -v

# All tests
pytest tests/ -v

# With coverage
pytest --cov=ascom_mcp --cov-report=html

# Specific test
pytest tests/unit/test_telescope_tools.py::TestTelescopeTools::test_goto_valid_coordinates -v
```

## Test Status
- Unit tests: 37/37 passing ✅
- MCP tests: Fixed for FastMCP Client API ✅
- Mocking: No network calls in tests ✅
- Fixtures: Updated for FastMCP 2.0 ✅

## Common Issues

### Import Errors
- Alpaca/alpyca are mocked via test_setup.py
- Activate venv: `source .venv/bin/activate`

### Hanging Tests  
- Use `mock_device_discovery` fixture
- Avoid real network operations
- Set short timeouts

### FastMCP Client API
- `list_tools()` returns Tool objects with `.name`
- `call_tool()` result has `.content[0].text`
- Resources have `.uri` attribute (AnyUrl type)
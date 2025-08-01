# Test Suite Context

## Testing Architecture (v0.4.0)

Three-layer testing approach:
- **Unit tests** (tests/unit/): Core business logic, mocked devices
- **Integration tests** (tests/integration/): Real simulators, IoT patterns (NEW!)
- **MCP tests** (tests/mcp/): Protocol validation and usage patterns

## Test Structure
```
tests/
├── unit/                    # Core logic tests (40+ tests, all pass)
│   ├── test_discovery_tools.py
│   ├── test_telescope_tools.py
│   ├── test_camera_tools.py
│   ├── test_device_manager.py
│   ├── test_device_resolver.py      # Device ID parsing (NEW!)
│   └── test_simulator_discovery.py
├── integration/             # Real simulator tests (NEW!)
│   ├── test_discovery_timeout.py    # Discovery performance
│   ├── test_iot_connection_pattern.py # Direct connections
│   ├── test_event_stream.py        # Event streaming (v0.4.0+)
│   ├── test_mcp_integration.py     # Full MCP workflow
│   └── test_observation_workflow.py # Complete sessions
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
    # Methods are SYNC in alpyca (despite "Async" name!)
    telescope.SlewToCoordinatesAsync = MagicMock()  # NOT AsyncMock!
    telescope.Park = MagicMock()
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

# Unit tests (40+ tests passing ✅)
pytest tests/unit/ -v

# Integration tests with simulator (NEW!)
pytest tests/integration/ -v

# MCP protocol tests
pytest tests/mcp/ -v

# All tests
pytest tests/ -v

# With coverage
pytest --cov=ascom_mcp --cov-report=html

# Specific test
pytest tests/unit/test_telescope_tools.py::TestTelescopeTools::test_goto_valid_coordinates -v
```

## Test Status (v0.4.0)
- Unit tests: 40+ tests passing ✅
- Integration tests: IoT patterns validated ✅
- MCP tests: Fixed for FastMCP Client API ✅
- Mocking: Alpyca methods are SYNC not async ✅
- Fixtures: Updated for FastMCP 2.0 ✅

## Integration Test Features
- No automatic discovery requirement
- Direct connection strings work
- Device state persistence tested
- Event stream handling (v0.4.0+):
  - Event types enumeration
  - Event history with filtering
  - Event stream resource templates
  - Clear event history
- Complete observation workflows

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
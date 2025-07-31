# Test Suite Context

## Testing Strategy
- **Unit tests** (90%): Business logic, mocked devices
- **Integration tests** (9%): FastMCP patterns, Context/ToolError
- **E2E tests** (1%): Real workflows, simulator/hardware

## Test Structure
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_discovery_tools.py
│   ├── test_telescope_tools.py
│   ├── test_camera_tools.py
│   ├── test_device_manager.py
│   └── test_simulator_discovery.py
├── integration/             # MCP protocol tests
│   ├── test_fastmcp_context.py
│   ├── test_tool_integration.py
│   └── test_mcp_full_flow.py
├── e2e/                     # Full system tests
│   └── test_simulator_integration.py
├── test_setup.py           # Alpaca/alpyca mocks
└── conftest.py             # Shared fixtures
```

## Key Fixtures

### `mock_context` - FastMCP Context
```python
@pytest.fixture
def mock_context():
    ctx = MagicMock(spec=Context)
    ctx.logger = structlog.get_logger()
    ctx.request_id = str(uuid.uuid4())
    return ctx
```

### `mock_telescope` - ASCOM Device
```python
@pytest.fixture
def mock_telescope():
    telescope = MagicMock()
    # Properties are sync
    telescope.Connected = True
    telescope.RightAscension = 5.5
    # Methods are async
    telescope.SlewToCoordinatesAsync = AsyncMock()
    return telescope
```

### `device_manager_with_simulator`
```python
@pytest.fixture
async def device_manager_with_simulator():
    os.environ["ASCOM_SIMULATOR_DEVICES"] = "localhost:4700:seestar_simulator"
    manager = DeviceManager()
    await manager.initialize()
    return manager
```

## Test Patterns

### FastMCP Tool Testing
```python
# Unit test - underlying function
async def test_discovery_logic(discovery_tools):
    result = await discovery_tools.discover_devices()
    assert result["success"] is True

# Integration test - with Context
async def test_discovery_with_context(mock_context):
    result = await discover_ascom_devices(mock_context, timeout=5.0)
    mock_context.logger.info.assert_called()
```

### ToolError Pattern
```python
async def test_connection_error(mock_context):
    with pytest.raises(ToolError) as exc_info:
        await telescope_connect(mock_context, "invalid_device")
    
    assert exc_info.value.code == "connection_failed"
    assert exc_info.value.recoverable is True
```

### Simulator Testing
```python
async def test_simulator_discovery(simulator_environment):
    config = Config()
    assert any("simulator" in name for _, _, name in config.simulator_devices)
```

## Running Tests

**Activate venv first!**

```bash
source .venv/bin/activate

# All unit tests (37/37 passing)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With simulator
export ASCOM_SIMULATOR_DEVICES="localhost:4700:seestar_simulator"
pytest tests/e2e/ -v

# Coverage report
pytest --cov=ascom_mcp --cov-report=html
```

## Test Status
- Unit tests: 37/37 passing ✅
- Integration tests: FastMCP 2.0 patterns ✅
- E2E tests: Simulator support ✅
- Alpaca mocking: test_setup.py ✅
- Environment detection: Auto-simulator ✅
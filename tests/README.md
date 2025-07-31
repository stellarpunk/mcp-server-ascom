# ASCOM MCP Server Testing Guide

## Overview

This directory contains comprehensive tests for the ASCOM MCP server using FastMCP 2.0 patterns. The tests are organized in three layers following the testing pyramid principle.

## Prerequisites

```bash
# Create virtual environment with uv
uv venv

# Activate environment
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Install Playwright browsers (for E2E tests)
playwright install chromium
```

## Test Structure

```
tests/
├── unit/                    # Fast, isolated tests of core logic
│   ├── test_discovery_tools.py
│   ├── test_telescope_tools.py
│   ├── test_camera_tools.py
│   └── test_device_manager.py
├── integration/             # Tests with mocked external dependencies
│   ├── test_fastmcp_context.py
│   ├── test_tool_integration.py
│   └── test_mcp_full_flow.py
├── e2e/                     # End-to-end tests with real services
│   ├── test_simulator_integration.py
│   └── test_seestar_workflow.py
├── fixtures/                # Shared test fixtures and factories
├── conftest.py             # Pytest configuration and fixtures
└── README.md               # This file
```

## Testing Layers

### 1. Unit Tests
Test the core business logic without MCP protocol overhead:
- Direct testing of service classes (DiscoveryTools, TelescopeTools, etc.)
- Fast execution with mocked dependencies
- Focus on algorithmic correctness

**Example:**
```python
# Test core discovery logic
async def test_discover_devices_success(discovery_tools, mock_device_manager):
    result = await discovery_tools.discover_devices(timeout=3.0)
    assert result["success"] is True
```

### 2. Integration Tests
Test the MCP protocol layer and tool decorators:
- FastMCP Context injection
- ToolError exception handling
- Protocol message formatting

**Example:**
```python
# Test MCP tool with Context
async def test_telescope_connect_with_context(mock_context):
    result = await telescope_connect(mock_context, "Telescope_1")
    mock_context.logger.info.assert_called_with("connecting_telescope", device_id="Telescope_1")
```

### 3. End-to-End Tests
Test complete workflows with real services:
- Full MCP client → server → ASCOM device flow
- Requires seestar_alp simulator running
- Validates real-world scenarios

**Example:**
```python
# Test complete discovery → connect → control flow
async def test_full_telescope_workflow(mcp_client, running_services):
    devices = await mcp_client.call_tool("discover_ascom_devices", {"timeout": 5.0})
    # ... complete workflow
```

## Running Tests

### Quick Start
```bash
# Run all unit tests (fast)
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/unit/test_discovery_tools.py::TestDiscoveryTools::test_discover_devices_success -v
```

### With Services
```bash
# Start seestar_alp simulator first
cd ../seestar_alp && python simulator/src/main.py &

# Run integration tests that need services
pytest tests/integration/test_tool_integration.py -v
```

### Full Test Suite
```bash
# Run all tests with coverage
pytest --cov=ascom_mcp --cov-report=html

# Run with markers
pytest -m "not requires_simulator"  # Skip tests needing simulator
pytest -m "smoke"                    # Run only smoke tests
```

## Key Testing Patterns

### 1. Testing Decorated Functions
FastMCP decorates functions with `@mcp.tool()`. Test both the underlying function and the decorated version:

```python
# Unit test - underlying function
async def test_discovery_logic():
    tools = DiscoveryTools(mock_manager)
    result = await tools.discover_devices()

# Integration test - decorated function  
async def test_discovery_through_mcp():
    result = await discover_ascom_devices(mock_context, timeout=5.0)
```

### 2. Context and Logging
All tools receive a FastMCP Context as the first parameter:

```python
@pytest.fixture
def mock_context():
    ctx = MagicMock(spec=Context)
    ctx.logger = structlog.get_logger()
    return ctx
```

### 3. Error Handling
Use ToolError for recoverable errors with helpful suggestions:

```python
with pytest.raises(ToolError) as exc_info:
    await telescope_connect(mock_context, "invalid_device")

assert exc_info.value.code == "connection_failed"
assert exc_info.value.recoverable is True
```

### 4. Service Coordination
For E2E tests, use fixtures to manage service lifecycle:

```python
@pytest.fixture
async def running_services():
    # Start simulator and seestar_alp
    # Yield control
    # Cleanup on teardown
```

## Common Fixtures

See `conftest.py` for shared fixtures:
- `mock_context` - FastMCP Context mock
- `mock_device_manager` - Device manager with test devices
- `mock_telescope` - ASCOM telescope mock
- `mock_camera` - ASCOM camera mock
- `mcp_server` - Configured MCP server instance

## Best Practices

1. **Test Naming**: Use descriptive names that explain the scenario
   - ✅ `test_discover_devices_with_network_timeout`
   - ❌ `test_discovery_fail`

2. **Assertions**: Be specific about what you're testing
   - ✅ `assert result["devices"][0]["type"] == "Telescope"`
   - ❌ `assert result`

3. **Mocking**: Mock at the appropriate boundary
   - Unit tests: Mock external dependencies
   - Integration tests: Mock network/hardware
   - E2E tests: Use real services when possible

4. **Async Testing**: Use `pytest.mark.asyncio` and proper async fixtures

5. **Test Data**: Use fixtures and factories for consistent test data

## Troubleshooting

### Import Errors
- Ensure you're in the project root or have installed the package
- Check PYTHONPATH includes the src directory
- ModuleNotFoundError: Wrong Python environment active

### Async Warnings  
- Use `pytest-asyncio` for async test support
- Ensure event loop handling in fixtures
- Use AsyncMock for async methods, not MagicMock

### Service Connection Errors
- Verify seestar_alp is running on expected ports
- Check firewall/network settings
- Use `ASCOM_SIMULATOR_DEVICES` environment variable
- Increase ASCOM_DISCOVERY_TIMEOUT if needed

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG pytest tests -v -s

# Run single test with output
pytest tests/unit/test_telescope_tools.py::TestTelescopeTools::test_connect_success -v -s
```

### Known Issues
- datetime.utcnow() deprecation warnings
- Some integration tests require seestar_alp running

## MCP Testing

### Testing with Claude Desktop

1. Configure Claude Desktop:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "python",
      "args": ["-m", "ascom_mcp"],
      "cwd": "/path/to/mcp-server-ascom",
      "env": {
        "PYTHONPATH": "/path/to/mcp-server-ascom/src",
        "ASCOM_KNOWN_DEVICES": "localhost:5555:seestar_alp"
      }
    }
  }
}
```

2. Test MCP tools in Claude:
```
/mcp ascom discover_devices timeout=5.0
/mcp ascom telescope_connect device_id="Telescope_1"
```

### Manual MCP Testing

```bash
# Start MCP server
python -m ascom_mcp

# In another terminal, send MCP commands
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m ascom_mcp
```

## Environment Variables

```bash
# For testing with known devices
export ASCOM_KNOWN_DEVICES="localhost:5555:seestar_alp"

# For simulator devices
export ASCOM_SIMULATOR_DEVICES="localhost:4700:seestar_simulator"

# For debug logging
export LOG_LEVEL=DEBUG

# For discovery timeout
export ASCOM_DISCOVERY_TIMEOUT=5
```

## Continuous Integration

GitHub Actions workflow runs tests automatically:
- Unit tests on Python 3.10, 3.11, 3.12
- Integration tests with mock devices  
- Code coverage reporting
- Pre-release validation on Test PyPI

## Contributing

When adding new tests:
1. Choose the appropriate test layer (unit/integration/e2e)
2. Follow existing patterns for consistency
3. Add docstrings explaining the test scenario
4. Update this README if adding new patterns
5. Ensure tests are deterministic and independent
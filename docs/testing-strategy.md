# Testing Strategy for ASCOM MCP Server

## Overview

Our testing strategy focuses on catching integration issues that affect Claude Desktop users, while maintaining a minimal and efficient test suite.

## Test Categories

### 1. Critical Integration Tests (`tests/integration/`)

These tests catch the specific issues that broke our releases:

- **test_claude_desktop_integration.py**: Tests actual stdio protocol communication
- **test_mcp_server_startup.py**: Catches coroutine and API parameter issues  
- **test_cli_entry.py**: Ensures CLI entry points work correctly

### 2. Device-Specific Tests (`tests/unit/`)

Using the extensible base classes in `tests/base.py`:

- **test_telescope_tools.py**: Telescope-specific operations
- **test_camera_tools.py**: Camera-specific operations
- Add new devices by subclassing `BaseDeviceTest` and `BaseToolTest`

### 3. Protocol Tests (`tests/integration/test_mcp_protocol.py`)

Tests MCP protocol compliance and version negotiation.

## Adding Tests for New Devices

### 1. Create a new test file

```python
# tests/unit/test_focuser_tools.py
from tests.base import BaseDeviceTest, BaseToolTest
from ascom_mcp.tools.focuser import FocuserTools

class TestFocuserDevice(BaseDeviceTest):
    @property
    def device_type(self):
        return "Focuser"
    
    @property
    def required_properties(self):
        return ["Position", "MaxStep", "StepSize", "TempComp"]

class TestFocuserTools(BaseToolTest):
    @property
    def tool_class(self):
        return FocuserTools
    
    @property 
    def device_type(self):
        return "Focuser"
```

### 2. Add mock device to conftest.py

```python
@pytest.fixture
def mock_focuser():
    """Mock ASCOM focuser device."""
    focuser = MagicMock()
    focuser.Connected = False
    focuser.Position = 5000
    focuser.MaxStep = 10000
    # ... add other properties
    return focuser
```

## CI/CD Pipeline

Our GitHub Actions workflow ensures quality:

1. **Every PR**: Runs critical tests first, then full test matrix
2. **Tags (releases)**: 
   - Tests on all platforms
   - Publishes to Test PyPI first
   - Verifies installation works
   - Then publishes to production PyPI
   - Creates GitHub release

## Running Tests Locally

```bash
# Run all tests
pytest

# Run critical tests only
pytest tests/integration/test_mcp_server_startup.py tests/integration/test_claude_desktop_integration.py

# Run with coverage
pytest --cov=ascom_mcp --cov-report=html

# Run pre-release checks
./scripts/test_before_release.sh
```

## Test Philosophy

- **Test what broke**: Focus on actual integration points that failed
- **Minimal but comprehensive**: Few tests that catch real issues
- **Fast feedback**: Critical tests run in <30 seconds
- **Real tools**: Use mcp-inspector and uvx in tests, not just mocks
- **Extensible**: Easy to add new device types

## Known Issues to Test For

1. **Coroutine entry point** (v0.2.1): `RuntimeWarning: coroutine 'main' was never awaited`
2. **API parameter changes** (v0.2.2-3): MCP SDK parameter updates
3. **Protocol negotiation**: Supporting both 2024-11-05 and 2025-06-18
4. **Installation methods**: pip, uvx, and direct execution
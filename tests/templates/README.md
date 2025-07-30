# Test Templates for Adding New Device Support

This directory contains templates to help contributors add support for new ASCOM device types.

## Quick Start

1. Copy the template for your device type (or use `device_template.py` for custom devices)
2. Replace `{DeviceType}` with your device name (e.g., `Focuser`, `Dome`)
3. Update the capabilities and test cases
4. Move to appropriate test directory when complete

## Templates

- `device_template.py` - Generic template for any device type
- `focuser_example.py` - Complete example for focuser implementation
- `integration_template.py` - Template for integration tests

## Step-by-Step Guide

### 1. Create Device Fixture

Add to `tests/conftest.py`:
```python
@pytest.fixture
def mock_focuser():
    """Mock ASCOM focuser device."""
    return create_focuser_mock()
```

### 2. Create Unit Tests

Create `tests/unit/tools/test_focuser.py`:
```python
from tests.base import BaseToolTest
from ascom_mcp.tools.focuser import FocuserTools

class TestFocuserTools(BaseToolTest):
    tool_class = FocuserTools
    device_type = "Focuser"
    
    # Add device-specific tests here
```

### 3. Update Integration Tests

Add test scenario to `tests/integration/test_device_scenarios.py`

### 4. Run Tests

```bash
pytest tests/unit/tools/test_focuser.py -v
```

## Best Practices

1. **Use Base Classes**: Inherit from `BaseDeviceTest` or `BaseToolTest`
2. **Test Behavior, Not Implementation**: Focus on what the tool does, not how
3. **Mock External Dependencies**: Use fixtures from `tests/fixtures/`
4. **Test Error Cases**: Include tests for invalid inputs and error conditions
5. **Keep Tests Fast**: Mock network calls and hardware interactions

## Example Test Structure

```python
class TestNewDevice(BaseToolTest):
    """Tests for new device type."""
    
    tool_class = NewDeviceTools
    device_type = "NewDevice"
    
    # Test successful operations
    async def test_specific_operation_success(self):
        """Test device-specific successful operation."""
        pass
    
    # Test error handling
    async def test_handles_device_error(self):
        """Test proper error handling."""
        pass
    
    # Test edge cases
    async def test_edge_case_behavior(self):
        """Test behavior at limits."""
        pass
```
# ASCOM MCP Testing Strategy

## Overview

Our testing strategy focuses on catching real integration issues while supporting both simulator-based testing for daily development and real hardware testing for validation.

## Testing Philosophy

- **Test what broke**: Focus on actual integration points that failed
- **Minimal but comprehensive**: Few tests that catch real issues  
- **Fast feedback**: Critical tests run in <30 seconds
- **Real tools**: Use mcp-inspector and uvx, not just mocks
- **Extensible**: Easy to add new device types

Following industry best practices:

- **90% Simulator Testing**: Fast, reliable, reproducible tests for CI/CD
- **10% Real Hardware Testing**: Critical validation and edge cases

## Environment Detection

The test suite automatically detects the testing environment:

```python
# Environment variables control test behavior
export ASCOM_TEST_MODE=simulator     # Use simulator (default)
export ASCOM_TEST_MODE=hardware      # Use real hardware
export ASCOM_TEST_MODE=auto          # Auto-detect available devices

# Specific device configuration
export ASCOM_SIMULATOR_DEVICES="localhost:4700:seestar_simulator"
export ASCOM_KNOWN_DEVICES="localhost:5555:seestar_alp"
```

## Test Categories

### 1. Unit Tests (Always Mocked)
```bash
pytest tests/unit/ -v
```
- Pure business logic testing
- No external dependencies
- Run on every commit
- Uses `test_setup.py` for alpaca/alpyca mocking

### 2. Integration Tests (Simulator by Default)
```bash
pytest tests/integration/ -v
```
- Tests MCP protocol integration
- FastMCP 2.0 patterns (Context, ToolError)
- Can run against simulator or real hardware
- Default: simulator mode

### 3. E2E Tests (Configurable)
```bash
# Simulator mode (default)
pytest tests/e2e/ -v

# Real hardware mode
ASCOM_TEST_MODE=hardware pytest tests/e2e/ -v

# Specific hardware test
pytest tests/e2e/test_real_hardware.py -v -m hardware_only
```

## Test Markers

```python
@pytest.mark.requires_simulator    # Test requires simulator running
@pytest.mark.requires_seestar      # Test requires seestar_alp running  
@pytest.mark.hardware_only         # Test only runs with real hardware
@pytest.mark.simulator_only        # Test only runs with simulator
@pytest.mark.slow                  # Test takes >5 seconds
```

## Hardware Test Fixtures

```python
@pytest.fixture
def hardware_config():
    """Configuration for real hardware tests."""
    if os.getenv("ASCOM_TEST_MODE") != "hardware":
        pytest.skip("Hardware tests disabled")
    
    return {
        "telescope_ip": os.getenv("SEESTAR_IP", "192.168.1.100"),
        "telescope_port": int(os.getenv("SEESTAR_PORT", "5555")),
        "safety_checks": True,  # Prevent dangerous movements
        "max_slew_time": 10,    # Limit slew operations
    }

@pytest.fixture
async def real_telescope(hardware_config):
    """Connect to real telescope with safety checks."""
    manager = DeviceManager()
    await manager.initialize()
    
    # Discover real devices
    devices = await manager.discover_devices(timeout=10.0)
    
    # Find non-simulator telescope
    for device in devices:
        if device.type == "Telescope" and not hasattr(device, "IsSimulator"):
            telescope = await manager.connect_device(device.id)
            
            # Safety check - verify it's parked
            if not telescope.client.AtPark:
                pytest.skip("Telescope not parked - unsafe to test")
            
            yield telescope
            
            # Ensure telescope is parked after test
            if not telescope.client.AtPark:
                await telescope.client.Park()
            
            await manager.disconnect_device(device.id)
            return
    
    pytest.skip("No real telescope found")
```

## Dual Mode Test Example

```python
class TestTelescopeMovement:
    """Tests that work with both simulator and real hardware."""
    
    @pytest.mark.asyncio
    async def test_basic_slew(self, telescope_fixture):
        """Test basic slewing - safe for both modes."""
        # This fixture automatically provides simulator or real telescope
        result = await telescope_fixture.slew_to_coordinates(
            ra=5.5,    # Safe coordinates
            dec=45.0,
            max_duration=10.0  # Timeout for safety
        )
        
        assert result["success"] is True
        
        # Wait for slew to complete
        await asyncio.sleep(1.0)
        
        # Verify position (with tolerance for real hardware)
        position = await telescope_fixture.get_position()
        assert abs(position["ra"] - 5.5) < 0.1
        assert abs(position["dec"] - 45.0) < 0.1
    
    @pytest.mark.hardware_only
    @pytest.mark.slow
    async def test_tracking_accuracy(self, real_telescope):
        """Test tracking accuracy - hardware only."""
        # This test only runs with real hardware
        # Measures actual tracking performance over time
        pass
    
    @pytest.mark.simulator_only
    async def test_error_conditions(self, simulator_telescope):
        """Test error handling - simulator only."""
        # Safe to test errors/failures in simulator
        # without risk to real hardware
        pass
```

## CI/CD Pipeline Configuration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Unit Tests
        run: |
          pip install -e .[dev]
          pytest tests/unit/ -v

  integration-tests:
    runs-on: ubuntu-latest
    services:
      simulator:
        image: seestar/simulator:latest
        ports:
          - 4700:4700
    steps:
      - uses: actions/checkout@v3
      - name: Run Integration Tests
        env:
          ASCOM_TEST_MODE: simulator
          ASCOM_SIMULATOR_DEVICES: localhost:4700:seestar_simulator
        run: |
          pip install -e .[dev]
          pytest tests/integration/ tests/e2e/ -v

  hardware-tests:
    runs-on: [self-hosted, telescope]  # Requires runner with telescope
    if: github.event_name == 'release'  # Only on releases
    steps:
      - uses: actions/checkout@v3
      - name: Run Hardware Tests
        env:
          ASCOM_TEST_MODE: hardware
          SEESTAR_IP: ${{ secrets.TELESCOPE_IP }}
        run: |
          pip install -e .[dev]
          pytest tests/e2e/ -v -m "not simulator_only"
```

## Running Tests Locally

### Quick Start (Simulator)
```bash
# Start simulator
cd ../seestar_alp
python simulator/src/main.py --port 4700 &

# Run all tests with simulator
cd ../mcp-server-ascom
pytest -v

# Run specific test category
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests
pytest tests/e2e/ -v           # End-to-end tests
```

### Hardware Testing
```bash
# Ensure telescope is connected and parked
export ASCOM_TEST_MODE=hardware
export SEESTAR_IP=192.168.1.100

# Run hardware-compatible tests
pytest tests/e2e/ -v -m "not simulator_only"

# Run specific hardware test
pytest tests/e2e/test_real_hardware.py::test_focus_control -v
```

### Test Selection
```bash
# Run only simulator tests
pytest -m "simulator_only or not hardware_only" -v

# Run only hardware tests  
pytest -m "hardware_only" -v

# Skip slow tests
pytest -m "not slow" -v

# Run smoke tests only
pytest -m "smoke" -v
```

## Safety Guidelines for Hardware Testing

1. **Always Park First**: Ensure telescope is parked before testing
2. **Use Timeouts**: Set maximum durations for all operations
3. **Limit Movements**: Restrict slew angles and speeds
4. **Monitor State**: Check telescope state before/after operations
5. **Emergency Stop**: Have manual override available
6. **Test in Stages**: Validate with simulator before hardware

## Test Coverage Requirements

- **Unit Tests**: 90%+ coverage of business logic
- **Integration Tests**: 80%+ coverage of MCP tools
- **E2E Tests**: Cover critical user workflows
- **Hardware Tests**: Validate key hardware interactions

## Troubleshooting

### Simulator Not Found
```bash
# Check if simulator is running
curl http://localhost:4700/api/v1/telescope/0/connected

# Check environment
echo $ASCOM_SIMULATOR_DEVICES

# Start simulator manually
cd ../seestar_alp
python simulator/src/main.py --port 4700
```

### Hardware Connection Issues
```bash
# Test direct connection
curl "http://$SEESTAR_IP:5555/api/v1/telescope/1/connected?ClientID=1&ClientTransactionID=1"

# Check discovery
python -c "from ascom_mcp.devices.manager import DeviceManager; ..."
```

### Mock Import Errors
```bash
# Ensure test_setup.py is imported before any ASCOM modules
# Check that alpaca/alpyca are properly mocked in tests/test_setup.py
```

## Best Practices

1. **Default to Simulator**: Make simulator the default for safety
2. **Explicit Hardware Mode**: Require explicit flag for hardware tests
3. **Gradual Validation**: Test with simulator → staging → production
4. **Document Hardware Tests**: Clearly mark hardware requirements
5. **Fail Safe**: Tests should fail safely if hardware unavailable
6. **Version Everything**: Track hardware firmware versions in tests

## Known Issues to Test For

Critical issues that broke previous releases:

1. **Coroutine entry point** (v0.2.1): `RuntimeWarning: coroutine 'main' was never awaited`
2. **API parameter changes** (v0.2.2-3): MCP SDK parameter updates  
3. **Protocol negotiation**: Supporting both 2024-11-05 and 2025-06-18
4. **Installation methods**: pip, uvx, and direct execution
5. **FastMCP patterns**: Context parameter, ToolError handling

## Future Enhancements

1. **Hardware Test Lab**: Dedicated test telescope setup
2. **Remote Testing**: VPN access to test hardware
3. **Performance Baselines**: Track hardware performance over time
4. **Automated Safety Checks**: Pre-flight checks before hardware tests
5. **Test Recording**: Record hardware test sessions for debugging
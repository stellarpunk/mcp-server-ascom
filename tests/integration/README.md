# Integration Tests

These tests verify end-to-end functionality with actual simulators.

## Test Categories

### 1. Discovery Tests (`test_discovery_timeout.py`)
- Test discovery with actual network timeouts
- Verify ASCOM_SKIP_UDP_DISCOVERY behavior
- Test device pre-population

### 2. Event Stream Tests (`test_event_stream.py`)
- Handle Seestar event messages (BalanceSensor, FocuserMove, etc.)
- Test concurrent command/event handling
- Verify state synchronization

### 3. Observation Workflow Tests (`test_observation_workflow.py`)
- Complete observation session lifecycle
- Target acquisition and imaging
- Error recovery scenarios

### 4. MCP Protocol Tests (`test_mcp_integration.py`)
- Test actual MCP tool execution (not mocked)
- Verify async/await behavior at runtime
- Test error propagation through MCP

## Running Integration Tests

```bash
# Start simulator first
cd ../seestar_alp
python root_app.py

# Run integration tests
cd ../mcp-server-ascom
pytest tests/integration/ -v
```

## Key Differences from Unit Tests

1. **No mocking of alpyca** - Uses real HTTP connections
2. **Actual simulators** - Tests against running services
3. **Real timing** - Tests timeouts and delays
4. **State persistence** - Tests device state across calls
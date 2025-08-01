# Testing Strategy

Two layers. Simple. Works.

## Architecture

1. **Unit tests** (`tests/unit/`) - Core logic, mocked devices
2. **MCP tests** (`tests/mcp/`) - Protocol validation

## Benefits

- No external dependencies
- Fast (in-memory)
- Deterministic
- CI-friendly
- Complete coverage

## Test Structure

```
tests/
├── unit/          # Business logic (37 tests, all pass)
├── mcp/           # Protocol compliance  
└── conftest.py    # Fixtures
```

## Examples

Real-world workflows live in `examples/`:
- `workflows/` - Complete sessions
- `discovery/` - Finding devices

## Test Patterns

### Unit Test
```python
async def test_discovery_logic():
    tools = DiscoveryTools(mock_manager)
    result = await tools.discover_devices()
    assert result["success"] is True
```

### MCP Test  
```python
async def test_discovery_through_mcp():
    async with Client(mcp) as client:
        result = await client.call_tool("discover_ascom_devices", {})
        data = json.loads(result.content[0].text)
        assert data["success"] is True
```

## What We Test

**Unit Tests:**
- Discovery logic
- Connection management  
- Coordinate calculations
- Error handling
- Device state

**MCP Tests:**
- Tool registration
- Parameter validation
- Response format
- ToolError compliance
- Resource access

## Running Tests

```bash
# Activate venv
source .venv/bin/activate

# Unit tests
pytest tests/unit/ -v

# MCP tests  
pytest tests/mcp/ -v

# All tests
pytest tests/ -v

# With coverage
pytest --cov=ascom_mcp --cov-report=html
```

## Key Fixtures

```python
@pytest.fixture
def mock_context():
    """FastMCP Context for testing"""
    ctx = MagicMock(spec=Context)
    # Direct methods, no ctx.logger
    return ctx

@pytest.fixture
def mock_telescope():
    """ASCOM telescope mock"""
    telescope = MagicMock()
    telescope.Connected = True
    telescope.CanSlew = True
    telescope.SlewToCoordinatesAsync = AsyncMock()
    return telescope
```

## Common Issues

**Import errors?** 
- Activate venv: `source .venv/bin/activate`
- Alpaca/alpyca mocked via test_setup.py

**Hanging tests?**
- Use `mock_device_discovery` fixture
- Set short timeouts

**FastMCP Client API:**
- `list_tools()` returns Tool objects with `.name`
- `call_tool()` result has `.content[0].text`

## CI/CD

```yaml
- name: Run tests
  run: |
    source .venv/bin/activate
    pytest tests/ -v
```

Tests run in seconds. No external servers needed.
# Test Suite Context

## 🧪 Testing Strategy
- **Unit tests**: Core functionality isolation
- **Integration tests**: Full MCP protocol flow
- **Fixture-based**: Consistent test environments

## 📋 Test Structure
```
tests/
├── test_server_fastmcp.py  # MCP server tests
├── test_ascom_client.py    # ASCOM client tests
├── test_config.py          # Configuration tests
└── conftest.py             # Shared fixtures
```

## 🔑 Key Fixtures

### `mock_ascom_response`
```python
@pytest.fixture
def mock_ascom_response():
    return {
        "Value": True,
        "ClientTransactionID": 1,
        "ServerTransactionID": 1,
        "ErrorNumber": 0,
        "ErrorMessage": ""
    }
```

### `test_client`
```python
@pytest.fixture
async def test_client():
    client = ASCOMClient()
    await client.initialize()
    yield client
    # Cleanup
```

## ✅ Test Patterns

### Discovery Testing
```python
async def test_discover_with_known_devices(test_client, monkeypatch):
    monkeypatch.setenv("ASCOM_KNOWN_DEVICES", "localhost:5555:test")
    devices = await test_client.discover_devices()
    assert any(d.device_name == "test" for d in devices)
```

### Error Handling
```python
async def test_connection_error():
    with pytest.raises(ConnectionError):
        await client.connect("invalid_device")
```

## 🚀 Running Tests
```bash
# Full suite with coverage
pytest tests/ -v --cov=ascom_mcp --cov-report=html

# Specific test file
pytest tests/test_server_fastmcp.py -v

# With markers
pytest -m "not integration" -v
```

## 📊 Coverage Goals
- Target: 80%+ coverage
- Focus on critical paths
- Mock external dependencies
# ASCOM MCP Core Implementation

## 🎯 Module Overview
Core implementation of ASCOM device bridging to MCP protocol.

## 🏗️ Key Components

### `server_fastmcp.py`
- FastMCP 2.0 server implementation
- Tool registration and capabilities
- Connection state management

### `ascom_client.py`
- ASCOM Alpaca HTTP client
- Device discovery (UDP port 32227)
- Management API integration

### `config.py`
- Known devices configuration
- Environment variable parsing
- `ASCOM_KNOWN_DEVICES` format: `host:port:name`

### `models.py`
- Pydantic models for ASCOM responses
- Type-safe device metadata
- Validation and serialization

## 🔧 Critical Functions

```python
# Always ensure initialization
async def ensure_initialized():
    if client is None:
        await initialize_client()

# Device discovery pattern
devices = await client.discover_devices(timeout=5.0)
devices.extend(client._known_devices)  # Include configured devices
```

## ⚡ Performance Tips
- Cache device connections in `_connections` dict
- Reuse HTTP session for multiple requests
- Discovery timeout: 5 seconds default

## 🐛 Common Issues
- **NoneType errors** → Missing `ensure_initialized()`
- **Discovery fails** → Use `ASCOM_KNOWN_DEVICES`
- **Connection refused** → Check device is running

## 🔍 Debugging
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check initialization
logger.debug(f"Client initialized: {client is not None}")
logger.debug(f"Known devices: {client._known_devices}")
```
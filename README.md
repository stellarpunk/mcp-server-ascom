# MCP Server for ASCOM

[![MCP](https://img.shields.io/badge/MCP-2025--06--18-brightgreen.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-server-ascom.svg)](https://pypi.org/project/mcp-server-ascom/)
[![Tests](https://github.com/stellarpunk/mcp-server-ascom/workflows/Test/badge.svg)](https://github.com/stellarpunk/mcp-server-ascom/actions)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Control astronomy equipment through AI. MCP 2025-06-18 compliant.

## What's New in v0.3.0

- **FastMCP** - Uses official SDK. Half the code. Same functionality.
- **Structured Logging** - JSON to stderr. OpenTelemetry compatible.
- **Better Errors** - FastMCP validates protocol compliance automatically.

## Features

- **FastMCP** - Production-ready. Clean API.
- **Observable** - JSON logs. Grafana-ready.
- **Any ASCOM Device** - Telescopes. Cameras. Focusers. More.
- **Natural Language** - "Point at M31" works.
- **Auto-Discovery** - Zero configuration.
- **Fast** - Async. Never blocks.
- **Secure** - OAuth ready. Off by default.
- **Extensible** - Add device types easily.
- **Tested** - Full coverage. Type safe.

## Installation

### Option 1: pip install (Simplest)
```bash
pip install mcp-server-ascom
```

### Option 2: uvx (No install needed)
```bash
uvx mcp-server-ascom
```

### Option 3: From source
```bash
git clone https://github.com/stellarpunk/mcp-server-ascom.git
cd mcp-server-ascom
pip install -e .
```

**Note:** The `alpyca` package (ASCOM library) imports as `alpaca` in Python code.

## Configuration

### Claude Desktop

#### Quick Setup (Recommended)
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "uvx",
      "args": ["mcp-server-ascom"]
    }
  }
}
```

This uses `uvx` to automatically handle Python environments and dependencies.

#### Alternative: Direct Installation
```bash
pip install mcp-server-ascom
```

Then use:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "mcp-server-ascom"
    }
  }
}
```

### Running the Server

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the server
python -m ascom_mcp
```

### MCP Inspector (Testing)
```bash
npm install -g @modelcontextprotocol/inspector

# With virtual environment
mcp-inspector .venv/bin/python -m ascom_mcp

# Or if mcp-server-ascom is in PATH
mcp-inspector mcp-server-ascom
```

## Usage

```
You: Connect to my telescope
AI: Found Seestar S50. Connected.

You: Point at the Orion Nebula
AI: Slewing to M42... Done.
```

## Supported Equipment

ASCOM Alpaca devices: Telescopes. Cameras. Focusers. Filter wheels. Domes.

## Tools

**Find devices**: `discover_ascom_devices`  
**Control telescope**: `connect` `goto` `goto_object` `park`  
**Use camera**: `connect` `capture` `get_status`

## Development

### Setup
```bash
git clone https://github.com/stellarpunk/mcp-server-ascom.git
cd mcp-server-ascom

# Create virtual environment (choose one)
uv venv                    # Using uv
python -m venv .venv       # Using standard venv

# Activate
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"    # or: uv pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ascom_mcp

# Run specific test file
pytest tests/test_device_manager.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

**Secure by Design** - Local connections only by default.

### Advanced Security (OAuth)
For production deployments with remote access:

```bash
cp .env.example .env
# Edit .env: ASCOM_MCP_OAUTH_ENABLED=true
# Configure OAuth provider settings
# Restart server
```

See [security.py](src/ascom_mcp/security.py) for configuration options.

## Troubleshooting

### ModuleNotFoundError: No module named 'alpyca'
The `alpyca` package installs as `alpaca`. Use:
```python
from alpaca import discovery  # NOT from alpyca
```

### Virtual Environment Issues
Always activate your virtual environment before running:
```bash
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### No ASCOM devices found
1. Ensure devices are powered on and connected to network
2. Check firewall settings (UDP port 32227 for discovery)
3. Try manual discovery at known IP:
   ```bash
   curl http://device-ip:11111/api/v1/description
   ```

## License

MIT - see [LICENSE](LICENSE)

## See Also

- [Seestar S50 Integration Guide](docs/seestar_integration.md)
- [ASCOM Standards](https://ascom-standards.org/)
- [Alpaca API Reference](https://ascom-standards.org/api/)
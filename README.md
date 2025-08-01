# MCP Server for ASCOM

[![MCP](https://img.shields.io/badge/MCP-2025--06--18-brightgreen.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/mcp-server-ascom.svg)](https://pypi.org/project/mcp-server-ascom/)
[![Tests](https://github.com/stellarpunk/mcp-server-ascom/workflows/Test/badge.svg)](https://github.com/stellarpunk/mcp-server-ascom/actions)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Control telescopes with AI. Works with any ASCOM device.

## Documentation

- [Quick Start Guide](QUICKSTART.md)
- [API Reference](docs/API.md)
- [Development Guide](docs/development.md)
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)
- [Testing Guide](tests/README.md)

## v0.3.0 Updates

- FastMCP 2.0 - Half the code
- JSON logging - OpenTelemetry ready
- Better errors - Protocol compliance built-in

## Features

- Works with any ASCOM telescope, camera, or focuser
- Natural language control: "Point at the Orion Nebula"
- Auto-discovers devices on your network
- Async architecture - never blocks
- Full test coverage and type safety

## Installation

```bash
# Quick start
pip install mcp-server-ascom

# Or use uvx (no install)
uvx mcp-server-ascom
```

## Claude Desktop Setup

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

Restart Claude Desktop to activate.

## Usage

```
You: Connect to my telescope
AI: Found Seestar S50. Connected.

You: Point at the Orion Nebula
AI: Slewing to M42... Done.
```

## Supported Equipment

Any ASCOM Alpaca device: telescopes, cameras, focusers, filter wheels, domes.

## Available Tools

- `discover_ascom_devices` - Find devices on network
- `telescope_connect` / `camera_connect` - Connect to device
- `telescope_goto` / `telescope_goto_object` - Point telescope
- `telescope_park` - Park at home position
- `camera_capture` - Take images

## Development

```bash
git clone https://github.com/stellarpunk/mcp-server-ascom.git
cd mcp-server-ascom
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Security

Local connections only by default. For remote access, enable OAuth in `.env`.

## Troubleshooting

**No devices found?**
- Check device is powered on and on same network
- Allow UDP port 32227 through firewall
- Test with: `curl http://device-ip:11111/api/v1/description`

**Import errors?** The `alpyca` package imports as `alpaca`.

See [troubleshooting.md](docs/troubleshooting.md) for more.

## Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Quick setup guide
- [API Reference](docs/API.md) - Tool documentation
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Seestar Integration](docs/seestar_integration.md) - Seestar S50 guide

## License

MIT
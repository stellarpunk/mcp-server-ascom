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
- [Testing Strategy](docs/E2E_TESTING_GUIDE.md)
- [Examples](examples/README.md)

## 🎯 v0.5.0: Visual Feedback & Type Safety!

See what your telescope sees:
- **Visual Preview**: `telescope_preview()` shows current view
- **Live Streaming**: `telescope_start_streaming()` for MJPEG feed  
- **Where Am I?**: `telescope_where_am_i()` with position + image
- **Type-Safe SDK**: No more parameter guessing!
- **Scenery Mode**: Optimized for terrestrial viewing

## Features

- Works with any ASCOM telescope, camera, or focuser
- Natural language control: "Point at the Orion Nebula"
- Visual feedback - always see where telescope points
- Type-safe Python SDK with full validation
- MJPEG streaming for real-time monitoring
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

### Previous Updates

**v0.4.0**: Instant connections without discovery  
**v0.3.0**: FastMCP 2.0, JSON logging, better errors

## Claude Desktop Setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "uvx",
      "args": ["mcp-server-ascom"],
      "env": {
        "ASCOM_DIRECT_DEVICES": "telescope_1:localhost:5555:Seestar S50"
      }
    }
  }
}
```

Restart Claude Desktop to activate.

## Claude Code Setup

```bash
git clone https://github.com/stellarpunk/mcp-server-ascom
cd mcp-server-ascom
python -m venv .venv
source .venv/bin/activate
pip install -e .

claude mcp add ascom "$PWD/.venv/bin/python" -- "$PWD/launcher.py"
```

## Usage

### Quick Connect (No Configuration)
```
You: Connect to seestar@192.168.1.100:5555
AI: Connected to Seestar S50!

You: Point at the Orion Nebula  
AI: Slewing to M42... Done.
```

### With Pre-Configured Devices
```
You: Connect to telescope_1
AI: Connected to Seestar S50!
```

## Supported Equipment

Any ASCOM Alpaca device: telescopes, cameras, focusers, filter wheels, domes.

## Available Tools

- `discover_ascom_devices` - Find devices on network
- `telescope_connect` / `camera_connect` - Connect to device
- `telescope_goto` / `telescope_goto_object` - Point telescope
- `telescope_park` - Park at home position
- `camera_capture` - Take images

## Event Streaming 🆕

Real-time event streaming from ASCOM devices (especially Seestar S50):

- **Event History**: `get_event_history` - Retrieve past events with filtering
- **Event Types**: `get_event_types` - List available event types  
- **Event Stream**: `ascom://events/{device_id}/stream` - Live event feed
- **Clear History**: `clear_event_history` - Clear event buffer

Supported event types:
- `PiStatus` - System status (battery, temperature)
- `GotoComplete` - Movement completed
- `BalanceSensor` - Device orientation
- `ViewChanged` - View state changes
- And more...

## Development

```bash
git clone https://github.com/stellarpunk/mcp-server-ascom.git
cd mcp-server-ascom
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Development with hot-reload
invoke dev --hot  # Auto-restarts on code changes

# Run tests
pytest
```

Hot-reload uses `watchmedo` to monitor Python files and restart automatically.
See [Development Guide](docs/development.md) for details.

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
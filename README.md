# MCP Server for ASCOM

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/astronomy-tools/mcp-server-ascom/workflows/Test/badge.svg)](https://github.com/astronomy-tools/mcp-server-ascom/actions)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Control ASCOM astronomy equipment through AI assistants.

## Features

- Works with any ASCOM Alpaca device
- Natural language: "Point at M31" instead of coordinates
- Auto-discovery of devices on network
- Non-blocking async operations
- Type-safe with full test coverage

## Installation

```bash
# From PyPI (when published)
pip install mcp-server-ascom

# Development
git clone https://github.com/astronomy-tools/mcp-server-ascom.git
cd mcp-server-ascom
./install.sh
```

## Configuration

### Claude Desktop
Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):
```json
{
  "mcpServers": {
    "ascom": {
      "command": "mcp-server-ascom"
    }
  }
}
```

### MCP Inspector (Testing)
```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector python -m ascom_mcp
```

## Usage

Start conversation: "Connect to my telescope"  
Then: "Point at M31" → "Take a 30 second exposure"

## Supported Equipment

Any ASCOM Alpaca-compatible device:
- Telescopes/Mounts
- Cameras
- Focusers
- Filter wheels
- Domes

## Tools

**Discovery:** `discover_ascom_devices`

**Telescope:** `connect`, `goto`, `goto_object`, `get_position`, `park`

**Camera:** `connect`, `capture`, `get_status`

## Development

```bash
git clone https://github.com/astronomy-tools/mcp-server-ascom.git
cd mcp-server-ascom
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT - see [LICENSE](LICENSE)

## See Also

- [Seestar S50 Integration Guide](docs/seestar_integration.md)
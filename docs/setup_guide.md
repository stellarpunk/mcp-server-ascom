# ASCOM MCP Server Setup Guide

## Prerequisites

1. **Python 3.10+** installed
2. **ASCOM-compatible devices** on your network (or use simulators)
3. **MCP-compatible AI assistant** (e.g., Claude Desktop)

## Installation

### 1. Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd mcp-server-ascom

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### 2. Verify Installation

```bash
# Test the server can be imported
python -c "from ascom_mcp import create_server; print('✓ Import successful')"

# Run the example
python examples/example_usage.py
```

## Configuration

### For Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ascom": {
      "command": "python",
      "args": ["-m", "ascom_mcp"],
      "cwd": "/path/to/mcp-server-ascom"
    }
  }
}
```

### Environment Variables

Optional environment variables:

```bash
export LOG_LEVEL=DEBUG  # Set logging level (default: INFO)
export ASCOM_DISCOVERY_TIMEOUT=10  # Discovery timeout in seconds (default: 5)
```

## Testing with Simulators

If you don't have physical ASCOM devices, you can use simulators:

### 1. ASCOM Simulator (Windows)

Download and install the ASCOM Platform from https://ascom-standards.org/

### 2. Python Telescope Simulator

```python
# Simple telescope simulator for testing
from alpyca import TelescopeSimulator

simulator = TelescopeSimulator(port=11111)
simulator.start()
```

## Quick Start

### 1. Start the Server Manually

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python -m ascom_mcp
```

### 2. Test with Example Requests

The server accepts JSON-RPC requests over stdio. Example:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

### 3. Using with AI Assistant

Once configured in Claude Desktop, you can say:

- "Connect to my telescope"
- "Show me the Orion Nebula"
- "Take a 30 second exposure"
- "Park the telescope"

## Troubleshooting

### No Devices Found

1. Check devices are powered on and connected to network
2. Verify firewall allows UDP port 32227 (discovery)
3. Try increasing discovery timeout

### Connection Failed

1. Check device IP and port are correct
2. Verify no other software is using the device
3. Check ASCOM drivers are installed (Windows)

### Import Errors

1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -e .`
3. Check Python version is 3.10+

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/

# Type checking
mypy src/
```

## Next Steps

1. **Add More Device Types**: Implement focuser, filter wheel support
2. **Enhance AI Features**: Add observation planning, image analysis
3. **Create GUI**: Optional control panel for manual testing
4. **Add Persistence**: Save device configurations

## Support

- GitHub Issues: [Report bugs and feature requests]
- Documentation: See `/docs` folder
- ASCOM Standards: https://ascom-standards.org/
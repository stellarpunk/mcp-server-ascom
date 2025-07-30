# ASCOM MCP Server Quick Start

Get up and running in 5 minutes with the latest MCP 2025-06-18 protocol.

## 1. Install

```bash
git clone https://github.com/astronomy-tools/mcp-server-ascom.git
cd mcp-server-ascom
./install.sh
```

## 2. Test with MCP Inspector

```bash
# Install inspector (once)
npm install -g @modelcontextprotocol/inspector

# Test server (with venv)
./inspect.sh

# Or manually:
source .venv/bin/activate
mcp-inspector python -m ascom_mcp
```

In the inspector:
1. Click "discover_ascom_devices" tool
2. Set timeout: 5
3. Execute

## 3. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ascom": {
      "command": "python",
      "args": ["-m", "ascom_mcp"],
      "cwd": "/path/to/mcp-server-ascom",
      "env": {
        "PYTHONPATH": "/path/to/mcp-server-ascom/src"
      }
    }
  }
}
```

Restart Claude Desktop.

## 4. Test with Seestar

Terminal 1 - Start seestar_alp:
```bash
cd /path/to/seestar_alp
source venv/bin/activate
python root_app.py
```

Terminal 2 - Verify it's running:
```bash
curl http://localhost:5555/api/v1/telescope/0/connected
```

In Claude:
```
You: Discover my telescope
Claude: Found Seestar S50 at localhost:5555

You: Connect to it
Claude: Connected to Seestar S50

You: Point at the Moon
Claude: Calculating Moon position... Slewing telescope...
```

## Common Issues

**No module named 'ascom_mcp'**
- Run: `pip install -e .` in the project directory

**No devices found**
- Check seestar_alp is running
- Verify network connectivity
- Try manual discovery: `curl http://localhost:32227/`

**Claude doesn't see the server**
- Check JSON syntax in config file
- Restart Claude Desktop completely
- Check logs: `tail -f ~/Library/Logs/Claude/*.log`

## Next Steps

- Read [Seestar Integration Guide](docs/seestar_integration.md)
- Try example astronomy targets
- Add support for new devices (see [Contributing](CONTRIBUTING.md))
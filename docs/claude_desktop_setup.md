# Claude Desktop Setup Guide

This guide helps you configure Claude Desktop to use the ASCOM MCP Server.

## Prerequisites

1. Claude Desktop installed
2. Python 3.10+ installed
3. ASCOM MCP Server installed

## Configuration Steps

### 1. Locate Configuration File

The configuration file location depends on your operating system:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Basic Configuration

For installed package:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "mcp-server-ascom",
      "args": [],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 3. Development Configuration

For development from source:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "python",
      "args": ["-m", "ascom_mcp"],
      "cwd": "/path/to/mcp-server-ascom",
      "env": {
        "PYTHONPATH": "/path/to/mcp-server-ascom/src",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### 4. With Seestar Integration

For use with seestar_alp:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "mcp-server-ascom",
      "env": {
        "LOG_LEVEL": "INFO",
        "ASCOM_DISCOVERY_TIMEOUT": "10"
      }
    }
  }
}
```

## Verification

1. **Restart Claude Desktop** after editing configuration

2. **Check server started**: Look for "ascom" in Claude's MCP servers list

3. **Test discovery**: 
   ```
   You: "Discover ASCOM devices"
   Claude: [Should list any devices found on network]
   ```

4. **Check logs** (if issues):
   - macOS: `~/Library/Logs/Claude/`
   - Check console output if running from terminal

## Troubleshooting

### Server Not Starting

1. Check JSON syntax is valid
2. Verify Python path is correct
3. Test command manually:
   ```bash
   mcp-server-ascom --version
   ```

### No Devices Found

1. Ensure ASCOM devices are on same network
2. Check firewall settings (UDP port 32227)
3. Try increasing discovery timeout

### Permission Errors

On macOS, you may need to grant network access:
- System Preferences → Security & Privacy → Firewall

## Environment Variables

- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `ASCOM_DISCOVERY_TIMEOUT`: Seconds to search for devices (default: 5)
- `ASCOM_ALPACA_PORT`: Default Alpaca port (default: 11111)

## Multiple Servers

You can configure multiple MCP servers:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "mcp-server-ascom"
    },
    "weather": {
      "command": "mcp-server-weather"
    }
  }
}
```
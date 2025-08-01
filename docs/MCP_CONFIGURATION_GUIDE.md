# MCP Configuration Guide

This guide explains how to configure the ASCOM MCP server for optimal performance.

## Environment Variables

### Device Configuration

#### ASCOM_DIRECT_DEVICES
Pre-populate devices without discovery. Format:
```
device_id:host:port:name[,device_id:host:port:name...]
```

Example:
```bash
export ASCOM_DIRECT_DEVICES="telescope_1:localhost:5555:Seestar S50,telescope_99:localhost:4700:Simulator"
```

#### ASCOM_KNOWN_DEVICES
Define known device endpoints for checking. Format:
```
host:port:name[,host:port:name...]
```

Example:
```bash
export ASCOM_KNOWN_DEVICES="localhost:5555:seestar_alp,localhost:4700:simulator"
```

#### ASCOM_PREPOPULATE_KNOWN (Deprecated)
No longer needed - devices are resolved on-demand from multiple sources.

## Claude Code Configuration

### Optimal Configuration (v0.4.0+)

Create or update `~/.claude.json`:

```json
{
  "mcpServers": {
    "ascom": {
      "type": "stdio",
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "ascom_mcp.server"],
      "env": {
        "ASCOM_DIRECT_DEVICES": "telescope_1:localhost:5555:Seestar S50,telescope_99:localhost:4700:Simulator"
      }
    }
  }
}
```

### Using PyPI Package

```json
{
  "mcpServers": {
    "ascom": {
      "type": "stdio", 
      "command": "uvx",
      "args": ["--from", "mcp-server-ascom", "mcp-server-ascom"],
      "env": {
        "ASCOM_DIRECT_DEVICES": "telescope_1:localhost:5555:Seestar S50"
      }
    }
  }
}
```

## Connection Methods (v0.4.0+)

### 1. Direct Connection String
Connect without any configuration:
```bash
/mcp ascom telescope_connect device_id="seestar@192.168.1.100:5555"
```

### 2. Environment Configuration
Pre-define devices in `ASCOM_DIRECT_DEVICES`:
```bash
/mcp ascom telescope_connect device_id="telescope_1"
```

### 3. Persistent State
Previously discovered devices are remembered:
```bash
# First time - discover
/mcp ascom discover_ascom_devices
# Later sessions - direct connect
/mcp ascom telescope_connect device_id="telescope_1"
```

### 4. Known Devices Config
Devices in config are always available.

## Configuration Strategy

### For Development
1. Use direct connection strings for quick testing
2. Or define devices in `ASCOM_DIRECT_DEVICES`

### For Production
1. Run discovery once to populate state
2. Devices persist across restarts
3. Use `ASCOM_DIRECT_DEVICES` for critical devices

### For New Users
1. Try direct connection: `seestar@host:port`
2. If successful, add to `ASCOM_DIRECT_DEVICES`
3. Or run discovery to find all devices

## Device ID Format

Device IDs follow the pattern: `{type}_{number}`

Examples:
- `telescope_1` - First telescope
- `camera_0` - First camera  
- `focuser_2` - Third focuser

## Troubleshooting

### "Device not found" Error
The error message now provides helpful options:
1. Use direct connection: `device_id="seestar@host:port"`
2. Add to `ASCOM_DIRECT_DEVICES` environment
3. Run discovery: `/mcp ascom discover_ascom_devices`

### Discovery Not Needed
Unlike v0.3.x, discovery is never automatic. Connect directly!

### State Persistence
Devices are saved to `~/.ascom_mcp/devices.json`
- Survives restarts
- Auto-cleaned after 30 days
- Delete file to reset

## Example Workflows

### Quick Connect (No Setup Required)
```bash
# Direct connection string
/mcp ascom telescope_connect device_id="seestar@192.168.1.100:5555"
/mcp ascom telescope_get_position device_id="seestar@192.168.1.100:5555"
```

### With Environment Config
```bash
# Using ASCOM_DIRECT_DEVICES
/mcp ascom telescope_connect device_id="telescope_1"
/mcp ascom telescope_goto device_id="telescope_1" ra=10.0 dec=45.0
```

### Discovery Workflow
```bash
# Only when adding new devices
/mcp ascom discover_ascom_devices timeout=10
/mcp ascom list_devices

# Connect using discovered ID
/mcp ascom telescope_connect device_id="telescope_0"
```
# Claude Desktop Testing Checklist

## Setup Complete
- ✅ Server installed: `/Users/jschulle/miniforge3/bin/mcp-server-ascom`
- ✅ Config added to: `~/Library/Application Support/Claude/claude_desktop_config.json`
- ✅ Server name: `ascom`

## Test Commands for Claude Desktop

After restarting Claude Desktop, try these commands:

### 1. Basic Connection Test
"Can you discover ASCOM devices on my network?"

Expected: Should run `discover_ascom_devices` tool and report 0 devices (unless you have ASCOM devices).

### 2. Server Info Test  
"Show me the ASCOM server information"

Expected: Should fetch `ascom://server/info` resource and display version 0.2.0.

### 3. List Available Tools
"What ASCOM tools are available?"

Expected: Should list 11 tools including telescope and camera controls.

### 4. Error Handling Test
"Connect to telescope_0"

Expected: Should fail gracefully with "Device telescope_0 not found" message.

## Known Issues
- numpy/astropy imports fail in miniforge environment
- Tests can't run due to environment issue
- Server itself works fine without astropy features

## Next Steps
1. Restart Claude Desktop
2. Look for "ascom" in MCP servers list
3. Test the commands above
4. Check logs if issues: `tail -f ~/Library/Logs/Claude/*.log`
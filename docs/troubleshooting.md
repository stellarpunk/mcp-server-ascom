# Troubleshooting ASCOM MCP Server

Quick fixes for common issues.

## Claude Desktop Shows "Disabled"

**Symptom**: ASCOM MCP appears but shows as disabled in Claude Desktop.

**Cause**: Server not responding to MCP protocol requests.

**Fix**: Update to v0.2.4+:
```bash
pip install --upgrade mcp-server-ascom
# Clear cache
uv cache clean
# Restart Claude Desktop
```

## "Method not found" Errors

**Symptom**: Logs show `{"error":{"code":-32601,"message":"Method not found"}}`.

**Fix**: Upgrade to v0.2.4+ which properly registers MCP handlers.

## "Coroutine was never awaited"

**Symptom**: Server fails with `RuntimeWarning: coroutine 'main' was never awaited`.

**Fix**: Fixed in v0.2.1+. Update your package.

## Server Won't Start

**Check**:
1. Python 3.10+ installed
2. Virtual environment active
3. Dependencies installed: `pip install mcp-server-ascom`

**Debug**:
```bash
# Test directly
python -m ascom_mcp --version

# Check logs
tail -f ~/Library/Logs/Claude/mcp-server-ascom.log
```

## No Devices Found

**Check**:
1. ASCOM devices on network
2. Same subnet as computer
3. Firewall allows discovery

**Test**:
```bash
# Use MCP Inspector
mcp-inspector python -- -m ascom_mcp
# Run: tools/call discover_ascom_devices {"timeout": 10}
```

## Installation Issues

**uvx fails**:
```bash
# Clear cache
uv cache clean
# Try pip
pip install mcp-server-ascom
```

**Import errors**:
```bash
# Wrong: import alpaca
# Right: import alpyca  # Note the 'y'
```

## Version Check

```bash
# CLI version
mcp-server-ascom --version

# Python version
python -c "import ascom_mcp; print(ascom_mcp.__version__)"
```

## Report Issues

Still stuck? [Open an issue](https://github.com/stellarpunk/mcp-server-ascom/issues) with:
- Error message
- Version (`mcp-server-ascom --version`)
- Python version (`python --version`)
- Logs (`~/Library/Logs/Claude/mcp-server-ascom.log`)
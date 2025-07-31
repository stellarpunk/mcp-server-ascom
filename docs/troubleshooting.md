# Troubleshooting

## Common Issues

### Claude Desktop Shows "Disabled"

Server not starting properly.

**Fix:**
```bash
pip install --upgrade mcp-server-ascom
uv cache clean
# Restart Claude Desktop
```

### No Devices Found

**Check:**
- Device powered on
- Same network subnet
- Firewall allows UDP 32227

**Test discovery:**
```bash
curl http://device-ip:11111/api/v1/description
```

**Use known devices:**
```json
{
  "mcpServers": {
    "ascom": {
      "command": "uvx",
      "args": ["mcp-server-ascom"],
      "env": {
        "ASCOM_KNOWN_DEVICES": "localhost:5555:seestar_alp"
      }
    }
  }
}
```

### Import Errors

**Wrong:** `from alpaca import discovery`  
**Right:** `from alpyca import discovery`

The PyPI package `alpyca` imports as `alpaca` in code.

### Connection Timeouts

**Seestar specific:**
1. Ensure seestar_alp is running
2. Check telescope is opened: `action_start_up_sequence`
3. Verify mount is not parked

### UV Command Not Found

**In devcontainer:**
```bash
# Install UV in container
pip install uv
```

### ErrorMessage Field Missing

**Symptom:** ASCOM responses lack ErrorMessage field

**Fix:** Update seestar_alp's `device/shr.py`:
```python
if hasattr(err, 'message'):
    self.ErrorMessage = err.message
elif hasattr(err, 'args') and err.args:
    self.ErrorMessage = str(err.args[0])
else:
    self.ErrorMessage = str(err)
```

## Debug Commands

### Check Version
```bash
mcp-server-ascom --version
python -c "import ascom_mcp; print(ascom_mcp.__version__)"
```

### View Logs
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp-server-ascom.log

# Linux
tail -f ~/.local/share/Claude/logs/mcp-server-ascom.log
```

### Test with Inspector
```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector python -- -m ascom_mcp
```

## Seestar Integration

### Telescope Not Responding

1. Check seestar_alp logs: `tail -f alpyca.log`
2. Verify startup sequence completed
3. Ensure not in solar mode for night objects

### Focus Issues

- Temperature changes require refocus
- Typical ranges: Stars 1800-2000, Terrestrial 1200-1500

### Movement Problems

Remember Seestar angles are counterintuitive:
- North/South = horizontal pan
- East/West = vertical tilt

## Getting Help

Include in bug reports:
- Error message
- `mcp-server-ascom --version`
- `python --version`  
- Relevant logs
- Device type

[Open an issue](https://github.com/stellarpunk/mcp-server-ascom/issues)
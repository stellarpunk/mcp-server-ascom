# Testing ASCOM MCP Server with Real Seestar S50

## Prerequisites

1. **Seestar S50 connected** to your network
2. **seestar_alp running** at `http://localhost:5555`
3. **Claude Code** with ASCOM MCP server v0.3.0

## Quick Test

### 1. Verify Seestar Connection

```bash
# Check seestar_alp is running
curl http://localhost:5555/api/v1/telescope/1/connected

# Should return connected status
```

### 2. Test MCP Discovery

In Claude Code:
```
/mcp ascom discover_ascom_devices
```

Should find:
- `telescope_1: Seestar Alpha` at localhost:5555

### 3. Connect to Telescope

```
/mcp ascom telescope_connect device_id="telescope_1"
```

### 4. Control Tests

#### Get Position
```
/mcp ascom telescope_get_position device_id="telescope_1"
```

#### Custom Actions (Seestar-specific)

Open telescope:
```
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="action_start_up_sequence" \
  parameters='{"lat": 40.745, "lon": -74.0256, "move_arm": true}'
```

Start view mode:
```
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="method_sync" \
  parameters='{"method": "iscope_start_view", "params": {"mode": "scenery"}}'
```

Move telescope:
```
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="method_sync" \
  parameters='{"method": "scope_speed_move", "params": {"speed": 400, "angle": 90, "dur_sec": 3}}'
```

Go to preset:
```
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="goto_preset" \
  parameters='{"preset_id": "manhattan_skyline"}'
```

### 5. Shutdown Sequence

```
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="method_sync" \
  parameters='{"method": "pi_shutdown"}'

/mcp ascom telescope_disconnect device_id="telescope_1"
```

## Troubleshooting

**No devices found?**
- Ensure seestar_alp is running
- Check ASCOM_KNOWN_DEVICES environment variable
- Verify network connectivity

**Connection refused?**
- Start seestar_alp first
- Check firewall settings
- Verify port 5555 is accessible

**Custom actions fail?**
- Ensure telescope is connected
- Check mount is open (use startup sequence)
- Verify parameters JSON format

## Complete Workflow Example

```python
# 1. Discover devices
/mcp ascom discover_ascom_devices

# 2. Connect
/mcp ascom telescope_connect device_id="telescope_1"

# 3. Open telescope
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="action_start_up_sequence" \
  parameters='{"lat": 40.745, "lon": -74.0256, "move_arm": true}'

# 4. Start scenery view
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="method_sync" \
  parameters='{"method": "iscope_start_view", "params": {"mode": "scenery"}}'

# 5. Go to Manhattan preset
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="goto_preset" \
  parameters='{"preset_id": "manhattan_skyline"}'

# 6. Take control actions...

# 7. Shutdown
/mcp ascom telescope_custom_action \
  device_id="telescope_1" \
  action="method_sync" \
  parameters='{"method": "pi_shutdown"}'
```

## Next Steps

1. Test all standard ASCOM commands
2. Verify custom Seestar actions
3. Test error handling scenarios
4. Document any issues found
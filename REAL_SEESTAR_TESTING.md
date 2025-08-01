# Real Seestar Testing Guide for v0.4.0

## Pre-flight Checklist

### 1. Seestar Setup
- [ ] Seestar S50 powered on and connected to WiFi
- [ ] Note the Seestar's IP address (check router or use `seestar.local`)
- [ ] Ensure no other apps are connected to Seestar
- [ ] Battery level > 20%

### 2. Update Configuration
- [x] Set `simulator = false` in seestar_alp config
- [x] Set correct IP address (`seestar.local` or actual IP)
- [ ] Verify lat/lon coordinates in config match your location

### 3. Environment Setup
```bash
# Terminal 1: Start seestar_alp
cd /Users/jschulle/construction-mcp/seestar_alp
source venv/bin/activate  # or your virtual env
python root_app.py

# Terminal 2: Start ASCOM MCP server
cd /Users/jschulle/construction-mcp/mcp-server-ascom
source .venv/bin/activate
python -m ascom_mcp
```

## Test Sequence

### 1. Direct Connection (v0.4.0 Feature!)
```bash
# Test direct connection without discovery
/mcp ascom telescope_connect device_id="seestar@192.168.1.100:5555"

# Or if using mDNS
/mcp ascom telescope_connect device_id="seestar@seestar.local:5555"
```

### 2. Startup Sequence (CRITICAL)
```bash
# Initialize Seestar with your location
/mcp ascom telescope_custom_action \
  device_id="Telescope_1" \
  action="action_start_up_sequence" \
  parameters='{"lat": 40.745, "lon": -74.0256, "move_arm": true}'
```

### 3. Basic Operations
```bash
# Check status
/mcp ascom telescope_get_position device_id="Telescope_1"

# Small movement test (safe)
/mcp ascom telescope_custom_action \
  device_id="Telescope_1" \
  action="method_sync" \
  parameters='{"method": "scope_speed_move", "params": {"speed": 200, "angle": 90, "dur_sec": 1}}'

# Goto test (pick a visible object)
/mcp ascom telescope_goto_object device_id="Telescope_1" object_name="Moon"
```

### 4. Event Stream Test
```bash
# Monitor events while performing actions
# Events should appear in the MCP server logs
```

### 5. State Persistence Test
```bash
# 1. Disconnect
/mcp ascom telescope_disconnect device_id="Telescope_1"

# 2. Restart MCP server
# 3. Connect without discovery
/mcp ascom telescope_connect device_id="Telescope_1"
# Should work instantly!
```

## Safety Tests

### Solar Mode Test (CAUTION)
Only test during daytime with proper precautions:
```bash
/mcp ascom telescope_custom_action \
  device_id="Telescope_1" \
  action="method_sync" \
  parameters='{"method": "iscope_start_view", "params": {"mode": "sun"}}'
```

### Park Test
```bash
/mcp ascom telescope_park device_id="Telescope_1"
```

## Expected Results

### ✅ Success Indicators
- Direct connection works without discovery
- Startup sequence completes (~30 seconds)
- Movement commands execute smoothly
- Events appear in logs
- State persists across restarts

### ❌ Common Issues
- "Device busy" → Wait for startup to complete
- "Not connected" → Check IP address and network
- No movement → Verify not parked, check battery
- Timeout errors → Increase timeout values

## Log Monitoring
```bash
# Seestar ALP logs
tail -f /Users/jschulle/construction-mcp/seestar_alp/seestar_alp.log

# MCP server logs
tail -f /Users/jschulle/construction-mcp/mcp-server-ascom/mcp.log
```

## Rollback Plan
If issues arise:
```bash
# Restore simulator config
cd /Users/jschulle/construction-mcp/seestar_alp/device
cp config.toml.simulator.backup config.toml
```

## Performance Metrics
- [ ] Direct connection time: ___ seconds (target: <2s)
- [ ] Discovery time (if used): ___ seconds (v0.3: 180s, target: <30s)
- [ ] Startup sequence: ___ seconds (typical: 30s)
- [ ] Goto response time: ___ seconds
- [ ] Event latency: ___ ms

## Next Steps
After successful testing:
1. Update NEXT_SESSION_NOTES.md with results
2. Clean up redundant MCP docs
3. Begin event stream integration
4. Implement session-based tools
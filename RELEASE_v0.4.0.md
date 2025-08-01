# ASCOM MCP Server v0.4.0 Release Notes

## Overview
This release implements proper IoT device patterns, removing the automatic discovery requirement and enabling instant connections to devices. Major architectural improvement aligned with how smart home devices actually work.

## 🚀 Breaking Changes

### Discovery No Longer Automatic
- **Removed**: Implicit discovery requirement before connection
- **Removed**: "Run discovery first" error pattern  
- **Removed**: `ASCOM_SKIP_UDP_DISCOVERY` environment variable (no longer needed)
- **Impact**: Discovery only runs when explicitly requested

## ✨ New Features

### Direct Connection Strings
Connect to any device without configuration:
```bash
telescope_connect device_id="seestar@192.168.1.100:5555"
telescope_connect device_id="192.168.1.100:4700"  # Uses default name
```

### Smart Device Resolution
Device IDs are resolved from multiple sources in order:
1. Memory cache (currently connected/available)
2. Persistent state (~/.ascom_mcp/devices.json)
3. Direct connection strings (new!)
4. Environment variables (ASCOM_DIRECT_DEVICES)
5. Known devices config

### IoT-Style Workflow
```bash
# First time - like pairing a smart bulb
/mcp ascom discover_ascom_devices

# Every time after - instant connection
/mcp ascom telescope_connect device_id="telescope_1"
```

## 🐛 Bug Fixes

### From v0.3.0
- Fixed async/await runtime errors with alpyca
- Fixed 3+ minute startup delays
- Added device state persistence

### New in v0.4.0  
- Helpful error messages guide users to solutions
- Connection strings parsed correctly
- Device type extracted from device_id intelligently

## 🏗️ Architecture Changes

### DeviceResolver
New class handles flexible device ID resolution:
- Parses connection strings
- Extracts device type from IDs
- Creates DeviceInfo from various sources

### DeviceManager Updates
- `connect_device()` now calls `_resolve_device_id()`
- No forced discovery requirement
- Saves resolved devices to persistent state

## 📚 Documentation

### Updated Guides
- MCP Configuration Guide - Simplified, removed obsolete settings
- New connection method examples
- IoT workflow patterns documented

### Removed Confusion
- No more ASCOM_SKIP_UDP_DISCOVERY
- No more ASCOM_PREPOPULATE_KNOWN
- Clear explanation of when discovery is needed

## 🧪 Testing

### New Tests
- `test_device_resolver.py` - Unit tests for resolution logic
- `test_iot_connection_pattern.py` - Integration tests for workflows
- Tests verify no automatic discovery

### Test Coverage
- 37 unit tests passing
- New integration tests for IoT patterns
- Existing discovery tests still work

## 🔧 Configuration

### Minimal Setup
```json
{
  "mcpServers": {
    "ascom": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "ascom_mcp.server"],
      "env": {
        "ASCOM_DIRECT_DEVICES": "telescope_1:localhost:5555:Seestar S50"
      }
    }
  }
}
```

### Or Even Simpler
No configuration needed - use connection strings!

## 🎯 Migration Guide

### From v0.3.x

1. **Remove from config**:
   - `ASCOM_SKIP_UDP_DISCOVERY`
   - `ASCOM_PREPOPULATE_KNOWN`

2. **Update connection code**:
   ```bash
   # Old way (required discovery)
   discover_ascom_devices
   telescope_connect device_id="telescope_1"
   
   # New way (direct connection)
   telescope_connect device_id="seestar@192.168.1.100:5555"
   ```

3. **Devices persist** - Previously discovered devices still work

## 🚀 Performance

- **Connection time**: Instant (no discovery wait)
- **Startup time**: < 1 second (was 3+ minutes)
- **Discovery**: Only when explicitly requested

## 📦 Dependencies

No new dependencies. Lighter and faster!

## 🎉 User Experience

Before: "Why do I have to wait 3 minutes every time?"
After: "It just connects like my smart home devices!"

## Next Steps

- Event stream integration for real-time updates
- Session-based observation workflows
- Stellarium telescope control
- Natural language target resolution

## Contributors

- IoT pattern implementation and architectural improvements
- Smart device resolution system
- Comprehensive test coverage
- User-friendly error messages
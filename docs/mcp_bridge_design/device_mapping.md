# ASCOM to MCP Device Mapping

## Overview

This document defines how ASCOM device types and their methods map to MCP tools, ensuring comprehensive coverage while providing an intuitive AI interface.

## Mapping Philosophy

1. **Simplify Complexity** - Group related ASCOM methods into logical MCP tools
2. **Natural Language** - Use terms AI and users understand
3. **Safety First** - Add guardrails not present in raw ASCOM
4. **Value Add** - Provide composite operations beyond basic ASCOM

## Device Type Mappings

### 1. Telescope → `telescope_*` tools

| ASCOM Method | MCP Tool | Description |
|--------------|-----------|-------------|
| `Connected` | `telescope_connect` | Establish connection |
| `SlewToCoordinates` | `telescope_goto` | Go to RA/Dec coordinates |
| `SlewToTarget` | `telescope_goto_target` | Go to named object |
| `AbortSlew` | `telescope_stop` | Emergency stop |
| `Park/Unpark` | `telescope_park` | Safe parking |
| `RightAscension/Declination` | `telescope_get_position` | Current pointing |
| `Tracking` | `telescope_set_tracking` | Sidereal tracking |
| `MoveAxis` | `telescope_nudge` | Fine adjustments |

**Composite Tools:**
- `telescope_goto_brightest` - AI selects optimal target
- `telescope_center_object` - Plate solve and recenter
- `telescope_track_satellite` - ISS/satellite tracking

### 2. Camera → `camera_*` tools

| ASCOM Method | MCP Tool | Description |
|--------------|-----------|-------------|
| `StartExposure` | `camera_capture` | Single exposure |
| `StopExposure` | `camera_abort` | Cancel capture |
| `ImageArray` | `camera_download` | Retrieve image |
| `BinX/BinY` | `camera_set_binning` | Pixel binning |
| `SetCCDTemperature` | `camera_set_cooling` | Cooling control |
| `Gain` | `camera_set_gain` | Sensor gain |

**Composite Tools:**
- `camera_capture_sequence` - Multiple exposures
- `camera_capture_mosaic` - Multi-panel image
- `camera_capture_hdr` - Bracketed exposures
- `camera_live_stack` - Real-time stacking

### 3. Focuser → `focus_*` tools

| ASCOM Method | MCP Tool | Description |
|--------------|-----------|-------------|
| `Move` | `focus_move_to` | Absolute position |
| `Position` | `focus_get_position` | Current position |
| `IsMoving` | `focus_status` | Movement status |
| `Temperature` | `focus_get_temperature` | Temperature compensation |

**Composite Tools:**
- `focus_autofocus` - Automatic focusing routine
- `focus_temperature_compensate` - Adjust for temperature
- `focus_find_stars` - Move to star focus

### 4. FilterWheel → `filter_*` tools

| ASCOM Method | MCP Tool | Description |
|--------------|-----------|-------------|
| `Position` | `filter_set` | Select filter |
| `Names` | `filter_list` | Available filters |

**Composite Tools:**
- `filter_capture_lrgb` - Full color sequence
- `filter_capture_narrowband` - Ha/OIII/SII sequence

### 5. Mount-Specific Tools

**Composite Tools:**
- `mount_polar_align` - Polar alignment routine
- `mount_model_build` - Pointing model creation
- `mount_backlash_measure` - Mechanical testing

### 6. Observatory → `observatory_*` tools

| ASCOM Devices | MCP Tool | Description |
|--------------|-----------|-------------|
| Dome | `observatory_open_dome` | Dome control |
| SafetyMonitor | `observatory_check_safety` | Weather/safety |
| Switch | `observatory_power_control` | Equipment power |
| ObservingConditions | `observatory_get_conditions` | Weather data |

**Composite Tools:**
- `observatory_startup` - Full startup sequence
- `observatory_shutdown` - Safe shutdown
- `observatory_weather_decision` - AI weather analysis

## Tool Naming Conventions

1. **Device Prefix**: `telescope_`, `camera_`, `focus_`, etc.
2. **Action Verb**: `get_`, `set_`, `capture_`, `move_`
3. **Clear Object**: What is being acted upon
4. **Optional Qualifier**: `_sequence`, `_auto`, `_smart`

Examples:
- ✅ `telescope_goto_object`
- ✅ `camera_capture_sequence`
- ❌ `slew_ra_dec` (unclear device)
- ❌ `take_picture` (too casual)

## Parameter Standardization

### Coordinates
```typescript
// Always use J2000 epoch
interface Coordinates {
  ra: number;  // Hours (0-24)
  dec: number; // Degrees (-90 to +90)
  epoch?: "J2000" | "JNOW"; // Default J2000
}
```

### Time
```typescript
// ISO 8601 format
interface TimeParam {
  time: string; // "2025-07-30T12:00:00Z"
  timezone?: string; // Default UTC
}
```

### Units
- **Angles**: Degrees (not radians)
- **Time**: Seconds (not milliseconds)
- **Temperature**: Celsius (not Fahrenheit)
- **Distance**: Millimeters for focus

## Error Response Mapping

```typescript
interface MCPError {
  code: string;
  message: string;
  details?: {
    ascom_code?: number;
    device?: string;
    operation?: string;
  };
}
```

Example:
```json
{
  "code": "DeviceNotReady",
  "message": "Camera is still cooling to target temperature",
  "details": {
    "ascom_code": 0x407,
    "device": "ASI2600MM",
    "operation": "StartExposure"
  }
}
```

## State Management

### Device States in MCP

1. **Discovered** - Found via network scan
2. **Connected** - ASCOM connection established
3. **Ready** - Can accept commands
4. **Busy** - Operation in progress
5. **Error** - Requires intervention
6. **Disconnected** - No connection

### State Transitions
```
Discovered → Connected → Ready ⟷ Busy
                ↓           ↓       ↓
            Disconnected ← Error ←──┘
```

## Multi-Device Coordination

### Tool Naming for Multiple Devices
```typescript
// When multiple devices of same type exist
telescope_goto(device_id?: string, ...params)

// Default device selection
1. Use specified device_id
2. Use first connected device
3. Return error if ambiguous
```

### Coordination Tools
- `system_connect_all` - Connect all discovered devices
- `system_status` - Combined status report
- `system_emergency_stop` - Stop all devices

## Performance Optimizations

Based on ASCOM patterns and Seestar findings:

1. **Batch Operations**
   - Group related commands
   - Single tool for complex sequences

2. **Caching Strategy**
   - Device capabilities (permanent)
   - Filter names (session)
   - Current position (short TTL)

3. **Async Handling**
   - Long exposures
   - Telescope slews
   - Temperature changes

## Future Mappings

As ASCOM evolves, new mappings may include:
- Spectrograph control
- Adaptive optics
- All-sky cameras
- Weather stations
- Power distribution

---

This mapping ensures comprehensive ASCOM device control while providing an intuitive interface for AI assistants.
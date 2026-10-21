# Seestar S50 Mode Operations Guide

## Overview

The Seestar S50 supports four distinct viewing modes, each with unique requirements, safety considerations, and operational patterns. This guide documents real-world usage aligned with our test workflows.

## Viewing Modes

### 🏙️ Scenery Mode - Terrestrial Viewing

**Purpose**: Landscape, wildlife, and terrestrial observation  
**Tracking**: Disabled (mount stationary)  
**Focus**: Manual or preset for infinity  
**Safety**: No special requirements

```python
# Workflow
telescope_custom_action(device_id="telescope_1",
    action="method_sync",
    parameters='{"method": "iscope_start_view", "params": {"mode": "scenery"}}')

# Key operations
- Disable tracking before entering mode
- Use speed_move for smooth panning
- Focus typically at infinity for landscapes
- No exposure time limits
```

### ⭐ Star Mode - Deep Sky Objects

**Purpose**: Galaxies, nebulae, star clusters  
**Tracking**: Sidereal rate (follows stars)  
**Focus**: Auto-focus on stars  
**Safety**: Dark sky preferred

```python
# Workflow
telescope_custom_action(device_id="telescope_1",
    action="method_sync",
    parameters='{"method": "iscope_start_view", "params": {"mode": "star"}}')

# Key operations
- Initialize with location for accurate tracking
- Enable sidereal tracking
- Use goto for object positioning
- Long exposures (10-30 seconds typical)
- Stack multiple frames for deep sky
```

### 🌙 Moon Mode - Lunar Observation

**Purpose**: Lunar surface details  
**Tracking**: Lunar rate (slightly different from sidereal)  
**Focus**: Specific for moon distance  
**Safety**: No special requirements

```python
# Workflow
telescope_custom_action(device_id="telescope_1",
    action="method_sync",
    parameters='{"method": "iscope_start_view", "params": {"mode": "moon"}}')

# Key operations
- Enable lunar tracking rate
- Short exposures (1-100ms)
- High contrast settings
- Automatic brightness adjustment
```

### ☀️ Sun Mode - Solar Observation

**Purpose**: Solar features (with proper filter!)  
**Tracking**: Solar rate  
**Focus**: Solar-specific  
**Safety**: ⚠️ **CRITICAL - REQUIRES SOLAR FILTER**

```python
# SAFETY CRITICAL - NEVER USE WITHOUT PROPER SOLAR FILTER
telescope_custom_action(device_id="telescope_1",
    action="method_sync",
    parameters='{"method": "iscope_start_view", "params": {"mode": "sun"}}')

# Safety requirements
- MUST have proper solar filter installed
- Verify filter before EVERY session
- Use only during daytime
- Minimal exposures (1-10ms max)
- Never remove filter while pointed at sun
```

## Mode Transition Rules

### Valid Transitions
- Any mode → Stop View → Any mode
- Scenery ↔ Star (via stop)
- Moon ↔ Star (tracking adjustment)
- Sun → Any (with safety checks)

### Invalid Transitions
- Direct mode switches without stop
- Sun mode without filter verification
- Tracking changes mid-exposure

## Operational Patterns by Mode

### Movement Commands

**Scenery Mode**
```python
# Smooth panning for landscapes
scope_speed_move(speed=200, angle=90, dur_sec=5)  # Slow pan east
```

**Star/Moon Mode**
```python
# Fine adjustments only
scope_speed_move(speed=50, angle=0, dur_sec=1)   # Tiny nudge up
```

**Sun Mode**
```python
# Automated tracking only - no manual moves during observation
```

### Focus Settings

| Mode | Focus Type | Typical Setting |
|------|-----------|----------------|
| Scenery | Manual | Infinity or hyperfocal |
| Star | Auto | Star-based AF |
| Moon | Semi-auto | Lunar contrast AF |
| Sun | Preset | Solar filter preset |

### Exposure Guidelines

| Mode | Min Exposure | Max Exposure | Typical |
|------|-------------|-------------|---------|
| Scenery | 1ms | No limit | 1/60s |
| Star | 100ms | 30s | 10s |
| Moon | 1ms | 1s | 10ms |
| Sun | 0.1ms | 10ms | 1ms |

## State Machine Validation

Each mode follows a specific state progression:

```
1. Idle State
   ↓
2. Mode Initialization
   ↓
3. Configuration (tracking, focus, exposure)
   ↓
4. Ready State
   ↓
5. Active Operations
   ↓
6. Cleanup/Stop
   ↓
7. Return to Idle
```

## Event Monitoring

Expected events by mode:

### Scenery Mode
- `ViewChanged` - Mode activated
- `MoveComplete` - After each pan/tilt
- `BalanceSensor` - Level status

### Star Mode
- `GotoComplete` - Target reached
- `TrackingStarted` - Sidereal tracking active
- `ExposureComplete` - Frame captured
- `StackProgress` - Multi-frame progress

### Moon Mode
- `GotoComplete` - Moon centered
- `TrackingAdjusted` - Lunar rate set
- `BrightnessAdjusted` - Auto-exposure

### Sun Mode
- `SafetyCheck` - Filter verified
- `TrackingStarted` - Solar rate
- `ExposureWarning` - If too long

## Testing Workflows

Our test suite validates each mode's:
1. **Safety checks** - Especially critical for sun mode
2. **State transitions** - Proper initialization and cleanup
3. **Tracking behavior** - Mode-appropriate rates
4. **Movement patterns** - Suitable for each mode
5. **Event generation** - Expected events fired
6. **Error handling** - Invalid operations blocked

## Best Practices

### General
- Always initialize telescope with location
- Check battery before long sessions
- Verify storage space for imaging
- Monitor temperature in extreme conditions

### Mode-Specific
- **Scenery**: Level mount for panoramas
- **Star**: Polar align for best tracking
- **Moon**: Use high frame rate for lucky imaging
- **Sun**: ALWAYS verify filter, never trust automation

### Safety First
- Sun mode requires physical filter verification
- Never bypass safety checks
- Park telescope when unattended
- Cover optics in daylight (except sun mode with filter)

## Troubleshooting

### Mode Won't Activate
1. Stop current view first
2. Disable conflicting tracking
3. Check prerequisites (time, location)

### Tracking Issues
1. Verify location settings
2. Check mount balance
3. Confirm appropriate tracking rate

### Focus Problems
1. Mode-specific focus required
2. Temperature changes affect focus
3. Use appropriate focus method per mode

## Integration with MCP

Each workflow test validates:
- Proper MCP command sequences
- Parameter validation prevents errors
- Event streaming captures mode changes
- Visual feedback tools work per mode
- Safety interlocks function correctly

This ensures our MCP bridge accurately reflects real Seestar operations across all viewing modes.
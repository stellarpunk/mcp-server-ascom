# Seestar SDK Guide

The v0.5.0 release includes a comprehensive Python SDK for type-safe telescope control with visual feedback.

## Overview

The SDK provides:
- **Type Safety**: Pydantic models prevent parameter errors
- **Visual Feedback**: See what the telescope sees
- **Service Organization**: Logical grouping of functionality
- **Async Support**: Non-blocking operations

## Installation

The SDK is included with mcp-server-ascom v0.5.0+:

```bash
pip install mcp-server-ascom>=0.5.0
```

## Basic Usage

```python
from ascom_mcp.sdk import SeestarClient

async def main():
    # Connect to telescope
    async with SeestarClient("seestar.local") as client:
        # Initialize (REQUIRED!)
        await client.initialize(
            latitude=40.7128,
            longitude=-74.0060
        )
        
        # Get visual feedback
        status = await client.telescope.where_am_i()
        print(f"Pointing at: RA={status.ra}, Dec={status.dec}")
        
        # Start scenery mode
        await client.viewing.start(mode="scenery")
        
        # Capture a frame
        frame = await client.imaging.capture_frame()
        with open("view.jpg", "wb") as f:
            f.write(frame)
```

## Service Reference

### TelescopeService

Movement and positioning with visual feedback:

```python
# Basic movement
await client.telescope.goto(ra=10.5, dec=41.2)
await client.telescope.move_direction("north", duration=3)

# With visual feedback
preview = await client.telescope.goto_with_preview(ra=10.5, dec=41.2)
# Returns current position, target, movement delta, and preview image

# Quick look in a direction
frame = await client.telescope.quick_look("east", duration=2)

# Tracking control (Error 207 safe!)
await client.telescope.set_tracking(enabled=True)

# Presets
await client.telescope.goto_preset("manhattan_skyline")

# Where am I?
status = await client.telescope.where_am_i()
# Returns position + preview image + tracking state
```

### ViewingService  

Control observation modes:

```python
# Start different modes
await client.viewing.start(mode="star")
await client.viewing.start(mode="scenery")  # For terrestrial
await client.viewing.start(mode="moon")

# With target
await client.viewing.start(mode="star", target_name="M31")

# Specialized helpers
await client.viewing.start_scenery_mode()  # Optimized for landscape
await client.viewing.start_solar_mode()     # With safety checks

# Status
status = await client.viewing.get_status()
print(f"Mode: {status.mode}, Stacking: {status.stacking}")
```

### ImagingService

Capture and manage images:

```python
# Simple frame capture
jpeg_bytes = await client.imaging.capture_frame()

# With metadata
frame = await client.imaging.capture_frame_with_metadata()
print(f"Captured at {frame.timestamp}, {frame.size_kb:.1f}KB")
frame.save("capture.jpg")

# Stacking
await client.imaging.start_stacking("Orion Nebula", mode="star")
info = await client.imaging.get_stacking_info()
print(f"Stacked {info.stack_count} frames")

# Multi-direction preview
previews = await client.imaging.capture_preview_grid(
    directions=["north", "east", "south", "west"]
)
# Returns dict with frame for each direction
```

### StreamingService

Live video feeds:

```python
# Get MJPEG URL
mjpeg_url = client.streaming.get_mjpeg_url()
print(f"Open in browser: {mjpeg_url}")

# Start/stop streaming
await client.streaming.start_streaming()
status = await client.streaming.get_status()

# Stream frames programmatically
async for frame in client.streaming.stream_frames():
    # Process each JPEG frame
    process_frame(frame)
    
# Record video segment
frames = await client.streaming.capture_video_segment(
    duration_seconds=10,
    output_file="capture.avi"
)
```

### FocusService

Focus and filter control:

```python
# Manual focus
await client.focus.set_position(1850)  # Good for stars
await client.focus.set_position(1250)  # Manhattan skyline (~2mi)

# Auto focus
await client.focus.auto_focus()

# Focus helpers
await client.focus.focus_for_distance("stars")
await client.focus.focus_for_distance("terrestrial")

# Filter wheel
await client.focus.set_filter(0)  # Clear
await client.focus.set_filter(2)  # Light pollution
await client.focus.set_filter_by_name("lp")
```

### StatusService

Device information:

```python
# Overall state
state = await client.status.get_device_state()
print(f"Battery: {state.battery_level}%")
print(f"Temperature: {state.temperature_celsius}°C")

# Detailed status
full_status = await client.status.get_detailed_status()
# Returns device, telescope, viewing, focus, streaming info

# Readiness checks
ready = await client.status.check_ready_for_operation()
if not ready["temperature_ok"]:
    print("Warning: Temperature out of range!")
```

## Error Handling

The SDK provides clear error messages:

```python
from ascom_mcp.sdk.models.responses import SeestarResponse

try:
    await client.telescope.set_tracking(enabled=True)
except Exception as e:
    print(f"Error: {e}")
    
# Or check response directly
response = await client.execute_action("method_sync", {...})
if not response.success:
    print(f"Failed: {response.error_message}")
    # Error 207: Parameter format error
    # Error 203: Equipment is moving
```

## Visual Feedback Patterns

### Safety Preview
```python
# Before making a large movement
preview = await client.telescope.goto_with_preview(ra, dec)
if preview["safety_check"]["large_movement"]:
    # Show user the preview
    display_image(preview["current_view"])
    if confirm("Proceed with movement?"):
        await client.telescope.goto(ra, dec)
```

### Continuous Monitoring
```python
# Watch what telescope sees
async def monitor_view():
    mjpeg_url = client.streaming.get_mjpeg_url()
    async for frame in client.streaming.stream_frames():
        # Update UI with latest frame
        update_preview(frame)
        await asyncio.sleep(0.1)  # ~10 FPS
```

### Landmark Navigation
```python
# For terrestrial viewing
await client.viewing.start_scenery_mode()
await client.telescope.goto_preset("empire_state_building")
await client.focus.focus_for_distance("terrestrial")
frame = await client.imaging.capture_frame()
```

## Best Practices

1. **Always Initialize**: Call `client.initialize()` before operations
2. **Use Context Manager**: `async with SeestarClient()` ensures cleanup
3. **Check Ready State**: Use `client.is_ready` before operations
4. **Handle Movement**: Check if telescope is slewing before new commands
5. **Visual Confirmation**: Use preview methods for safety

## Integration with MCP

The SDK is used internally by MCP tools:

```python
# In Claude:
/mcp ascom telescope_preview device_id="telescope_1"
# Internally uses: client.imaging.capture_frame()

/mcp ascom telescope_where_am_i device_id="telescope_1"  
# Internally uses: client.telescope.where_am_i()
```

## Future: SpatialLM Integration

The SDK is ready for spatial AI workflows:

```python
# Capture landmark
await client.viewing.start_scenery_mode()
frame = await client.imaging.capture_frame()

# Process with SpatialLM
spatial_features = spatialLM.analyze(frame)
nearby_landmarks = spatialLM.identify_landmarks(spatial_features)

# Navigate to identified landmark
if "brooklyn_bridge" in nearby_landmarks:
    await client.telescope.goto_preset("brooklyn_bridge")
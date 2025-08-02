# Seestar S50 Integration Guide

This guide explains how to use the ASCOM MCP Server with [seestar_alp](https://github.com/smart-underworld/seestar_alp).

## Architecture

```
AI Assistant ↔ MCP Server ↔ seestar_alp ↔ Seestar S50
   (Claude)     (This repo)   (ASCOM server)  (Hardware)
```

## Quick Start

1. **Start seestar_alp** (on same network as Seestar):
   ```bash
   cd /path/to/seestar_alp
   source venv/bin/activate
   python root_app.py
   ```

2. **Start MCP Server**:
   ```bash
   cd /path/to/mcp-server-ascom
   mcp-server-ascom
   ```

3. **In Claude**: Connect directly or discover
   ```
   telescope_connect device_id="telescope_1"
   # Or: telescope_connect device_id="seestar@seestar.local:5555"
   ```

## Visual Feedback Examples (v0.5.0+)

### See What Telescope Sees
```
User: "Where is my telescope pointing?"
AI: [Shows preview image]
    Currently at: RA 5h 35m, Dec -5° 27'
    Tracking: Enabled
    Mode: Star
```

### Live Streaming
```
User: "Start live view from telescope"
AI: Starting video stream...
    MJPEG URL: http://seestar.local:5432/img/live_stacking
    Open this URL in your browser for live view
```

### Scenery Mode (Terrestrial)
```
User: "Switch to scenery mode and look at the city skyline"
AI: Switching to scenery mode...
    [Shows preview of current view]
    Ready for terrestrial observation
```

## Example Sessions

### Astronomy Session
```
User: "Connect to my Seestar and show me what it sees"
AI: Connected to Seestar S50
    [Shows current view image]
    Currently pointing at: RA 12h 30m, Dec +45° 15'

User: "Point at the Orion Nebula" 
AI: Slewing to M42...
    [Shows preview after movement]
    Target acquired at RA: 5h 35m 17s, Dec: -5° 27' 00"
```

### Terrestrial Session
```
User: "Start scenery mode for viewing Manhattan"
AI: Starting scenery mode...
    [Shows current view]
    
User: "Go to the Empire State Building preset"
AI: Moving to preset...
    [Shows view of Empire State Building]
    Focus adjusted for ~2 mile distance
```

## Popular Seestar Targets

### Bright Objects (Focus: ~1900)
- **Moon**: Always visible when up, great for testing
- **Jupiter**: Shows cloud bands, 4 moons visible
- **Saturn**: Ring system visible
- **Venus**: Phases visible at high magnification

### Deep Sky Objects (Focus: 1950-2000)
- **M42** (Orion Nebula): Best winter target, very bright
- **M31** (Andromeda): Large galaxy, needs dark skies  
- **M45** (Pleiades): Beautiful star cluster
- **M13** (Hercules Cluster): Bright globular cluster
- **M51** (Whirlpool Galaxy): Spiral structure visible

### ⚠️ WARNING: Solar Observation
**NEVER** point at the Sun without proper solar filter. The Seestar S50 does NOT have built-in solar filtering. Permanent damage to equipment and eyesight can occur.

## Focus Guidelines

| Target Type | Focus Position | Notes |
|------------|---------------|-------|
| Stars/DSO | 1950-2000 | Temperature dependent |
| Moon | 1900-1950 | Adjust for phase |
| Planets | 1850-1900 | Jupiter/Saturn optimal |

## Troubleshooting

### Device Not Found
- Ensure seestar_alp is running: `curl http://localhost:5555/api/v1/telescope/0/connected`
- Check firewall allows port 5555
- Verify Seestar is powered on and connected to WiFi

### Slewing Issues  
- Seestar movement is reversed: North command moves view south
- Allow 10-15 seconds for long slews
- Park telescope before shutdown

### Focus Problems
- Temperature changes require refocus
- Use `autofocus` command when available
- Manual focus: increase for closer, decrease for infinity

## Advanced Features

### Live Stacking
```
User: "Start live stacking on M42 for 5 minutes"
AI: Beginning live stack sequence...
    Exposure: 10s x 30 frames
    Stacking in progress...
```

### Plate Solving
```
User: "Where am I pointing?"
AI: Capturing image for plate solve...
    Current position: RA 5h 32m, Dec -5° 15'
    Nearest object: M42 (2.5° away)
```
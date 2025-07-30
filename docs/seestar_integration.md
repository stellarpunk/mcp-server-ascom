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

3. **In Claude**: "Discover my telescope"

## Example Astronomy Session

```
User: "Connect to my Seestar"
AI: Discovering devices... Found Seestar S50 at seestar.local
    Connected successfully

User: "Show me the Moon"
AI: Calculating current Moon position...
    Slewing to Moon (Alt: 45°, Az: 220°)
    
User: "Point at the Orion Nebula"
AI: Slewing to M42 (RA: 5h 35m 17s, Dec: -5° 27' 00")
    Target acquired

User: "Take a 30 second exposure of the Andromeda Galaxy"  
AI: Slewing to M31 (RA: 0h 42m 44s, Dec: +41° 16' 09")
    Capturing 30s light frame...
    Image complete
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
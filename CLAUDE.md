# CLAUDE.md - ASCOM MCP Server

Bridge ASCOM devices to Claude Code via MCP.

## Quick Start
```bash
# Dev
source .venv/bin/activate && python -m ascom_mcp

# Test  
pytest -v --cov=ascom_mcp

# Release
python scripts/release.py --version X.Y.Z
```

## Key Facts
- Version: 0.3.0 (FastMCP 2.0)
- Primary device: Seestar S50
- Known issue: MCP Inspector protocol error

## Architecture
```
Claude → MCP → ASCOM Server → Device
```

## Development Tips
- Test with simulator first
- Use Task tool for complex operations
- Monitor: `python -m ascom_mcp 2>&1 | tee mcp.log`
- Always call `ensure_initialized()` before device access

## Safety Critical
```python
# Initialize before use
await connect("Telescope_1")
await telescope_custom_action("Telescope_1", "action_start_up_sequence", 
    {"lat": 40.745, "lon": -74.0256, "move_arm": True})

# Solar mode requires explicit change
await telescope_custom_action("Telescope_1", "method_sync",
    {"method": "iscope_start_view", "params": {"mode": "sun"}})
```
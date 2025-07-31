# CLAUDE.md - ASCOM MCP Server

Bridge ASCOM devices to Claude Code via MCP.

## Environment Setup

**Use project venv. Always.**

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Verify
which python  # Must show .venv path
```

## Quick Start
```bash
# Dev
source .venv/bin/activate && python -m ascom_mcp

# Test (all 37 unit tests pass)
pytest tests/unit/ -v

# With simulator
export ASCOM_SIMULATOR_DEVICES="localhost:4700:seestar_simulator"
pytest tests/ -v

# Release
python scripts/release.py --version X.Y.Z
```

## Key Facts
- Version: 0.3.0 (FastMCP 2.0)
- Primary device: Seestar S50
- All tools use Context parameter (first arg)
- ToolError for recoverable errors
- Simulator auto-detection on port 4700

## Architecture
```
Claude → MCP → ASCOM Server → Device
         ↓
    Context, ToolError, Logging
```

## Development Tips
- Test with simulator first (90% of tests)
- Real hardware for validation (10%)
- Use alpaca mocks in unit tests
- Monitor: `multitail -ci green mcp.log -ci yellow seestar.log`
- Test modes: `ASCOM_TEST_MODE=simulator` (default) or `hardware`

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

## Documentation

- **Development**: `docs/development.md` - Environment, architecture, troubleshooting
- **Testing**: `tests/README.md` - Comprehensive testing guide
- **Strategy**: `tests/TESTING_STRATEGY.md` - Simulator vs hardware testing
- **Seestar**: `../seestar_alp/CLAUDE.md` - Telescope control details
# Next Session Plan

## Current Status ✅

### What's Working
- **v0.4.0 Published to PyPI** with device pre-population fix
- **Claude Code configured** to use local development version
- **No discovery needed!** Devices auto-populate from `ASCOM_DIRECT_DEVICES`
- **Event streaming infrastructure** implemented and ready
- **Both telescopes available:**
  - `telescope_1`: Seestar S50 at localhost:5555
  - `telescope_99`: Simulator at localhost:4700

### Recent Accomplishments
- Fixed 2-minute discovery timeout issue
- Implemented event streaming with WebSocket support
- Created event resources and subscription tools
- Published v0.4.0 with all fixes

## Next Session Goals 🎯

### 1. Test Real Hardware
- Connect to physical Seestar S50
- Test event streaming with real telescope movements
- Verify all custom actions work

### 2. Add Hot-Reload Development Mode
```python
# Option A: HTTP transport with uvicorn
uvicorn ascom_mcp.server_fastmcp:app --reload --port 8000

# Option B: File watcher with auto-restart
python -m ascom_mcp --dev --watch
```

### 3. Set Up Python Invoke Tasks
Create `tasks.py` for common operations:
```python
from invoke import task

@task
def dev(c):
    """Run MCP server in development mode with hot-reload"""
    c.run("uvicorn ascom_mcp.server_fastmcp:app --reload")

@task
def test(c, unit=False, mcp=False):
    """Run tests"""
    if unit:
        c.run("pytest tests/unit/")
    elif mcp:
        c.run("pytest tests/mcp/")
    else:
        c.run("pytest tests/")

@task
def start_seestar(c):
    """Start seestar_alp and simulator"""
    c.run("cd ../seestar_alp && python root_app.py &")
    c.run("python src/seestar_simulator.py &")

@task
def publish(c, version):
    """Build and publish to PyPI"""
    c.run(f"bump2version --new-version {version} patch")
    c.run("python -m build")
    c.run("python -m twine upload dist/*")

@task
def connect(c):
    """Quick test connection to Seestar"""
    c.run("python examples/workflows/complete_telescope_session.py")
```

### 4. Priority Todo Items
1. **Test event streaming with real Seestar** (high priority)
2. **Implement hot-reload for development** (high priority)
3. **Add session-based observation workflows** (medium priority)
4. **Streamable HTTP support for real-time updates** (medium priority)
5. **Stellarium integration** (medium priority)

## Development Setup Checklist

### Before Starting
```bash
# 1. Ensure venv has dependencies
cd /Users/jschulle/construction-mcp/mcp-server-ascom
uv pip install -e .

# 2. Start Seestar services
cd /Users/jschulle/construction-mcp/seestar_alp
python root_app.py

# 3. Start simulator (optional)
python src/seestar_simulator.py
```

### Claude Code Config (Development)
Already configured to use local development version:
- Command: `/Users/jschulle/construction-mcp/mcp-server-ascom/.venv/bin/python`
- Auto-populates devices from `ASCOM_DIRECT_DEVICES`
- No discovery needed!

## Quick Test Commands

```bash
# Test connection (no discovery needed!)
/mcp ascom telescope_connect device_id="telescope_1"

# Get telescope position
/mcp ascom telescope_get_position device_id="telescope_1"

# Subscribe to events
/mcp ascom event_subscribe device_id="telescope_1" event_types='["status", "progress"]'

# Start observation
/mcp ascom telescope_custom_action device_id="telescope_1" action="method_sync" parameters='{"method": "iscope_start_view", "params": {"mode": "star"}}'
```

## Architecture Decisions

### Why Local Development Mode?
- Instant feedback on code changes
- No publish/download cycle
- Direct debugging access
- Faster iteration

### Why Invoke?
- Consistent task interface
- Composable commands
- Built-in help system
- Python-native (no shell scripts)

### Hot-Reload Strategy
1. **Phase 1**: Basic file watching with process restart
2. **Phase 2**: HTTP transport option for uvicorn --reload
3. **Phase 3**: Selective module reloading for tools

## Success Metrics
- [ ] Can modify code and test without restarting Claude Code
- [ ] Event streaming works with real telescope
- [ ] All invoke tasks functional
- [ ] Development cycle under 10 seconds
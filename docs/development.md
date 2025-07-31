# Development Guide

## Environment Setup

**Use the project's virtual environment. Always.**

```bash
# Install UV (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Verify
which python
# Must show: .../mcp-server-ascom/.venv/bin/python
```

Wrong Python? Tests fail. Every time.

### Options

1. **UV + venv**: Fast. Local. Recommended.
2. **DevContainer**: Full isolation. Slower.
3. **direnv**: Auto-activation. Install → `direnv allow`.

## Architecture

ASCOM MCP Server uses **FastMCP**:

- Decorators: `@mcp.tool()`, `@mcp.resource()`  
- Built-in lifecycle management
- Production defaults
- 300 lines vs 600 (low-level API)

## Key Design Decisions

### 1. FastMCP vs Low-Level API

Why FastMCP:

- 300 lines vs 600
- Built-in validation
- Recommended by MCP team
- Protocol compliance automatic

### 2. Structured Logging

MCP requires stderr logging. We use JSON:

```python
from ascom_mcp.logging import StructuredLogger

logger = StructuredLogger("ascom.telescope")
logger.info("telescope_connected", device_id="telescope_0", ra=5.5)
```

Works with OpenTelemetry, Grafana, DataDog.

### 3. Testing Strategy

Three layers. Each serves a purpose.

1. **Unit** (90%): Business logic. Mocked devices. Fast.
2. **Integration** (9%): MCP protocol. FastMCP patterns.
3. **E2E** (1%): Real workflows. Simulator or hardware.

## Common Pitfalls

1. **Never log to stdout** - Breaks protocol
2. **Use FastMCP** - Not low-level API
3. **Test stdio first** - Catches most issues
4. **Clear UV cache** - `uv cache clean`

## Running Tests

**Activate venv first.**

```bash
source .venv/bin/activate

# All tests
pytest

# By category
pytest tests/unit/           # Mock devices
pytest tests/integration/    # FastMCP protocol
pytest tests/e2e/           # Requires simulator

# Coverage
pytest --cov=ascom_mcp
```

### Test Modes

```bash
# Default: Simulator
export ASCOM_TEST_MODE=simulator

# Hardware tests (careful!)
export ASCOM_TEST_MODE=hardware
pytest -m "not simulator_only"
```

## Debugging

Claude Desktop logs:
```bash
tail -f ~/Library/Logs/Claude/mcp-server-ascom.log
```

Debug mode:
```bash
LOG_LEVEL=DEBUG mcp-server-ascom
```

## Troubleshooting

### Wrong Python
```bash
which python
# Bad:  /usr/bin/python
# Good: .../mcp-server-ascom/.venv/bin/python

# Fix:
source .venv/bin/activate
```

### Import Errors
```bash
# ModuleNotFoundError: No module named 'alpaca'
# Expected in unit tests. They use mocks.

# ModuleNotFoundError: No module named 'pytest'  
# Wrong environment. Activate venv.
```

### Test Discovery Failures
```bash
# Check environment variables
echo $ASCOM_SIMULATOR_DEVICES
# Should show: localhost:4700:seestar_simulator
```
# ASCOM MCP Examples

This directory contains example scripts demonstrating various usage patterns for the ASCOM MCP server.

## Directory Structure

### workflows/
Complete end-to-end workflow examples:
- `complete_telescope_session.py` - Full telescope control flow (discover → connect → control → disconnect)
- `seestar_full_control.py` - Comprehensive Seestar S50 control example

### discovery/
Device discovery examples:
- `simple_discovery.py` - Basic ASCOM device discovery
- `direct_discovery.py` - Direct connection to known devices
- `seestar_discovery.py` - Seestar-specific discovery patterns

## Running Examples

```bash
# Activate virtual environment
source .venv/bin/activate

# Run a workflow example
python examples/workflows/complete_telescope_session.py

# Run discovery
python examples/discovery/simple_discovery.py
```

## Prerequisites

1. Have an ASCOM device or simulator running
2. For Seestar examples, ensure seestar_alp is running:
   ```bash
   cd /path/to/seestar_alp
   python root_app.py
   ```

## Example Output

```
=== MCP End-to-End Test ===

1. Discovering ASCOM devices...
   Found 1 devices:
   - Seestar S50 (Telescope) at localhost:5555

2. Getting info for device: Telescope_1
   Device: Seestar S50
   Type: Telescope
   Status: Not connected

3. Connecting to telescope...
   ✓ Connected successfully!
   Can slew: True
   Can park: True
```
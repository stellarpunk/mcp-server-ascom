#!/bin/bash
# Quick test script for v0.4.0 with real Seestar

echo "=== v0.4.0 Real Seestar Testing ==="
echo

# Set up environment for real hardware
export ASCOM_TEST_MODE=hardware
export ASCOM_DIRECT_DEVICES="telescope_1:seestar.local:5555:Seestar S50"
export LOG_LEVEL=INFO

# Source from .env.real_seestar if exists
if [ -f ".env.real_seestar" ]; then
    echo "Loading .env.real_seestar..."
    set -a
    source .env.real_seestar
    set +a
fi

echo "Configuration:"
echo "  ASCOM_DIRECT_DEVICES: $ASCOM_DIRECT_DEVICES"
echo "  LOG_LEVEL: $LOG_LEVEL"
echo

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found"
    exit 1
fi

# Run v0.4.0 direct connection tests
echo "Testing direct connection features..."
python scripts/test_v0.4_direct_connection.py

# Run integration tests
echo
echo "Running integration tests..."
pytest tests/integration/test_iot_connection_pattern.py -v

# Run hardware-compatible MCP tests
echo
echo "Running MCP tests..."
pytest tests/mcp/ -v -m "not simulator_only"

echo
echo "✅ Testing complete!"
#!/bin/bash
# Start MCP Inspector for ASCOM MCP Server

echo "Starting MCP Inspector for ASCOM MCP Server..."
echo "==========================================="
echo ""
echo "🚀 Open in your browser:"
echo "   http://localhost:6274"
echo ""
echo "📝 In the inspector:"
echo "   1. Click 'discover_ascom_devices' tool"
echo "   2. Set timeout: 5-10 seconds"
echo "   3. Click Execute"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run inspector with our server
DANGEROUSLY_OMIT_AUTH=true mcp-inspector python -m ascom_mcp
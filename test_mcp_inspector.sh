#!/bin/bash
echo "Testing local MCP server with Inspector..."
echo "This will open MCP Inspector to test our server"
echo ""
echo "After it opens, test these commands:"
echo "1. tools/list"
echo "2. tools/call discover_ascom_devices {}"
echo ""
read -p "Press Enter to start..."

# Run with local Python
mcp-inspector python -- -m ascom_mcp
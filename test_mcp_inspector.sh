#!/bin/bash
echo "Testing mcp-server-ascom with MCP Inspector"
echo ""
echo "1. Testing PyPI version with uvx:"
echo "   mcp-inspector uvx mcp-server-ascom"
echo ""
echo "2. Test these tools:"
echo "   - discover_ascom_devices"
echo "   - telescope_connect (with a device_id from discovery)"
echo "   - telescope_goto_object (try 'M42' or 'Orion Nebula')"
echo ""
echo "Starting MCP Inspector..."
mcp-inspector uvx mcp-server-ascom
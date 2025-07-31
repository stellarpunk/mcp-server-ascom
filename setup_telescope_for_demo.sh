#!/bin/bash
# Setup telescope for MCP demo
# This connects seestar_alp to the telescope so our MCP server can control it

echo "=== TELESCOPE SETUP FOR MCP DEMO ==="
echo
echo "This script will:"
echo "1. Connect seestar_alp to the telescope"
echo "2. Verify connection"
echo
echo "Prerequisites:"
echo "- Seestar S50 must be powered on (wait 60-90 seconds after power on)"
echo "- seestar_alp must be running (http://localhost:5555)"
echo

# Check if seestar_alp is running
if ! curl -s "http://localhost:5555/management/v1/description" > /dev/null 2>&1; then
    echo "❌ ERROR: seestar_alp is not running!"
    echo "   Start it with: cd /Users/jschulle/construction-mcp/seestar_alp && python root_app.py"
    exit 1
fi

echo "✓ seestar_alp is running"

# Connect to telescope
echo
echo "Connecting seestar_alp to telescope..."
response=$(curl -s -X PUT "http://localhost:5555/api/v1/telescope/1/connected" \
  -d "Connected=true&ClientID=1&ClientTransactionID=1")

# Check if connection succeeded
error_num=$(echo "$response" | python -c "import sys, json; print(json.load(sys.stdin).get('ErrorNumber', 1))")

if [ "$error_num" -eq 0 ]; then
    echo "✓ Successfully connected to telescope!"
    
    # Verify connection
    connected=$(curl -s "http://localhost:5555/api/v1/telescope/1/connected?ClientID=1&ClientTransactionID=1" | \
      python -c "import sys, json; print(json.load(sys.stdin)['Value'])")
    
    if [ "$connected" = "True" ]; then
        echo "✓ Connection verified"
        echo
        echo "=== TELESCOPE READY FOR MCP DEMO ==="
        echo "You can now run: python seestar_complete_control.py"
    else
        echo "❌ Connection verification failed"
        exit 1
    fi
else
    echo "❌ Failed to connect to telescope"
    echo "   Error: $response"
    echo
    echo "Troubleshooting:"
    echo "1. Is the Seestar S50 powered on?"
    echo "2. Did you wait 60-90 seconds after power on?"
    echo "3. Is the telescope on the same network?"
    exit 1
fi
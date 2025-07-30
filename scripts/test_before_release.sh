#!/bin/bash
# Pre-release test script for ASCOM MCP Server
# This catches the issues that slipped through in v0.2.1 and v0.2.2

set -e  # Exit on error

echo "🔍 ASCOM MCP Server Pre-Release Tests"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "Running: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Test Python module can be imported
echo -e "\n${YELLOW}1. Module Import Tests${NC}"
run_test "Import main module" "python -c 'import ascom_mcp'"
run_test "Import server module" "python -c 'from ascom_mcp.server import create_server, run'"
run_test "Check version" "python -c 'import ascom_mcp; print(ascom_mcp.__version__)'"

# 2. Test CLI entry points
echo -e "\n${YELLOW}2. CLI Entry Point Tests${NC}"
run_test "Module execution" "timeout 2 python -m ascom_mcp --version"
run_test "Help output" "python -m ascom_mcp --help | grep -q 'ASCOM MCP Server'"

# 3. Test server startup (the critical test!)
echo -e "\n${YELLOW}3. Server Startup Test${NC}"
echo "Starting server and sending initialization..."

# Create a test script to send initialization
cat > /tmp/test_init.py << 'EOF'
import subprocess
import json
import time
import sys

# Start server
proc = subprocess.Popen(
    [sys.executable, "-m", "ascom_mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=False
)

try:
    # Send initialization message
    init_msg = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        },
        "id": 1
    }
    
    content = json.dumps(init_msg)
    header = f"Content-Length: {len(content)}\r\n\r\n"
    message = (header + content).encode('utf-8')
    
    proc.stdin.write(message)
    proc.stdin.flush()
    
    # Wait for response
    time.sleep(1)
    
    # Check if process is still running
    if proc.poll() is None:
        proc.terminate()
        print("Server started successfully")
        sys.exit(0)
    else:
        stderr = proc.stderr.read().decode('utf-8')
        if "coroutine" in stderr and "was never awaited" in stderr:
            print("FAILED: Coroutine error detected")
        elif "initialize_fn" in stderr:
            print("FAILED: initialize_fn parameter error")
        elif "initialization_options" in stderr:
            print("FAILED: initialization_options parameter error")
        else:
            print(f"FAILED: {stderr}")
        sys.exit(1)
except Exception as e:
    print(f"FAILED: {e}")
    proc.terminate()
    sys.exit(1)
EOF

run_test "Server initialization" "python /tmp/test_init.py"

# 4. Test with MCP Inspector (if available)
echo -e "\n${YELLOW}4. MCP Inspector Test${NC}"
if command -v mcp-inspector &> /dev/null; then
    echo "Testing with MCP Inspector..."
    
    # Create expect script for MCP Inspector
    cat > /tmp/test_inspector.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 10
spawn mcp-inspector python -- -m ascom_mcp
expect "Connected"
send "tools/list\r"
expect "discover_ascom_devices"
send "exit\r"
expect eof
EOF
    
    if command -v expect &> /dev/null; then
        run_test "MCP Inspector connection" "expect /tmp/test_inspector.exp"
    else
        echo -e "${YELLOW}⚠ Skipping: 'expect' command not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping: MCP Inspector not installed${NC}"
fi

# 5. Test package build
echo -e "\n${YELLOW}5. Package Build Test${NC}"
run_test "Build package" "python -m build --outdir /tmp/test_dist"
run_test "Check wheel exists" "ls /tmp/test_dist/*.whl"
run_test "Check sdist exists" "ls /tmp/test_dist/*.tar.gz"

# 6. Test with uvx (if available)
echo -e "\n${YELLOW}6. UVX Installation Test${NC}"
if command -v uvx &> /dev/null; then
    # Install the local package
    run_test "Install with pip" "pip install /tmp/test_dist/*.whl --force-reinstall"
    run_test "Run installed command" "timeout 2 mcp-server-ascom --version"
else
    echo -e "${YELLOW}⚠ Skipping: uvx not installed${NC}"
fi

# Clean up
rm -f /tmp/test_init.py /tmp/test_inspector.exp
rm -rf /tmp/test_dist

# Summary
echo -e "\n${YELLOW}Test Summary${NC}"
echo "============="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed! Ready for release.${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Do not release!${NC}"
    exit 1
fi
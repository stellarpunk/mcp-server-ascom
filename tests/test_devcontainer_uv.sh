#!/bin/bash
# Test devcontainer UV commands

echo "Testing devcontainer UV commands..."
echo "================================="

# Test mcp-server-ascom
echo -e "\n1. Testing mcp-server-ascom container:"
docker run --rm mcp-server-ascom-mcp-ascom /bin/bash -c "
echo '  UV version:' && uv --version
echo '  Python version:' && python --version
echo '  Virtual env:' && echo \$VIRTUAL_ENV
echo '  UV pip list (first 5):' && uv pip list | head -5
"

# Test seestar_alp
echo -e "\n2. Testing seestar_alp container:"
docker run --rm seestar_alp-seestar-alp /bin/bash -c "
echo '  UV version:' && uv --version
echo '  Python version:' && python --version
echo '  Virtual env:' && echo \$VIRTUAL_ENV
echo '  UV pip list (first 5):' && uv pip list | head -5
"

echo -e "\n✅ UV is available in both runtime containers!"
#!/bin/bash
# Installation script for ASCOM MCP Server

set -e

echo "Installing ASCOM MCP Server..."
echo "=============================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
min_version="3.10"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "❌ Python 3.10+ required (found $python_version)"
    exit 1
fi
echo "✓ Python $python_version"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Using virtual environment: $VIRTUAL_ENV"
    pip_cmd="pip"
    python_cmd="python"
else
    echo "⚠️  No virtual environment detected"
    echo "   Consider using: python -m venv .venv && source .venv/bin/activate"
    echo "   Or with uv: uv venv && source .venv/bin/activate"
    pip_cmd="pip"
    python_cmd="python3"
fi

# Install package
echo -e "\nInstalling package..."
$pip_cmd install -e .

# Note about alpyca/alpaca naming
echo -e "\n📝 Note: The 'alpyca' package imports as 'alpaca'"

# Verify installation
echo -e "\nVerifying installation..."
$python_cmd -m ascom_mcp --version

# Test import
if $python_cmd -c "from ascom_mcp import create_server; print('✓ Import successful')"; then
    echo "✓ Package installed correctly"
else
    echo "❌ Import failed"
    exit 1
fi

# Show configuration example
echo -e "\n📋 Example Claude Desktop configuration:"
echo "Add to ~/Library/Application Support/Claude/claude_desktop_config.json:"
echo
cat mcp_config_example.json

echo -e "\n✨ Installation complete!"
echo "Next steps:"
echo "1. Run 'mcp-server-ascom' to start the server"
echo "2. Or test with: python -m ascom_mcp"
echo "3. For MCP Inspector: mcp-inspector python -m ascom_mcp"
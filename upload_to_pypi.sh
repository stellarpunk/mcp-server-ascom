#!/bin/bash
echo "=== Uploading mcp-server-ascom v0.2.1 to PyPI ==="
echo ""
echo "This will fix the Claude Desktop error!"
echo ""
echo "You'll need your PyPI API token."
echo "Get it from: https://pypi.org/manage/account/token/"
echo ""
read -p "Press Enter to continue..."

export TWINE_USERNAME=__token__
echo "Enter your PyPI API token (starts with pypi-):"
read -s TWINE_PASSWORD
export TWINE_PASSWORD

echo ""
echo "Uploading v0.2.1..."
twine upload dist/mcp_server_ascom-0.2.1*

echo ""
echo "✅ Done! Now let's fix Claude Desktop:"
echo ""
echo "1. Clear uvx cache:"
echo "   rm -rf ~/.local/share/uv/tools/mcp-server-ascom"
echo ""
echo "2. Test new version:"
echo "   uvx --refresh mcp-server-ascom --version"
echo ""
echo "3. Restart Claude Desktop"
echo ""
echo "The error will be gone! 🎉"
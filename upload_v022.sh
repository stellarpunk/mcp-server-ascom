#!/bin/bash
echo "Uploading v0.2.2 to PyPI..."
echo "Enter your PyPI API token:"
read -s PYPI_TOKEN
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$PYPI_TOKEN
twine upload dist/mcp_server_ascom-0.2.2*
echo "Done! Clear uvx cache: rm -rf ~/.local/share/uv/tools/mcp-server-ascom"
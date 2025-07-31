#!/bin/bash
# Check if we're using the correct Python environment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Checking Python Environment..."
echo "================================"

# Check Python location
PYTHON_PATH=$(which python)
echo "Python path: $PYTHON_PATH"

# Check if we're in a venv
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
elif [[ "$PYTHON_PATH" == *".venv"* ]]; then
    echo -e "${GREEN}✅ Using .venv Python${NC}"
else
    echo -e "${RED}❌ Not using virtual environment!${NC}"
    echo -e "${YELLOW}   Run: source .venv/bin/activate${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "Python version: $PYTHON_VERSION"

# Check if mcp-server-ascom is installed in dev mode
if python -c "import ascom_mcp" 2>/dev/null; then
    echo -e "${GREEN}✅ ascom_mcp module found${NC}"
    
    # Check if it's editable install
    if pip show mcp-server-ascom | grep -q "Editable project location"; then
        echo -e "${GREEN}✅ Installed in development mode${NC}"
    else
        echo -e "${YELLOW}⚠️  Not installed in development mode${NC}"
        echo -e "${YELLOW}   Run: make install${NC}"
    fi
else
    echo -e "${RED}❌ ascom_mcp module not found${NC}"
    echo -e "${YELLOW}   Run: make install${NC}"
    exit 1
fi

# Check for global installation
if pip show mcp-server-ascom 2>/dev/null | grep -q "Location.*miniforge\|homebrew"; then
    echo -e "${RED}❌ WARNING: Global installation detected!${NC}"
    echo -e "${YELLOW}   Run: pip uninstall mcp-server-ascom${NC}"
fi

echo ""
echo -e "${GREEN}✅ Environment check complete!${NC}"
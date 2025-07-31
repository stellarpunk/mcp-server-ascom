#!/bin/bash
# Run Playwright E2E tests for mcp-server-ascom

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}🎭 Running Playwright E2E Tests${NC}"
echo -e "${YELLOW}==============================${NC}"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}Error: No virtual environment found${NC}"
    echo "Create with: uv venv"
    exit 1
fi

# Install dependencies if needed
if ! python -c "import playwright" 2>/dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install -r requirements-test.txt
    playwright install chromium
fi

# Run tests
echo -e "\n${YELLOW}Running E2E tests...${NC}"
if pytest tests/e2e -v --tb=short; then
    echo -e "\n${GREEN}✓ All E2E tests passed${NC}"
else
    echo -e "\n${RED}✗ Some E2E tests failed${NC}"
    exit 1
fi
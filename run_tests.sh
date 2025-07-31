#!/bin/bash
# Run tests for ASCOM MCP server

set -e  # Exit on error

echo "=== ASCOM MCP Server Test Suite ==="
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: Not in a virtual environment${NC}"
    echo "Consider activating your virtual environment first"
    echo
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
EXTRA_ARGS="${@:2}"

# Function to run tests
run_tests() {
    local test_pattern=$1
    local description=$2
    
    echo -e "${GREEN}Running $description...${NC}"
    
    if pytest $test_pattern $EXTRA_ARGS; then
        echo -e "${GREEN}✓ $description passed${NC}"
    else
        echo -e "${RED}✗ $description failed${NC}"
        return 1
    fi
    echo
}

# Main test execution
case $TEST_TYPE in
    "unit")
        run_tests "tests/unit -m 'not slow'" "Unit Tests"
        ;;
    
    "integration")
        run_tests "tests/integration -m 'not requires_simulator'" "Integration Tests"
        ;;
    
    "e2e")
        echo -e "${YELLOW}Starting E2E tests (requires services)...${NC}"
        echo "Make sure seestar_alp simulator is available"
        echo
        run_tests "tests/e2e" "End-to-End Tests"
        ;;
    
    "smoke")
        run_tests "-m smoke" "Smoke Tests"
        ;;
    
    "all")
        echo "Running complete test suite..."
        echo
        
        # Run tests in order: unit -> integration -> e2e
        run_tests "tests/unit -m 'not slow'" "Unit Tests" || exit 1
        run_tests "tests/integration -m 'not requires_simulator'" "Integration Tests" || exit 1
        
        echo -e "${YELLOW}Skipping E2E tests (run with './run_tests.sh e2e' when services are ready)${NC}"
        ;;
    
    "coverage")
        echo "Running tests with coverage..."
        pytest --cov=ascom_mcp --cov-report=html --cov-report=term $EXTRA_ARGS
        echo
        echo "Coverage report generated in htmlcov/index.html"
        ;;
    
    "watch")
        echo "Running tests in watch mode..."
        # Requires pytest-watch
        if command -v ptw &> /dev/null; then
            ptw tests/unit tests/integration -- -v
        else
            echo "pytest-watch not installed. Install with: pip install pytest-watch"
            exit 1
        fi
        ;;
    
    *)
        echo "Usage: $0 [unit|integration|e2e|smoke|all|coverage|watch] [extra pytest args]"
        echo
        echo "Examples:"
        echo "  $0                    # Run all tests"
        echo "  $0 unit              # Run unit tests only"
        echo "  $0 integration       # Run integration tests"
        echo "  $0 e2e               # Run end-to-end tests (requires services)"
        echo "  $0 coverage          # Run with coverage report"
        echo "  $0 unit -k discover  # Run unit tests matching 'discover'"
        echo "  $0 watch             # Run tests in watch mode"
        exit 1
        ;;
esac

echo -e "${GREEN}Test run complete!${NC}"
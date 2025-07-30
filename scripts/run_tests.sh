#!/bin/bash
# Quick test runner for development

echo "Running ASCOM MCP Server Tests"
echo "=============================="

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Not in virtual environment. Activate with: source venv/bin/activate"
    exit 1
fi

# Install dev dependencies if needed
pip install -q -e ".[dev]"

echo -e "\n1. Running unit tests..."
pytest tests/unit/ -v

echo -e "\n2. Running integration tests..."
pytest tests/integration/ -v

echo -e "\n3. Code quality checks..."
black --check src/ tests/ && echo "✓ Black formatting OK"
ruff check src/ tests/ && echo "✓ Ruff linting OK"

echo -e "\n4. Type checking..."
mypy src/ --ignore-missing-imports

echo -e "\nDone!"
.PHONY: help install test test-critical test-integration lint format build clean release check-release

help:
	@echo "ASCOM MCP Server Development Commands"
	@echo "===================================="
	@echo "make install       - Install package in development mode"
	@echo "make test         - Run all tests"
	@echo "make test-critical - Run critical integration tests only"
	@echo "make lint         - Run code linting"
	@echo "make format       - Auto-format code"
	@echo "make build        - Build distribution packages"
	@echo "make check-release - Run pre-release checks"
	@echo "make clean        - Clean build artifacts"

install:
	pip install -e ".[dev]"

test:
	pytest -v

test-critical:
	pytest tests/integration/test_mcp_server_startup.py tests/integration/test_claude_desktop_integration.py -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check .

format:
	ruff check . --fix
	ruff format .

build: clean
	python -m build

check-release:
	@echo "Running pre-release checks..."
	./scripts/test_before_release.sh

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Helper to show what version would be released
version:
	@python -c "import ascom_mcp; print(f'Current version: {ascom_mcp.__version__}')"

# Test the package with MCP Inspector
test-inspector:
	mcp-inspector python -- -m ascom_mcp
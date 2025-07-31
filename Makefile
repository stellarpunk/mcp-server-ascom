# Makefile for ASCOM MCP Server
# Always uses the correct virtual environment

VENV := .venv
PYTHON := $(VENV)/bin/python
UV := uv

# Check if venv exists
ifeq ($(wildcard $(VENV)/.*),)
    VENV_EXISTS := 0
else
    VENV_EXISTS := 1
endif

.PHONY: help install test test-critical test-integration lint format build clean release check-release

help:
	@echo "ASCOM MCP Server Development Commands"
	@echo "===================================="
	@echo "make venv          - Create virtual environment"
	@echo "make install       - Install package in development mode"
	@echo "make test          - Run all tests"
	@echo "make test-critical - Run critical integration tests only"
	@echo "make lint          - Run code linting"
	@echo "make format        - Auto-format code"
	@echo "make build         - Build distribution packages"
	@echo "make check-release - Run pre-release checks"
	@echo "make clean         - Clean build artifacts"
	@echo "make run           - Run the MCP server"
	@echo ""
	@echo "Current environment:"
	@if [ $(VENV_EXISTS) -eq 1 ]; then \
		echo "✅ Virtual environment exists"; \
		echo "   Python: $$($(PYTHON) --version 2>&1)"; \
	else \
		echo "❌ No virtual environment found - run: make venv"; \
	fi

venv:
	@echo "Creating virtual environment with uv..."
	$(UV) venv
	@echo "✅ Virtual environment created. Now run: make install"

install: check-venv
	@echo "Installing package in development mode..."
	$(UV) pip install --python $(PYTHON) -e ".[dev]"

test: check-venv
	$(PYTHON) -m pytest -v

test-critical: check-venv
	$(PYTHON) -m pytest tests/integration/test_mcp_server_startup.py tests/integration/test_claude_desktop_integration.py -v

test-integration: check-venv
	$(PYTHON) -m pytest tests/integration/ -v

lint: check-venv
	$(PYTHON) -m ruff check .

format: check-venv
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m ruff format .

build: check-venv clean
	$(PYTHON) -m build

check-release: check-venv
	@echo "Running pre-release checks..."
	$(VENV)/bin/bash ./scripts/test_before_release.sh

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Helper to show what version would be released
version: check-venv
	@$(PYTHON) -c "import ascom_mcp; print(f'Current version: {ascom_mcp.__version__}')"

# Run the MCP server
run: check-venv
	$(PYTHON) -m ascom_mcp

# Test the package with MCP Inspector
test-inspector: check-venv
	npx @modelcontextprotocol/inspector -- $(PYTHON) -m ascom_mcp

# Check that we're using the venv
check-venv:
	@if [ $(VENV_EXISTS) -eq 0 ]; then \
		echo "❌ ERROR: No virtual environment found!"; \
		echo "   Run: make venv && make install"; \
		exit 1; \
	fi

# Development setup shortcut
dev: venv install
	@echo "✅ Development environment ready!"
	@echo "   Activate with: source .venv/bin/activate"
	@echo "   Or use direnv: direnv allow"
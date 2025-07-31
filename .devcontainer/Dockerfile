# syntax=docker/dockerfile:1.4
# Modern multi-stage Dockerfile for MCP Server ASCOM using UV

# Build stage
FROM python:3.12-slim AS builder

# Install UV for fast dependency management
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip uv

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up build environment
WORKDIR /app
COPY pyproject.toml requirements*.txt ./
# Copy source structure needed for egg_base
COPY src ./src
COPY README.md ./

# Create virtual environment with UV
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies using UV
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f requirements.txt ]; then \
        uv pip install -r requirements.txt; \
    else \
        uv pip install .; \
    fi && \
    uv pip install pip  # Add pip for devcontainer compatibility

# Copy remaining files
COPY . .
# Install the package in development mode
RUN uv pip install -e .

# Runtime stage
FROM python:3.12-slim AS runtime

# Copy UV from official image for devcontainer support
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Install runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mcp

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application
WORKDIR /app
COPY --from=builder /app /app

# Switch to non-root user
USER mcp

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ASCOM_DISCOVERY_TIMEOUT=5.0

# MCP server runs over stdio, no ports exposed
# Health check via the parent application

# Run MCP server
CMD ["python", "-m", "ascom_mcp"]
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

# Install development dependencies including Playwright
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e ".[dev]" && \
    uv pip install pytest-playwright playwright

# Install Playwright dependencies and browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/* \
    && playwright install chromium --with-deps

# Copy remaining files
COPY . .
# Install the package in development mode
RUN uv pip install -e .

# Runtime stage
FROM python:3.12-slim AS runtime

# Copy UV from official image for devcontainer support
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Install runtime dependencies and debugging tools
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    multitail \
    jq \
    netcat-openbsd \
    procps \
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

# Copy multitail configuration
COPY .multitailrc /home/mcp/.multitailrc
RUN chown mcp:mcp /home/mcp/.multitailrc

# Switch to non-root user
USER mcp

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ASCOM_DISCOVERY_TIMEOUT=5.0

# MCP server runs over stdio, no ports exposed
# Health check via the parent application

# Run MCP server
CMD ["python", "-m", "ascom_mcp"]
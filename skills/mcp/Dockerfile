# AI SAFE2 MCP Server — Dockerfile
# Non-root user, minimal attack surface, pinned base image.
# Binds to 127.0.0.1 only. Caddy handles HTTPS termination externally.
# Build: docker build -t ai-safe2-mcp .
# Run (stdio):  docker run --rm -i ai-safe2-mcp
# Run (HTTPS):  docker run --env-file .env -p 127.0.0.1:8000:8000 ai-safe2-mcp

FROM python:3.12-slim-bookworm AS base

# Security: do not run as root
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --no-create-home --shell /sbin/nologin appuser

WORKDIR /app

# Prevent .pyc files and ensure stdout/stderr is unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# ── Dependency layer (cached unless pyproject.toml changes) ───────────────────
FROM base AS deps
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ── Final image ───────────────────────────────────────────────────────────────
FROM deps AS final

# Copy application source
COPY src/ ./src/

# Copy data files (controls JSON)
COPY data/ ./data/

# Own everything to appuser
RUN chown -R appuser:appgroup /app

USER appuser

# Health check for Railway / Render / Fly.io
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

# Default to HTTP transport (Caddy handles TLS)
# Override to stdio for local use: docker run --rm -i -e MCP_TRANSPORT=stdio ai-safe2-mcp
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "mcp_server.app"]

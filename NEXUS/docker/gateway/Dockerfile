FROM python:3.11-slim

LABEL org.opencontainers.image.title="NEXUS Sovereign Gateway"
LABEL org.opencontainers.image.description="NEXUS-A2A sovereign gateway wrapping MCP/ACS endpoints"
LABEL org.opencontainers.image.version="0.3.0"
LABEL org.opencontainers.image.vendor="Cyber Strategy Institute"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.source="https://github.com/CyberStrategyInstitute/ai-safe2-framework"

# Non-root user for security
RUN groupadd -r nexus && useradd -r -g nexus -d /app nexus

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache)
COPY ../../sdk/python/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install the NEXUS SDK
COPY ../../sdk/python /app/sdk/python
RUN pip install --no-cache-dir -e "/app/sdk/python[full]"

# Copy gateway application
COPY gateway.py /app/gateway.py

# OPA policies and schemas are mounted at runtime (see docker-compose.yml)
# This allows policy updates without rebuilding the image.

# Runtime directories
RUN mkdir -p /app/logs && chown -R nexus:nexus /app

USER nexus

EXPOSE 8080 8443

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "gateway:app", "--host", "0.0.0.0", "--port", "8080", \
     "--log-level", "info"]

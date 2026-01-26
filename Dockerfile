FROM python:3.11-slim

WORKDIR /app

# Install dependencies via pyproject.toml
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy the Gateway Source Code
# NOTE: We are copying the 'gateway' folder into the container
COPY gateway/ ./gateway/
COPY config/ ./config/

# Security: Run as non-root
RUN useradd -m -u 1000 gateway && chown -R gateway:gateway /app
USER gateway

EXPOSE 8000

# Point to the correct module inside the gateway folder
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Zero Tolerance System - Production Docker Image
FROM python:3.11-slim

# Metadata
LABEL maintainer="Zero Tolerance Team"
LABEL version="2.0.0"
LABEL description="Zero Tolerance Code Quality System"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ZT_ENV=production \
    ZT_HOME=/app \
    ZT_API_HOST=0.0.0.0 \
    ZT_API_PORT=8088 \
    ZT_MIN_SCORE=90 \
    ZT_MODE=safe \
    ZT_DRY_RUN=0

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper structure
RUN mkdir -p \
    logs \
    data/cache \
    data/cache/ai_index \
    data/cache/patches \
    data/config \
    cache/patches \
    .github/workflows

# Health check using API endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${ZT_API_PORT}/live || exit 1

# Expose API port
EXPOSE 8088

# Default command - API Server
CMD ["python", "api_server/start_server.py"]

# Alternative commands (use with docker run --entrypoint):
# Validator: ["python", "enforcement/validator_engine.py", "/workspace"]
# Queue: ["python", "enforcement/ai_queue.py"]
# MCP: ["python", "contract-enforcer-mcp/server.py"]

# Zero Tolerance MCP Server Dockerfile
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY contract-enforcer-mcp/ ./contract-enforcer-mcp/
COPY enforcement/ ./enforcement/
COPY app/ ./app/
COPY data/ ./data/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    ZT_DOCKER_MODE=1 \
    PYTHONPATH=/app

# Create a non-root user
RUN useradd -m -u 1000 ztuser && \
    chown -R ztuser:ztuser /app

USER ztuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the MCP server with proper signal handling
ENTRYPOINT ["python", "-u", "main.py"]

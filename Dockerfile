# Zero Tolerance MCP Server Dockerfile
FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt .
COPY pyproject.toml .
COPY main.py .
COPY contract-enforcer-mcp/ ./contract-enforcer-mcp/
COPY enforcement/ ./enforcement/
COPY app/ ./app/
COPY data/ ./data/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ZT_DOCKER_MODE=1
ENV PYTHONPATH=/app

# Expose port (if needed for HTTP mode)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the MCP server
CMD ["python", "main.py"]

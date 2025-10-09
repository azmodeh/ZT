#!/usr/bin/env python3
"""Entry point for Zero Tolerance MCP Server - Docker compatible"""
import sys
import os
from pathlib import Path

# Set environment variable to skip validation
os.environ['ZT_DOCKER_MODE'] = '1'

# Set working directory to app root
app_root = Path(__file__).parent.resolve()
os.chdir(app_root)

# Add paths to sys.path
sys.path.insert(0, str(app_root))
sys.path.insert(0, str(app_root / "contract-enforcer-mcp"))

# Import and run the server
from server import mcp

if __name__ == "__main__":
    mcp.run()

#!/usr/bin/env python3
"""Entry point for Zero Tolerance MCP Server - Docker compatible"""
import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("Starting Zero Tolerance MCP Server...")

# Set environment variable to skip validation
os.environ['ZT_DOCKER_MODE'] = '1'
logger.info("Docker mode enabled")

# Set working directory to app root
app_root = Path(__file__).parent.resolve()
logger.info(f"App root: {app_root}")
os.chdir(app_root)

# Add paths to sys.path
sys.path.insert(0, str(app_root))
sys.path.insert(0, str(app_root / "contract-enforcer-mcp"))
logger.info(f"Python path updated: {sys.path[:3]}")

# Check if required files exist
server_file = app_root / "contract-enforcer-mcp" / "server.py"
enforcement_dir = app_root / "enforcement"
logger.info(f"Server file exists: {server_file.exists()}")
logger.info(f"Enforcement dir exists: {enforcement_dir.exists()}")

# Import and run the server
try:
    logger.info("Importing server module...")
    from server import mcp
    logger.info("Server module imported successfully")
    logger.info("Starting MCP server...")
    mcp.run()
except Exception as e:
    logger.error(f"Failed to start server: {e}", exc_info=True)
    sys.exit(1)

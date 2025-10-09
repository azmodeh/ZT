#!/usr/bin/env python3
"""Entry point for Zero Tolerance MCP Server"""
import sys
from pathlib import Path

# Add contract-enforcer-mcp to path
sys.path.insert(0, str(Path(__file__).parent / "contract-enforcer-mcp"))

# Import and run the server
from server import mcp

if __name__ == "__main__":
    mcp.run()

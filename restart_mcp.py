#!/usr/bin/env python3
"""
Force restart MCP server by updating modification time
This tricks VS Code/Windsurf into reloading the server
"""

import os
import time
from pathlib import Path

def restart_mcp_server():
    """Force restart MCP server by touching the server file"""
    
    server_file = Path("contract-enforcer-mcp/server.py")
    
    if server_file.exists():
        # Update modification time to current time
        current_time = time.time()
        os.utime(server_file, (current_time, current_time))
        print(f"✅ Updated {server_file} modification time")
        print("🔄 MCP server should restart automatically")
        print("⏰ Wait 5-10 seconds then try the tools again")
    else:
        print(f"❌ Server file not found: {server_file}")

if __name__ == "__main__":
    restart_mcp_server()

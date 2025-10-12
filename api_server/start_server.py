#!/usr/bin/env python3
"""
Zero Tolerance API Server Launcher
Starts uvicorn server programmatically with configuration from environment
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

# Configuration from environment
HOST = os.getenv("ZT_API_HOST", "127.0.0.1")
PORT = int(os.getenv("ZT_API_PORT", "8088"))
RELOAD = os.getenv("ZT_API_RELOAD", "false").lower() == "true"
WORKERS = int(os.getenv("ZT_API_WORKERS", "1"))
LOG_LEVEL = os.getenv("ZT_LOG_LEVEL", "info")

def main():
    """Start the API server"""
    print("=" * 60)
    print("🚀 Zero Tolerance API Server")
    print("=" * 60)
    print(f"Host:     {HOST}")
    print(f"Port:     {PORT}")
    print(f"Reload:   {RELOAD}")
    print(f"Workers:  {WORKERS}")
    print(f"Log:      {LOG_LEVEL}")
    print("=" * 60)
    print(f"")
    print(f"📍 Endpoints:")
    print(f"   http://{HOST}:{PORT}/health")
    print(f"   http://{HOST}:{PORT}/validate")
    print(f"   http://{HOST}:{PORT}/rewrite")
    print(f"   http://{HOST}:{PORT}/queue")
    print(f"   http://{HOST}:{PORT}/learn")
    print(f"")
    print(f"📚 Documentation:")
    print(f"   http://{HOST}:{PORT}/docs")
    print(f"   http://{HOST}:{PORT}/redoc")
    print("=" * 60)
    print("")
    
    # Configure uvicorn
    config = uvicorn.Config(
        "api_server.server:app",
        host=HOST,
        port=PORT,
        reload=RELOAD,
        workers=WORKERS if not RELOAD else 1,  # Reload incompatible with multiple workers
        log_level=LOG_LEVEL,
        access_log=True,
        use_colors=True,
    )
    
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    main()

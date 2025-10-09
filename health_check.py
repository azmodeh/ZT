#!/usr/bin/env python3
"""
Health check endpoint for ZT MCP Server
Used by Smithery.ai and other deployment platforms
"""

import json
import sys
from pathlib import Path

def health_check() -> dict:
    """Perform health check on ZT system components."""
    status = {
        "status": "healthy",
        "timestamp": "2025-01-10T01:10:00Z",
        "version": "1.0.0",
        "components": {}
    }
    
    try:
        # Check if contract rules exist
        rules_path = Path("enforcement/contract_rules.yml")
        status["components"]["contract_rules"] = {
            "status": "ok" if rules_path.exists() else "missing",
            "path": str(rules_path)
        }
        
        # Check if MCP server can be imported
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("server", "contract-enforcer-mcp/server.py")
            if spec and spec.loader:
                status["components"]["mcp_server"] = {"status": "ok"}
            else:
                status["components"]["mcp_server"] = {"status": "error", "error": "Cannot load server module"}
        except Exception as e:
            status["components"]["mcp_server"] = {"status": "error", "error": str(e)}
        
        # Check Python version
        status["components"]["python"] = {
            "status": "ok",
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        
        # Overall health
        component_statuses = [comp["status"] for comp in status["components"].values()]
        if "error" in component_statuses:
            status["status"] = "unhealthy"
        elif "missing" in component_statuses:
            status["status"] = "degraded"
            
    except Exception as e:
        status["status"] = "unhealthy"
        status["error"] = str(e)
    
    return status

def main():
    """Main health check function."""
    health = health_check()
    print(json.dumps(health, indent=2))
    
    # Exit with appropriate code
    if health["status"] == "healthy":
        sys.exit(0)
    elif health["status"] == "degraded":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()

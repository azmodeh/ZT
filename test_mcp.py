#!/usr/bin/env python3
"""Test MCP server validation function"""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

try:
    # Import from the correct module path
    import importlib.util
    spec = importlib.util.spec_from_file_location("server", "contract-enforcer-mcp/server.py")
    server_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server_module)
    run_validation = server_module.run_validation
    
    # Test validation on ArisenManager
    result = run_validation('d:/Workdir/Manager/ArisenManager')
    
    print("SUCCESS: ZT validation completed!")
    print("Total violations found:", result.get("violations_total", 0))
    print("Files scanned:", result.get("files_scanned", 0))
    print("Compliance score:", result.get("compliance_score", 0))
    
    # Save full results to file
    with open("full_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("Full report saved to: full_validation_report.json")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

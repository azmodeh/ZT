#!/usr/bin/env python3
"""Test MCP server autofix function"""

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
    run_fixer = server_module.run_fixer
    
    # Test autofix on ArisenManager
    result = run_fixer('d:/Workdir/Manager/ArisenManager')
    
    print("SUCCESS: ZT autofix completed!")
    print("Files fixed:", result.get("total_files", 0))
    
    # Save full results to file
    with open("autofix_report.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("Full autofix report saved to: autofix_report.json")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

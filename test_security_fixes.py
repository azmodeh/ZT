#!/usr/bin/env python3
"""Test security enhancements in MCP server"""

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
    
    print("=== TESTING SECURITY ENHANCEMENTS ===")
    
    # Test 1: Path validation
    print("\n1. Testing Path Validation:")
    valid_path = server_module.validate_base_path('d:/Workdir/Manager/ArisenManager')
    print(f"Valid path test: {valid_path}")
    
    invalid_path = server_module.validate_base_path('../../../../../etc/passwd')
    print(f"Invalid path test (should be False): {invalid_path}")
    
    # Test 2: Rate limiting
    print("\n2. Testing Rate Limiting:")
    for i in range(12):  # Exceed the limit of 10
        result = server_module.check_rate_limit()
        if i < 10:
            print(f"Request {i+1}: {result}")
        else:
            print(f"Request {i+1} (should be limited): {result}")
    
    # Test 3: Config hash
    print("\n3. Testing Config Integrity:")
    config_hash = server_module.get_config_hash()
    print(f"Config hash: {config_hash}")
    
    # Test 4: Validation with security
    print("\n4. Testing Secure Validation:")
    result = server_module.run_validation('d:/Workdir/Manager/ArisenManager')
    print(f"Validation completed with security info: {bool(result.get('security_info'))}")
    print(f"Security metadata: {result.get('security_info', {})}")
    
    print("\n=== ALL SECURITY TESTS COMPLETED ===")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
"""
Direct test of MCP server functions to verify they work
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_mcp_server_direct():
    """Test MCP server functions directly"""
    
    try:
        print("=== Direct MCP Server Test ===")
        
        # Import the server module
        import importlib.util
        server_path = Path("contract-enforcer-mcp/server.py")
        
        if not server_path.exists():
            print(f"❌ Server file not found: {server_path}")
            return
            
        spec = importlib.util.spec_from_file_location("server", server_path)
        server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server)
        
        print("✅ Server module loaded successfully")
        
        # Test contract rules loading
        print("\n1. Testing contract rules loading...")
        try:
            rules = server.load_contract_rules()
            print(f"✅ Rules loaded: {len(rules)} items")
            print(f"   Sample rules: {list(rules.keys())[:5]}")
        except Exception as e:
            print(f"❌ Rules loading failed: {e}")
            return
            
        # Test path validation
        print("\n2. Testing path validation...")
        test_path = "d:/Workdir/Manager/ArisenManager"
        is_valid = server.validate_base_path(test_path)
        print(f"✅ Path validation: {is_valid}")
        
        # Test validation function
        print("\n3. Testing validation function...")
        try:
            # Use a smaller path for testing
            small_path = str(Path(__file__).parent)
            result = server.run_validation(small_path)
            print(f"✅ Validation completed")
            print(f"   Files scanned: {result.get('files_scanned', 0)}")
            print(f"   Violations: {result.get('violations_total', 0)}")
            print(f"   Compliance score: {result.get('compliance_score', 0)}")
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            import traceback
            traceback.print_exc()
            
        print("\n=== Direct Test Completed ===")
        
    except Exception as e:
        print(f"❌ General error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_server_direct()

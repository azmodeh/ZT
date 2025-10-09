#!/usr/bin/env python3
"""ZT MCP Server Tools Test"""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_zt_tools():
    """Test all ZT tools"""
    
    try:
        # Import server module
        import importlib.util
        spec = importlib.util.spec_from_file_location("server", "contract-enforcer-mcp/server.py")
        server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server_module)
        
        print("=== ZT MCP Tools Test ===")
        
        # Test project path
        test_path = "d:/Workdir/Manager/ArisenManager"
        
        # Test 1: Basic validation test
        print("\n1. Basic Validation Test:")
        try:
            # Test loading contract rules first
            print("   Loading contract rules...")
            rules = server_module.load_contract_rules()
            print(f"   Rules loaded: {len(rules)} items")
            
            # Test path validation
            print("   Validating path...")
            is_valid = server_module.validate_base_path(test_path)
            print(f"   Path valid: {is_valid}")
            
            if is_valid:
                # Try a smaller test path first
                print("   Testing on smaller project...")
                small_test_path = "d:/Workdir/ZeroToleranceSystem/ZT"
                
                # Test file validation
                from pathlib import Path
                base_path_obj = Path(small_test_path)
                include_globs = rules.get("include_globs", [])
                exclude_globs = rules.get("exclude_globs", [])
                
                print(f"   Include globs: {include_globs}")
                print(f"   Exclude globs: {exclude_globs}")
                
                size_valid = server_module.validate_file_size_and_count(
                    base_path_obj, include_globs, exclude_globs
                )
                print(f"   Size valid: {size_valid}")
                
                if size_valid:
                    print("   Running validation...")
                    result = server_module.run_validation(small_test_path)
                    print(f"   Result type: {type(result)}")
                    if result:
                        print(f"   Violations: {result.get('violations_total', 'N/A')}")
                    
        except Exception as e:
            print(f"   Exception in basic test: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Auto-fixer
        print("\n2. Auto-fixer Test:")
        try:
            result = server_module.run_fixer(test_path)
            print(f"   Files fixed: {result.get('total_files', 0)}")
            print(f"   Server version: {result.get('security_info', {}).get('server_version', 'N/A')}")
            
            # Show some fixed files details
            fixed_files = result.get('fixed_files', [])
            if fixed_files:
                print(f"   First fixed file details:")
                first_file = fixed_files[0]
                print(f"     Path: {first_file.get('path', 'N/A')}")
                print(f"     Replaced prints: {first_file.get('replaced_prints', 0)}")
                print(f"     Wrapped lines: {first_file.get('wrapped_lines', 0)}")
                print(f"     Logger added: {first_file.get('added_logger', False)}")
        except Exception as e:
            print(f"   Exception: {e}")
            
        # Test 3: Self-assessment report
        print("\n3. Self-Assessment Report Test:")
        try:
            result = server_module.generate_self_assessment_report(test_path)
            print(f"   Status: {result.get('status', 'UNKNOWN')}")
            print(f"   Compliance Score: {result.get('compliance_score', 0)}")
            print(f"   Total Files: {result.get('total_files', 0)}")
            print(f"   Total Violations: {result.get('total_violations', 0)}")
        except Exception as e:
            print(f"   Exception: {e}")
            
        # Test 4: Security functions
        print("\n4. Security Functions Test:")
        try:
            # Test path validation
            is_valid = server_module.validate_base_path(test_path)
            print(f"   Path Valid: {is_valid}")
            
            # Test config hash
            config_hash = server_module.get_config_hash()
            print(f"   Config Hash: {config_hash}")
            
            # Test rate limiting
            can_proceed = server_module.check_rate_limit("test_client")
            print(f"   Rate Limit: {'Allowed' if can_proceed else 'Limited'}")
            
        except Exception as e:
            print(f"   Exception: {e}")
            
        print("\n=== Test Completed ===")
        
    except Exception as e:
        print(f"General Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_zt_tools()

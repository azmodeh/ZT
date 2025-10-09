#!/usr/bin/env python3
"""Debug import issues"""

from pathlib import Path
import importlib.util

# Test paths
ZT_ROOT = Path(__file__).parent.resolve()
ENFORCEMENT_MODULE_PATH = ZT_ROOT / "enforcement"

print(f"ZT_ROOT: {ZT_ROOT}")
print(f"ENFORCEMENT_MODULE_PATH: {ENFORCEMENT_MODULE_PATH}")
print(f"Utils path exists: {(ENFORCEMENT_MODULE_PATH / 'utils.py').exists()}")

# Test secure import
def secure_import_module(module_path: Path, module_name: str):
    """Securely import module from trusted path only."""
    print(f"Trying to import: {module_path}")
    
    if not module_path.is_relative_to(ENFORCEMENT_MODULE_PATH):
        raise Exception(f"Module path outside trusted zone: {module_path}")
    
    if not module_path.exists():
        raise Exception(f"Module not found: {module_path}")
    
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise Exception(f"Cannot load module spec: {module_name}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

try:
    print("\n=== Testing Utils Import ===")
    utils_module = secure_import_module(
        ENFORCEMENT_MODULE_PATH / "utils.py", 
        "enforcement.utils"
    )
    print(f"Utils module loaded: {utils_module}")
    print(f"Utils attributes: {dir(utils_module)}")
    
    print("\n=== Testing load_contract_rules ===")
    load_rules_func = utils_module.load_contract_rules
    print(f"load_contract_rules function: {load_rules_func}")
    
    # Test calling it
    rules = load_rules_func()
    print(f"Rules loaded: {type(rules)}")
    print(f"Rules content: {rules}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

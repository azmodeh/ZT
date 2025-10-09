#!/usr/bin/env python3
"""
SECURE Zero Tolerance Python Contract Enforcer MCP Server
Provides validation tools as MCP services with enhanced security
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache
import time
from collections import defaultdict
import importlib.util
import os

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# SECURE: Hardcoded trusted ZT root path (no dynamic resolution)
ZT_ROOT = Path(__file__).parent.parent.resolve()
ENFORCEMENT_MODULE_PATH = ZT_ROOT / "enforcement"

# Validate ZT root is safe
if not ZT_ROOT.name == "ZT" or not ENFORCEMENT_MODULE_PATH.exists():
    raise SecurityError("ZT project structure validation failed")

mcp = FastMCP("ZT")

# Security constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_REQUEST = 1000
ALLOWED_EXTENSIONS = {'.py', '.yml', '.yaml', '.json', '.txt', '.md'}
RATE_LIMIT_REQUESTS = 10  # Max requests per minute
RATE_LIMIT_WINDOW = 60  # Time window in seconds

# Rate limiting tracking
request_counts = defaultdict(list)

class SecurityError(Exception):
    """Custom security exception"""
    pass

def secure_import_module(module_path: Path, module_name: str):
    """Securely import module from trusted path only."""
    if not module_path.is_relative_to(ENFORCEMENT_MODULE_PATH):
        raise SecurityError(f"Module path outside trusted zone: {module_path}")
    
    if not module_path.exists():
        raise SecurityError(f"Module not found: {module_path}")
    
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise SecurityError(f"Cannot load module spec: {module_name}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def check_rate_limit(client_id: str = "default") -> bool:
    """Check if client has exceeded rate limit."""
    current_time = time.time()
    
    # Clean old requests outside the window
    request_counts[client_id] = [
        req_time for req_time in request_counts[client_id]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    # Check if under limit
    if len(request_counts[client_id]) >= RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for client: {client_id}")
        return False
    
    # Record this request
    request_counts[client_id].append(current_time)
    return True

def validate_base_path(base_path: str) -> bool:
    """Validate that base_path is safe and accessible."""
    try:
        abs_path = Path(base_path).resolve()
        
        # Check if path exists
        if not abs_path.exists():
            logger.warning(f"Path does not exist: {base_path}")
            return False
            
        # Check if it's a directory
        if not abs_path.is_dir():
            logger.warning(f"Path is not a directory: {base_path}")
            return False
            
        # SECURE: Strict path traversal prevention
        if '..' in str(abs_path) or str(abs_path) != str(abs_path.resolve()):
            logger.warning(f"Path traversal detected: {base_path}")
            return False
            
        # Check if path is too deep (prevent excessive recursion)
        if len(abs_path.parts) > 20:
            logger.warning(f"Path too deep: {base_path}")
            return False
        
        # SECURE: Validate path is not in system directories
        system_dirs = {'/etc', '/usr', '/bin', '/sbin', '/root', 'C:\\Windows', 'C:\\Program Files'}
        if any(str(abs_path).startswith(sys_dir) for sys_dir in system_dirs):
            logger.warning(f"System directory access denied: {base_path}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False

def validate_file_size_and_count(base_path: Path, include_globs: list, exclude_globs: list) -> bool:
    """Validate file sizes and count to prevent resource exhaustion."""
    try:
        # SECURE: Use secure module import
        utils_module = secure_import_module(
            ENFORCEMENT_MODULE_PATH / "utils.py", 
            "enforcement.utils"
        )
        ProjectPaths = utils_module.ProjectPaths
        
        paths = ProjectPaths(base_path, include_globs, exclude_globs)
        
        file_count = 0
        total_size = 0
        
        for file_path in paths.python_files():
            file_count += 1
            if file_count > MAX_FILES_PER_REQUEST:
                logger.warning(f"Too many files to process: {file_count}")
                return False
                
            file_size = file_path.stat().st_size
            total_size += file_size
            
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"File too large: {file_path} ({file_size} bytes)")
                return False
                
        logger.info(f"Validation scope: {file_count} files, {total_size} bytes")
        return True
        
    except Exception as e:
        logger.error(f"File validation error: {e}")
        return False

def get_config_hash() -> str:
    """Get hash of contract rules for integrity checking."""
    try:
        config_path = ENFORCEMENT_MODULE_PATH / "contract_rules.yml"
        
        if config_path.exists():
            with open(config_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        pass
    return "unknown"

def load_contract_rules() -> Dict[str, Any]:
    """SECURE: Load contract rules from YAML configuration"""
    try:
        # SECURE: Use secure module import instead of sys.path manipulation
        utils_module = secure_import_module(
            ENFORCEMENT_MODULE_PATH / "utils.py", 
            "enforcement.utils"
        )
        load_rules_func = utils_module.load_contract_rules
        
        # SECURE: Use context manager instead of os.chdir
        config_path = ENFORCEMENT_MODULE_PATH / "contract_rules.yml"
        if not config_path.exists():
            raise FileNotFoundError(f"Contract rules not found: {config_path}")
        
        # Load rules with current working directory preserved
        return load_rules_func()
        
    except Exception as e:
        logger.error(f"Failed to load contract rules: {e}")
        raise SecurityError(f"Contract rules loading failed: {e}")

@lru_cache(maxsize=10)
def _cached_validation(base_path: str, config_hash: str) -> Dict[str, Any]:
    """SECURE: Cached validation implementation."""
    try:
        # SECURE: Use secure module imports
        validator_module = secure_import_module(
            ENFORCEMENT_MODULE_PATH / "validator.py",
            "enforcement.validator"
        )
        utils_module = secure_import_module(
            ENFORCEMENT_MODULE_PATH / "utils.py",
            "enforcement.utils"
        )
        
        Validator = validator_module.Validator
        ProjectPaths = utils_module.ProjectPaths

        rules = load_contract_rules()
        
        # Security validation
        if not validate_base_path(base_path):
            raise ValueError(f"Invalid base path: {base_path}")
        
        base_path_obj = Path(base_path)
        include_globs = rules.get("include_globs", [])
        exclude_globs = rules.get("exclude_globs", [])
        
        if not validate_file_size_and_count(base_path_obj, include_globs, exclude_globs):
            raise ValueError("File validation failed: Too many files or files too large")
        
        paths = ProjectPaths(base_path_obj, include_globs, exclude_globs)
        validator = Validator(rules, paths)
        report = validator.run()
        
        # Add security metadata
        result = report.to_dict()
        result["security_info"] = {
            "config_hash": config_hash,
            "validation_timestamp": str(Path(base_path).stat().st_mtime),
            "server_version": "ZT-MCP-SECURE-1.0"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise

def run_validation(base_path: str) -> Dict[str, Any]:
    """Run contract validation over codebase with security checks."""
    config_hash = get_config_hash()
    return _cached_validation(base_path, config_hash)

def run_fixer(base_path: str) -> Dict[str, Any]:
    """Run auto-fixer on codebase with security checks."""
    # Security validation first
    if not validate_base_path(base_path):
        raise ValueError(f"Invalid base path: {base_path}")
    
    try:
        # SECURE: Use secure module imports
        rewriter_module = secure_import_module(
            ENFORCEMENT_MODULE_PATH / "rewriter.py",
            "enforcement.rewriter"
        )
        utils_module = secure_import_module(
            ENFORCEMENT_MODULE_PATH / "utils.py",
            "enforcement.utils"
        )
        
        AutoRewriter = rewriter_module.AutoRewriter
        ProjectPaths = utils_module.ProjectPaths

        rules = load_contract_rules()
        base_path_obj = Path(base_path)
        include_globs = rules.get("include_globs", [])
        exclude_globs = rules.get("exclude_globs", [])
        
        # Additional validation for file operations
        if not validate_file_size_and_count(base_path_obj, include_globs, exclude_globs):
            raise ValueError("File validation failed: Cannot fix - too many files or files too large")
        
        paths = ProjectPaths(base_path_obj, include_globs, exclude_globs)
        rewriter = AutoRewriter(paths)
        outcomes = rewriter.execute()

        results = []
        for outcome in outcomes:
            results.append(
                {
                    "path": str(outcome.path),
                    "replaced_prints": outcome.replaced_prints,
                    "wrapped_lines": outcome.wrapped_lines,
                    "added_logger": outcome.added_logger,
                }
            )

        return {
            "fixed_files": results, 
            "total_files": len(outcomes),
            "security_info": {
                "config_hash": get_config_hash(),
                "server_version": "ZT-MCP-SECURE-1.0"
            }
        }
    except Exception as e:
        logger.error(f"Fixer error: {e}")
        raise

# MCP Tools with enhanced security
@mcp.tool
def validate_code(base_path: str) -> dict:
    """Validate Python codebase against Zero Tolerance contract rules"""
    try:
        # Rate limiting check
        if not check_rate_limit():
            return {"error": "Rate limit exceeded. Please wait before making another request."}
        
        return run_validation(base_path)
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return {"error": str(e)}

@mcp.tool
def fix_violations(base_path: str) -> dict:
    """Auto-fix contract violations in Python codebase"""
    try:
        # Rate limiting check
        if not check_rate_limit():
            return {"error": "Rate limit exceeded. Please wait before making another request."}
        
        return run_fixer(base_path)
    except Exception as e:
        logger.error(f"Fixer error: {e}")
        return {"error": str(e)}

@mcp.tool
def check_compliance(base_path: str) -> dict:
    """Check overall compliance status of a codebase"""
    try:
        # Rate limiting check
        if not check_rate_limit():
            return {"error": "Rate limit exceeded. Please wait before making another request."}
        
        result = run_validation(base_path)
        score = result.get("compliance_score", 0)
        status = "PASS" if result.get("violations_total", 0) == 0 else "FAIL"

        return {
            "status": status,
            "compliance_score": score,
            "total_violations": result.get("violations_total", 0),
            "files_scanned": result.get("files_scanned", 0),
        }
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()

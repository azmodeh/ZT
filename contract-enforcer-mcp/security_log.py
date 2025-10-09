#!/usr/bin/env python3
"""
Security logging module for ZT MCP Server
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class SecurityLogger:
    """Handles security-related logging for MCP server."""
    
    def __init__(self, log_dir: str = "logs/security"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup security logger
        self.logger = logging.getLogger("zt_security")
        self.logger.setLevel(logging.INFO)
        
        # File handler for security events
        handler = logging.FileHandler(
            self.log_dir / "security.log", 
            encoding="utf-8"
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_validation_request(self, base_path: str, client_id: str = "default") -> None:
        """Log validation request."""
        self.logger.info(f"VALIDATION_REQUEST - Client: {client_id}, Path: {base_path}")
    
    def log_fix_request(self, base_path: str, client_id: str = "default") -> None:
        """Log autofix request."""
        self.logger.warning(f"AUTOFIX_REQUEST - Client: {client_id}, Path: {base_path}")
    
    def log_rate_limit_exceeded(self, client_id: str) -> None:
        """Log rate limit violation."""
        self.logger.warning(f"RATE_LIMIT_EXCEEDED - Client: {client_id}")
    
    def log_security_violation(self, violation_type: str, details: str, client_id: str = "default") -> None:
        """Log security violation."""
        self.logger.error(f"SECURITY_VIOLATION - Type: {violation_type}, Client: {client_id}, Details: {details}")
    
    def log_path_validation_failure(self, path: str, reason: str) -> None:
        """Log path validation failure."""
        self.logger.warning(f"PATH_VALIDATION_FAILED - Path: {path}, Reason: {reason}")

# Global security logger instance
security_logger = SecurityLogger()

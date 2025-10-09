"""Zero Tolerance Python Contract Enforcer
Centralized Logging Module
"""

import logging
import logging.config
from pathlib import Path


def configure_logging() -> None:
    """Configure the logging subsystem using the YAML file.
    Idempotent: safe to call multiple times.
    """
    log_config_path = Path("data/config/logging.yml")
    if getattr(configure_logging, "_configured", False):
        return
    if log_config_path.exists():
        with log_config_path.open("r", encoding="utf-8") as stream:
            import yaml
            config = yaml.safe_load(stream) or {}
        if config:
            logging.config.dictConfig(config)
    logging.getLogger("zero_tolerance").debug("Logging configured from %s", log_config_path)
    configure_logging._configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Name of the logger (typically __name__)
        
    Returns:
        Configured logger instance
    """
    configure_logging()
    return logging.getLogger(name)

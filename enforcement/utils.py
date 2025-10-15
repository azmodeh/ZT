from __future__ import annotations

import logging
import logging.config
import os
import sys
import shutil
from dataclasses import dataclass
import json
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterator, Sequence, Optional, Union

import yaml

LOG_CONFIG_PATH = Path("data/config/logging.yml")
RULES_PATH = Path("enforcement/contract_rules.yml")
AI_MODEL_CONFIG_PATH = Path("data/config/ai_models.json")

# Logger for this module
logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """
    Configure the logging subsystem using the YAML file.
    Idempotent: safe to call multiple times.
    """
    if getattr(configure_logging, "_configured", False):
        return
    if LOG_CONFIG_PATH.exists():
        with LOG_CONFIG_PATH.open("r", encoding="utf-8") as stream:
            config = yaml.safe_load(stream) or {}
        if config:
            logging.config.dictConfig(config)
    logging.getLogger("zero_tolerance").debug("Logging configured from %s", LOG_CONFIG_PATH)
    configure_logging._configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def emit_ui_message(message: str) -> None:
    """
    Display Persian-facing UI text without violating the no-print rule.
    """
    text = f"{message}\n"
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.flush()


def get_ai_config() -> Dict[str, str]:
    """
    Load AI configuration from contract rules with environment variable support.
    """
    try:
        rules = load_contract_rules()
        ai_config = rules.get("ai_config", {})
        
        # Support environment variables for API key security
        api_key = ai_config.get("api_key", "")
        if api_key.startswith("env:"):
            env_var = api_key[4:]  # Remove "env:" prefix
            api_key = os.getenv(env_var, api_key)
        
        return {
            "api_key": api_key,
            "base_url": ai_config.get("base_url", "https://openrouter.ai/api/v1"),
            "model": ai_config.get("model", "meta-llama/llama-3.3-70b-instruct:free")
        }
    except Exception as e:
        get_logger(__name__).error(f"Failed to load AI config: {e}")
        return {
            "api_key": "",
            "base_url": "https://openrouter.ai/api/v1", 
            "model": "meta-llama/llama-3.3-70b-instruct:free"
        }


def load_contract_rules() -> Dict[str, Any]:
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"Contract rules file not found at {RULES_PATH}")
    with RULES_PATH.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def resolve_target_root(rules: Dict[str, Any]) -> Path:
    override = os.getenv("ZT_TARGET")
    if override:
        return Path(override).expanduser().resolve()
    target = rules.get("target_root")
    if not target:
        return RULES_PATH.parent.resolve()
    target_path = Path(target)
    if not target_path.is_absolute():
        target_path = (RULES_PATH.parent / target_path).resolve()
    return target_path


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


class ProjectPaths:
    def __init__(self, base: Path, includes: Sequence[str], excludes: Sequence[str]):
        self.base = base
        self.includes = includes
        self.excludes = excludes

    def iter_python_files(self) -> Iterator[Path]:
        if not self.base.exists():
            return
        for path in self.base.rglob("*.py"):
            relative = path.relative_to(self.base)
            if self._is_excluded(relative):
                continue
            if not self._is_included(relative):
                continue
            yield path
    
    def python_files(self) -> Iterator[Path]:
        """Alias for iter_python_files for compatibility"""
        return self.iter_python_files()

    def _is_included(self, relative: Path) -> bool:
        if not self.includes:
            return True
        return any(fnmatch(str(relative), pattern) for pattern in self.includes)

    def _is_excluded(self, relative: Path) -> bool:
        return any(fnmatch(str(relative), pattern) for pattern in self.excludes)


def load_project_paths() -> ProjectPaths:
    rules = load_contract_rules()
    target_root = resolve_target_root(rules)
    includes = rules.get("include_globs", []) or []
    excludes = rules.get("exclude_globs", []) or []
    return ProjectPaths(base=target_root, includes=includes, excludes=excludes)


def timestamped_name(prefix: str, suffix: str) -> str:
    from datetime import datetime

    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{now}{suffix}"


def load_ai_model_config() -> Dict[str, Any]:
    if not AI_MODEL_CONFIG_PATH.exists():
        return {}
    with AI_MODEL_CONFIG_PATH.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def is_dry_run() -> bool:
    """
    Check if we're in dry-run mode
    
    Returns:
        True if ZT_DRY_RUN is set to 1, true, or yes
    """
    return os.getenv("ZT_DRY_RUN", "0").lower() in ("1", "true", "yes")


def validate_path_within_target(path: Union[str, Path], target: Optional[str] = None) -> Path:
    """
    Validate that a path is within the target directory
    
    Args:
        path: Path to validate
        target: Optional target root (defaults to ZT_TARGET from environment)
    
    Returns:
        Validated Path object
    
    Raises:
        ValueError: If path is outside ZT_TARGET
    """
    # Get target from parameter or environment
    target_str = target or os.getenv("ZT_TARGET", os.getcwd())
    target_root = Path(target_str).resolve()
    
    # Normalize path
    if isinstance(path, str):
        path_obj = Path(path)
    else:
        path_obj = path
    
    # Resolve to absolute path
    requested_path = path_obj.resolve()
    
    # Check if requested path is within target
    if not str(requested_path).startswith(str(target_root)):
        raise ValueError(
            f"Path security violation: {requested_path} is outside target directory {target_root}"
        )
    
    return requested_path


def safe_write_file(path: Union[str, Path], content: str, backup: bool = True) -> bool:
    """
    Safely write content to a file with validation and backup
    
    Args:
        path: Path to write to
        content: Content to write
        backup: Whether to create a backup of the original file
    
    Returns:
        True if file was written, False if in dry-run mode
    
    Raises:
        ValueError: If path is outside ZT_TARGET
        IOError: If file cannot be written
    """
    # Check if we're in dry-run mode
    if is_dry_run():
        logger.info(f"DRY-RUN: Would write to {path}, but skipping in dry-run mode")
        return False
    
    # Validate path is within target
    path_obj = validate_path_within_target(path)
    
    try:
        # Create parent directories if needed
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if file exists and backup is requested
        if backup and path_obj.exists():
            backup_path = path_obj.with_suffix(f"{path_obj.suffix}.bak")
            shutil.copy2(path_obj, backup_path)
            logger.debug(f"Created backup at {backup_path}")
        
        # Write content
        path_obj.write_text(content, encoding="utf-8")
        logger.info(f"Successfully wrote to {path_obj}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write to {path_obj}: {e}")
        raise IOError(f"Failed to write to {path}: {e}") from e


def json_serialize(obj: Any) -> str:
    """
    Serialize object to JSON with proper formatting
    
    Args:
        obj: Object to serialize
    
    Returns:
        JSON string
    """
    return json.dumps(obj, indent=2, ensure_ascii=False)


def json_deserialize(json_str: str) -> Any:
    """
    Deserialize JSON string to object
    
    Args:
        json_str: JSON string
    
    Returns:
        Deserialized object
    """
    return json.loads(json_str)

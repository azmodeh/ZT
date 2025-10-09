from __future__ import annotations

import logging
import logging.config
import os
import sys
from dataclasses import dataclass
import json
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterator, Sequence

import yaml

LOG_CONFIG_PATH = Path("data/config/logging.yml")
RULES_PATH = Path("enforcement/contract_rules.yml")
AI_MODEL_CONFIG_PATH = Path("data/config/ai_models.json")


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

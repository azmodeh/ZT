from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import orjson

from enforcement.utils import ensure_directory, get_logger, timestamped_name

LOGGER = get_logger("zero_tolerance.report")
LOG_DIR = Path("logs")


def _default_serializer(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def store_report(data: Dict[str, Any], prefix: str = "validation") -> Path:
    """
    Persist the given report dictionary to the logs directory with a timestamp.
    """
    ensure_directory(LOG_DIR)
    filename = timestamped_name(prefix, ".json")
    destination = LOG_DIR / filename
    try:
        payload = orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
    except orjson.JSONEncodeError:
        payload = json.dumps(data, indent=2, default=_default_serializer).encode("utf-8")
    destination.write_bytes(payload)
    LOGGER.info("Stored report at %s", destination)
    return destination

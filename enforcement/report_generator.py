from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def load_latest_report(prefix: str = "validation") -> Optional[Dict[str, Any]]:
    """
    Load the latest validation report from the logs directory.
    
    Args:
        prefix: The prefix of the report files to search for
        
    Returns:
        The latest report data or None if no reports exist
    """
    ensure_directory(LOG_DIR)
    
    # Find all validation report files
    report_files = list(LOG_DIR.glob(f"{prefix}_*.json"))
    
    if not report_files:
        LOGGER.info("No %s reports found in %s", prefix, LOG_DIR)
        return None
    
    # Sort by modification time (most recent first)
    latest_file = max(report_files, key=lambda f: f.stat().st_mtime)
    
    try:
        content = latest_file.read_bytes()
        data = orjson.loads(content)
        LOGGER.info("Loaded latest %s report from %s", prefix, latest_file)
        return data
    except Exception as e:
        LOGGER.error("Failed to load report %s: %s", latest_file, e)
        return None


def load_all_reports(prefix: str = "validation") -> List[Dict[str, Any]]:
    """
    Load all validation reports from the logs directory.
    
    Args:
        prefix: The prefix of the report files to search for
        
    Returns:
        List of all report data
    """
    ensure_directory(LOG_DIR)
    
    # Find all validation report files
    report_files = list(LOG_DIR.glob(f"{prefix}_*.json"))
    
    reports = []
    for report_file in report_files:
        try:
            content = report_file.read_bytes()
            data = orjson.loads(content)
            reports.append(data)
        except Exception as e:
            LOGGER.error("Failed to load report %s: %s", report_file, e)
            continue
    
    # Sort by timestamp in the data (assuming it exists)
    reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    LOGGER.info("Loaded %d %s reports", len(reports), prefix)
    return reports

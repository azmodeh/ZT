from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import httpx
import orjson

from enforcement.utils import (
    ProjectPaths,
    emit_ui_message,
    ensure_directory,
    get_logger,
    load_ai_model_config,
    load_contract_rules,
    load_project_paths,
    timestamped_name,
)

LOGGER = get_logger("zero_tolerance.ai_agent")
PATCH_CACHE = Path("data/cache/patches")
INDEX_PATH = Path("data/cache/ai_index/index.json")


@dataclass
class Patch:
    path: Path
    content: str


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Zero Tolerance AI Agent - applies contract compliant patches.",
    )
    parser.add_argument("task", type=str, help="شرح وظیفه برای عامل هوش مصنوعی (فارسی یا انگلیسی)")
    parser.add_argument("--dry-run", action="store_true", help="فقط پاسخ مدل را دریافت کن، بدون اعمال پچ.")
    return parser.parse_args()


def load_index() -> List[Dict[str, Any]]:
    if not INDEX_PATH.exists():
        raise FileNotFoundError("Index not found. Run ai_indexer.py first.")
    data = orjson.loads(INDEX_PATH.read_bytes())
    if not isinstance(data, list):
        raise ValueError("Index file is malformed; expected a list.")
    return data


def select_relevant_chunks(task: str, chunks: Sequence[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    keywords = {token.lower() for token in task.split()}
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for chunk in chunks:
        content = chunk.get("content", "")
        score = sum(1 for word in keywords if word and word in content.lower())
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]


def build_prompt(task: str, rules: Dict[str, Any], context_snippets: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    contract_summary = json.dumps(rules, indent=2)
    context_payload = "\n\n".join(
        f"# {item['path']}:{item['start_line']}-{item['end_line']}\n{item.get('content', '')}"
        for item in context_snippets
    )
    system_prompt = (
        "You are the Zero Tolerance Contract Enforcer. "
        "You must obey the rules strictly and return deterministic JSON patches only."
    )
    instructions = (
        "Contract Rules:\n"
        f"{contract_summary}\n\n"
        "Task Instructions:\n"
        f"{task}\n\n"
        "Project Context:\n"
        f"{context_payload}\n\n"
        "Return a JSON array of objects with 'path' and 'content'. "
        "Each 'content' value must contain the complete file content after your modifications. "
        "Do not include explanations."
    )
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instructions},
        ]
    }


def request_completion(prompt: Dict[str, Any], model_config: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    client = httpx.Client(timeout=60)
    try:
        payload = {
            "model": model_config.get("default"),
            "messages": prompt["messages"],
            "temperature": model_config.get("temperature", 0.2),
            "response_format": {"type": "json_object"},
        }
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()
    finally:
        client.close()


def extract_patches(response: Dict[str, Any]) -> List[Patch]:
    choices = response.get("choices", [])
    if not choices:
        raise ValueError("Model returned no choices.")
    content = choices[0].get("message", {}).get("content", "")
    if not content:
        raise ValueError("Model response missing content.")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        LOGGER.error("Invalid JSON response from model: %s", content)
        raise ValueError("Model response is not valid JSON.") from exc
    if not isinstance(parsed, list):
        raise ValueError("Model response must be a JSON array.")
    patches: List[Patch] = []
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("Each patch must be a JSON object.")
        raw_path = item.get("path")
        content_text = item.get("content")
        if not raw_path or content_text is None:
            raise ValueError("Each patch requires 'path' and 'content'.")
        patches.append(Patch(path=Path(raw_path), content=str(content_text)))
    if not patches:
        raise ValueError("Model returned an empty patch list.")
    return patches


def sanitize_patch_paths(patches: Sequence[Patch], project_paths: ProjectPaths) -> List[Patch]:
    sanitized: List[Patch] = []
    target_root = project_paths.base
    for patch in patches:
        resolved = patch.path if patch.path.is_absolute() else (target_root / patch.path).resolve()
        if not str(resolved).startswith(str(target_root)):
            raise ValueError(f"Patch path escapes target root: {resolved}")
        if any(part in resolved.parts for part in ("enforcement", "data", "logs", ".vscode", "__pycache__")):
            raise ValueError(f"Patch attempts to modify restricted path: {resolved}")
        sanitized.append(Patch(path=resolved, content=patch.content))
    return sanitized


def apply_patches(patches: Sequence[Patch]) -> List[Path]:
    ensure_directory(PATCH_CACHE)
    applied: List[Path] = []
    for patch in patches:
        destination = patch.path
        ensure_directory(destination.parent)
        backup = destination.with_suffix(destination.suffix + ".bak")
        if destination.exists() and not backup.exists():
            shutil.copy2(destination, backup)
        with destination.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(patch.content)
        applied.append(destination)
        LOGGER.info("Applied patch to %s", destination)
    archive_name = PATCH_CACHE / timestamped_name("patch", ".json")
    archive_payload = [{"path": str(item.path), "content": item.content} for item in patches]
    archive_name.write_bytes(orjson.dumps(archive_payload, option=orjson.OPT_INDENT_2))
    LOGGER.info("Stored patch payload at %s", archive_name)
    return applied


def run_validator() -> None:
    result = subprocess.run([sys.executable, "enforcement/validator.py"], check=False)
    if result.returncode != 0:
        LOGGER.warning("Validator reported issues after applying patches.")
    else:
        LOGGER.info("Validator executed successfully after patch application.")


async def main() -> None:
    args = parse_arguments()
    rules = load_contract_rules()
    model_config = load_ai_model_config()
    project_paths = load_project_paths()
    from os import getenv

    api_key = getenv("OPENROUTER_API_KEY") or model_config.get("api_key_override")
    if not api_key:
        LOGGER.error("OPENROUTER_API_KEY is required for the AI agent.")
        emit_ui_message("کلید OpenRouter تنظیم نشده است. لطفاً متغیر محیطی را ست کن.")
        return

    chunks = load_index()
    context = select_relevant_chunks(args.task, chunks)
    prompt = build_prompt(args.task, rules, context)
    response = request_completion(prompt, model_config, api_key)

    try:
        patches = extract_patches(response)
    except ValueError as exc:
        LOGGER.error("Failed to extract patches: %s", exc)
        emit_ui_message("پاسخ مدل معتبر نیست و هیچ تغییری اعمال نشد.")
        return

    sanitized = sanitize_patch_paths(patches, project_paths)
    if args.dry_run:
        emit_ui_message("پاسخ مدل دریافت شد (حالت آزمایشی، بدون اعمال پچ).")
        return

    applied = apply_patches(sanitized)
    run_validator()
    emit_ui_message(
        "پچ‌های مدل اعمال شد.\n"
        f"تعداد فایل‌های تغییرکرده: {len(applied)}\n"
        f"شرح وظیفه: {args.task}"
    )


if __name__ == "__main__":
    main()

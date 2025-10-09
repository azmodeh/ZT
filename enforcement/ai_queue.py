from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

import yaml

from enforcement.utils import ProjectPaths, emit_ui_message, get_logger, load_contract_rules, load_project_paths

QUEUE_LOG_PATH = Path("logs/ai_actions/queue_run.log")
PATCH_CACHE = Path("data/cache/patches")
LOGGER = get_logger("zero_tolerance.queue")


def _attach_queue_handler() -> None:
    for handler in LOGGER.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == QUEUE_LOG_PATH:
            return
    handler = logging.FileHandler(QUEUE_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.propagate = False


@dataclass
class Task:
    task_id: str
    description: str
    agent_prompt: Optional[str] = None
    action: Optional[str] = None


class ChangeTracker:
    def __init__(self, project_paths: ProjectPaths) -> None:
        self.project_paths = project_paths
        self.patch_snapshot = self._snapshot_patches()
        self.file_snapshot = self._snapshot_files()

    def _snapshot_patches(self) -> Dict[Path, float]:
        if not PATCH_CACHE.exists():
            return {}
        return {path: path.stat().st_mtime for path in PATCH_CACHE.glob("*.json")}

    def _snapshot_files(self) -> Dict[Path, float]:
        snapshot: Dict[Path, float] = {}
        for path in self.project_paths.iter_python_files():
            try:
                snapshot[path] = path.stat().st_mtime
            except FileNotFoundError:
                continue
        return snapshot

    def refresh(self) -> None:
        self.patch_snapshot = self._snapshot_patches()
        self.file_snapshot = self._snapshot_files()

    def has_changes(self) -> bool:
        current_patches = self._snapshot_patches()
        current_files = self._snapshot_files()

        if set(current_patches) - set(self.patch_snapshot):
            return True

        for path, mtime in current_files.items():
            baseline = self.file_snapshot.get(path)
            if baseline is None or abs(baseline - mtime) > 1e-6:
                return True
        return False


def load_tasks() -> List[Task]:
    config_path = Path("enforcement/tasks.yml")
    if not config_path.exists():
        raise FileNotFoundError("tasks.yml not found in enforcement directory.")
    with config_path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    tasks: List[Task] = []
    for entry in raw.get("tasks", []):
        tasks.append(
            Task(
                task_id=str(entry.get("id")),
                description=str(entry.get("description", "")),
                agent_prompt=entry.get("agent_prompt"),
                action=entry.get("action"),
            )
        )
    return tasks


def run_command(command: List[str]) -> int:
    LOGGER.info("Executing command: %s", " ".join(command))
    result = subprocess.run(command, check=False)
    return result.returncode


def handle_noop(tracker: ChangeTracker) -> None:
    LOGGER.warning("Task produced no observable changes; running auto rewriter as fallback.")
    emit_ui_message("هیچ تغییری ثبت نشد؛ بازنویس خودکار در حال اجرا است.")
    run_command([sys.executable, "enforcement/rewriter.py"])
    tracker.refresh()


def execute_task(task: Task, tracker: ChangeTracker) -> None:
    emit_ui_message(f"در حال اجرا: {task.description}")
    tracker.refresh()
    if task.agent_prompt:
        code = run_command([sys.executable, "enforcement/ai_agent.py", task.agent_prompt])
    elif task.action == "validate":
        code = run_command([sys.executable, "enforcement/validator.py"])
    elif task.action == "rewrite":
        code = run_command([sys.executable, "enforcement/rewriter.py"])
    else:
        LOGGER.error("Unsupported task configuration: %s", task)
        emit_ui_message("وظیفه ناشناخته است و اجرا نشد.")
        return

    if code != 0:
        LOGGER.error("Task %s exited with code %s", task.task_id, code)
        emit_ui_message("اجرای وظیفه با خطا روبه‌رو شد.")
        return

    if task.agent_prompt and not tracker.has_changes():
        handle_noop(tracker)
        if not tracker.has_changes():
            LOGGER.error("Fallback rewrite also produced no changes.")
            emit_ui_message("هنوز تغییری مشاهده نشد؛ لطفاً بررسی دستی انجام بده.")
            return

    emit_ui_message(f"وظیفه '{task.description}' با موفقیت پایان یافت.")
    tracker.refresh()


def main() -> None:
    _attach_queue_handler()
    load_contract_rules()  # ensures rules file exists
    project_paths = load_project_paths()
    tracker = ChangeTracker(project_paths)
    tasks = load_tasks()

    emit_ui_message("صف هوش مصنوعی آغاز شد.")
    for task in tasks:
        execute_task(task, tracker)

    emit_ui_message("اجرای صف کامل شد. گزارش‌ها در پوشه logs موجود است.")


if __name__ == "__main__":
    main()


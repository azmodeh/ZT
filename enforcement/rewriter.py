from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from enforcement.utils import ProjectPaths, emit_ui_message, get_logger, load_project_paths

LOGGER = get_logger("zero_tolerance.rewriter")
PRINT_PATTERN = re.compile(r"(?<![\w.])print\s*\(")
MAX_LINE_LENGTH = 79


@dataclass
class RewriteOutcome:
    path: Path
    replaced_prints: int = 0
    wrapped_lines: int = 0
    added_logger: bool = False

    @property
    def changed(self) -> bool:
        return any([self.replaced_prints, self.wrapped_lines, self.added_logger])


class AutoRewriter:
    def __init__(self, project_paths: ProjectPaths) -> None:
        self.project_paths = project_paths

    def execute(self) -> List[RewriteOutcome]:
        outcomes: List[RewriteOutcome] = []
        for path in self._iter_files():
            outcome = self._process_file(path)
            if outcome.changed:
                outcomes.append(outcome)
        return outcomes

    def _iter_files(self) -> Iterable[Path]:
        yield from self.project_paths.iter_python_files()

    def _process_file(self, path: Path) -> RewriteOutcome:
        try:
            original = path.read_text(encoding="utf-8")
        except OSError as exc:
            LOGGER.error("Unable to read %s: %s", path, exc)
            return RewriteOutcome(path=path)

        rewritten = original
        outcome = RewriteOutcome(path=path)

        rewritten, print_count = self._replace_prints(rewritten)
        outcome.replaced_prints = print_count

        rewritten, wraps, added_logger = self._enforce_line_length_and_logger(path, rewritten)
        outcome.wrapped_lines = wraps
        outcome.added_logger = added_logger

        if not outcome.changed:
            LOGGER.debug("No rewrite opportunities in %s", path)
            return outcome

        backup_path = path.with_suffix(path.suffix + ".bak")
        try:
            if not backup_path.exists():
                shutil.copy2(path, backup_path)
            path.write_text(rewritten, encoding="utf-8", newline="\n")
            LOGGER.info(
                "Rewrote %s (prints=%s, wraps=%s, added_logger=%s)",
                path,
                outcome.replaced_prints,
                outcome.wrapped_lines,
                outcome.added_logger,
            )
        except OSError as exc:
            LOGGER.error("Failed to persist rewritten file %s: %s", path, exc)
        return outcome

    def _replace_prints(self, text: str) -> Tuple[str, int]:
        count = 0

        def replacement(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return "logger.info("

        replaced = PRINT_PATTERN.sub(replacement, text)
        return replaced, count

    def _enforce_line_length_and_logger(self, path: Path, text: str) -> Tuple[str, int, bool]:
        lines = text.splitlines()
        wraps = 0
        ensure_logger = False
        has_logging_import = any(line.startswith("import logging") for line in lines)
        has_logger_assignment = any("getLogger(__name__)" in line for line in lines)

        adjusted_lines: List[str] = []
        for line in lines:
            adjusted_lines.extend(self._wrap_line(line))
        wraps = sum(1 for line in adjusted_lines if line.endswith("\\"))

        if not has_logging_import and "logger.info(" in "\n".join(adjusted_lines):
            adjusted_lines.insert(0, "import logging")
            ensure_logger = True
        if not has_logger_assignment and "logger.info(" in "\n".join(adjusted_lines):
            insertion_index = 0
            while insertion_index < len(adjusted_lines) and adjusted_lines[insertion_index].startswith("import "):
                insertion_index += 1
            adjusted_lines.insert(insertion_index, "logger = logging.getLogger(__name__)")
            ensure_logger = True

        return "\n".join(adjusted_lines) + "\n", wraps, ensure_logger

    def _wrap_line(self, line: str) -> List[str]:
        if len(line) <= MAX_LINE_LENGTH:
            return [line]
        indentation = len(line) - len(line.lstrip(" "))
        prefix = line[:indentation]
        remainder = line[indentation:]
        segments: List[str] = []
        current = remainder
        while len(prefix + current) > MAX_LINE_LENGTH:
            split_at = MAX_LINE_LENGTH - len(prefix) - 2
            split_at = max(split_at, 10)
            candidate = current.rfind(" ", 0, split_at)
            if candidate == -1:
                candidate = split_at
            segments.append(f"{prefix}{current[:candidate].rstrip()} \\")
            current = current[candidate:].lstrip()
        segments.append(f"{prefix}{current}")
        return segments


def summarize(outcomes: List[RewriteOutcome]) -> str:
    if not outcomes:
        return "هیچ موردی برای بازنویسی خودکار یافت نشد."

    total_prints = sum(item.replaced_prints for item in outcomes)
    total_wraps = sum(item.wrapped_lines for item in outcomes)
    total_files = len(outcomes)
    return (
        "بازنویسی خودکار تکمیل شد.\n"
        f"فایل‌های تغییرکرده: {total_files}\n"
        f"جایگزینی print(): {total_prints}\n"
        f"شکستن خطوط طولانی: {total_wraps}"
    )


def main() -> None:
    paths = load_project_paths()
    rewriter = AutoRewriter(project_paths=paths)
    outcomes = rewriter.execute()
    emit_ui_message(summarize(outcomes))


if __name__ == "__main__":
    main()

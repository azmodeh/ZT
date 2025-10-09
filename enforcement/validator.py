from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from radon.visitors import ComplexityVisitor  # type: ignore import-not-found
except ImportError:  # pragma: no cover
    ComplexityVisitor = None  # type: ignore[assignment]

from enforcement.report_generator import store_report
from enforcement.utils import ProjectPaths, emit_ui_message, get_logger, load_contract_rules, load_project_paths

COMPLEXITY_WARNING_EMITTED = False

LOGGER = get_logger("zero_tolerance.validator")


@dataclass
class RuleViolation:
    rule: str
    message: str
    file_path: Path
    line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "message": self.message,
            "file": str(self.file_path),
            "line": self.line,
        }


@dataclass
class FileValidationResult:
    path: Path
    violations: List[RuleViolation] = field(default_factory=list)

    def add(self, violation: RuleViolation) -> None:
        self.violations.append(violation)


@dataclass
class ValidationReport:
    files: List[FileValidationResult]
    rules_count: int
    violations: List[RuleViolation]

    @property
    def files_scanned(self) -> int:
        return len(self.files)

    @property
    def total_violations(self) -> int:
        return len(self.violations)

    def compliance_score(self) -> float:
        if self.files_scanned == 0 or self.rules_count == 0:
            return 100.0
        penalty = (self.total_violations / (self.files_scanned * self.rules_count)) * 100
        return max(0.0, round(100 - penalty, 2))

    def to_dict(self) -> Dict[str, Any]:
        grouped = {}
        for file_result in self.files:
            grouped[str(file_result.path)] = [item.to_dict() for item in file_result.violations]
        return {
            "files_scanned": self.files_scanned,
            "rules_evaluated": self.rules_count,
            "violations_total": self.total_violations,
            "compliance_score": self.compliance_score(),
            "violations": [item.to_dict() for item in self.violations],
            "violations_by_file": grouped,
        }


class Validator:
    def __init__(self, rules: Dict[str, Any], project_paths: ProjectPaths) -> None:
        self.rules = rules
        self.project_paths = project_paths
        self.active_rules = [
            "syntax_valid",
            "main_max_lines",
            "no_print",
            "type_hints_required",
            "max_file_lines",
            "max_line_length",
            "no_hardcoded_values",
            "absolute_imports_only",
            "complexity_limit",
        ]
        self.max_complexity = 12

    def run(self) -> ValidationReport:
        results: List[FileValidationResult] = []
        all_violations: List[RuleViolation] = []

        for file_path in self._iter_target_files():
            result = self._validate_file(file_path)
            results.append(result)
            all_violations.extend(result.violations)

        report = ValidationReport(files=results, rules_count=len(self.active_rules), violations=all_violations)
        if report.total_violations == 0:
            LOGGER.info("Validation completed with no contract violations.")
        else:
            LOGGER.warning("Validation found %s violations across %s files.", report.total_violations, report.files_scanned)
        return report

    def _iter_target_files(self) -> Iterable[Path]:
        yield from self.project_paths.iter_python_files()

    def _validate_file(self, file_path: Path) -> FileValidationResult:
        result = FileValidationResult(path=file_path)
        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            LOGGER.error("Failed to read %s: %s", file_path, exc)
            return result

        lines = source.splitlines()
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            result.add(
                RuleViolation(
                    rule="syntax_valid",
                    message=f"Syntax error: {exc.msg}",
                    file_path=file_path,
                    line=exc.lineno,
                )
            )
            LOGGER.error("Syntax error while parsing %s: %s", file_path, exc)
            return result

        self._check_main_length(file_path, lines, result)
        self._check_no_print(tree, file_path, result)
        self._check_type_hints(tree, file_path, result)
        self._check_max_file_lines(file_path, lines, result)
        self._check_line_length(file_path, lines, result)
        self._check_no_hardcoded_values(tree, file_path, result)
        self._check_imports(tree, file_path, result)
        self._check_complexity(tree, file_path, result)

        return result

    def _check_main_length(self, file_path: Path, lines: List[str], result: FileValidationResult) -> None:
        if file_path.name != "main.py":
            return
        max_lines = int(self.rules.get("main_max_lines", 4))
        if len([line for line in lines if line.strip()]) > max_lines:
            result.add(
                RuleViolation(
                    rule="main_max_lines",
                    message=f"main.py exceeds {max_lines} non-empty lines.",
                    file_path=file_path,
                )
            )

    def _check_no_print(self, tree: ast.AST, file_path: Path, result: FileValidationResult) -> None:
        class PrintVisitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.issues: List[int] = []

            def visit_Call(self, node: ast.Call) -> None:
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    self.issues.append(node.lineno)
                self.generic_visit(node)

        visitor = PrintVisitor()
        visitor.visit(tree)
        for lineno in visitor.issues:
            result.add(
                RuleViolation(
                    rule="no_print",
                    message="print() usage detected; use structured logging instead.",
                    file_path=file_path,
                    line=lineno,
                )
            )

    def _check_type_hints(self, tree: ast.AST, file_path: Path, result: FileValidationResult) -> None:
        missing: List[Tuple[str, int]] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                args_without_hint = [
                    arg.arg
                    for arg in (*node.args.args, *node.args.kwonlyargs)
                    if arg.arg not in {"self", "cls"} and arg.annotation is None
                ]
                if node.args.vararg and node.args.vararg.annotation is None:
                    args_without_hint.append(node.args.vararg.arg)
                if node.args.kwarg and node.args.kwarg.annotation is None:
                    args_without_hint.append(node.args.kwarg.arg)
                if node.returns is None and node.name != "__init__":
                    missing.append((node.name, node.lineno))
                elif args_without_hint:
                    missing.append((node.name, node.lineno))

        for func_name, lineno in missing:
            result.add(
                RuleViolation(
                    rule="type_hints_required",
                    message=f"Function '{func_name}' is missing full type hints.",
                    file_path=file_path,
                    line=lineno,
                )
            )

    def _check_max_file_lines(self, file_path: Path, lines: Sequence[str], result: FileValidationResult) -> None:
        max_lines = int(self.rules.get("max_file_lines", 300))
        if len(lines) > max_lines:
            result.add(
                RuleViolation(
                    rule="max_file_lines",
                    message=f"File exceeds {max_lines} lines.",
                    file_path=file_path,
                    line=max_lines + 1,
                )
            )

    def _check_line_length(self, file_path: Path, lines: Sequence[str], result: FileValidationResult) -> None:
        max_len = int(self.rules.get("max_line_length", 79))
        for index, line in enumerate(lines, start=1):
            if len(line) > max_len:
                result.add(
                    RuleViolation(
                        rule="max_line_length",
                        message=f"Line length {len(line)} exceeds limit {max_len}.",
                        file_path=file_path,
                        line=index,
                    )
                )

    def _check_no_hardcoded_values(self, tree: ast.AST, file_path: Path, result: FileValidationResult) -> None:
        suspicious_tokens = ("sk-", "api_key", "apikey", "secret", "password", "passwd", "token")
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.strip().startswith("#"):  # comments ignored
                    continue
                lowered = node.value.lower()
                if any(marker in lowered for marker in suspicious_tokens):
                    result.add(
                        RuleViolation(
                            rule="no_hardcoded_values",
                            message="Suspicious hardcoded string literal detected.",
                            file_path=file_path,
                            line=getattr(node, "lineno", None),
                        )
                    )

    def _check_imports(self, tree: ast.AST, file_path: Path, result: FileValidationResult) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level > 0:
                result.add(
                    RuleViolation(
                        rule="absolute_imports_only",
                        message="Relative import detected.",
                        file_path=file_path,
                        line=node.lineno,
                    )
                )

    def _check_complexity(self, tree: ast.AST, file_path: Path, result: FileValidationResult) -> None:
        global COMPLEXITY_WARNING_EMITTED
        if ComplexityVisitor is None:
            if not COMPLEXITY_WARNING_EMITTED:
                LOGGER.warning("ComplexityVisitor unavailable; install 'radon' to enable complexity checks.")
                COMPLEXITY_WARNING_EMITTED = True
            return
        try:
            visitor = ComplexityVisitor.from_ast(tree)
        except Exception as exc:
            LOGGER.error("Complexity analysis failed for %s: %s", file_path, exc)
            return

        for block in visitor.blocks:
            if block.complexity > self.max_complexity:
                result.add(
                    RuleViolation(
                        rule="complexity_limit",
                        message=f"Block '{block.name}' complexity {block.complexity} exceeds {self.max_complexity}.",
                        file_path=file_path,
                        line=block.lineno,
                    )
                )


def generate_console_summary(report: ValidationReport) -> str:
    header = "گزارش اعتبارسنجی قرارداد صفر خطا"
    status = "وضعیت: همه‌چیز عالی است." if report.total_violations == 0 else "وضعیت: نیاز به اصلاح دارد."
    details = (
        f"تعداد فایل‌های بررسی‌شده: {report.files_scanned}\n"
        f"مجموع قوانین ارزیابی‌شده: {report.rules_count}\n"
        f"تعداد تخلفات: {report.total_violations}\n"
        f"امتیاز تطابق: {report.compliance_score()}٪"
    )
    offending = ""
    if report.total_violations > 0:
        offenders = {str(item.file_path) for item in report.violations}
        joined = "\n".join(f"- {path}" for path in sorted(offenders))
        offending = f"\nفایل‌های دارای تخلف:\n{joined}"
    return f"{header}\n{status}\n{details}{offending}"


def main() -> None:
    rules = load_contract_rules()
    paths = load_project_paths()
    validator = Validator(rules=rules, project_paths=paths)
    report = validator.run()
    payload = report.to_dict()
    store_report(payload)
    summary = generate_console_summary(report)
    emit_ui_message(summary)


if __name__ == "__main__":
    main()

"""
Zero Tolerance Validator Engine
Core validation engine with support for multiple rule types

Key Features:
- Zero Tolerance rule validation
- Multi-language support (Python, TypeScript, JavaScript)
- AST analysis for deeper inspection
- Detailed violation reporting
- Learning system integration
"""

import ast
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import json

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from enforcement.utils import get_logger, load_contract_rules, emit_ui_message

logger = get_logger("zero_tolerance.validator")


@dataclass
class Violation:
    """Represents a rule violation"""
    rule_id: str
    message: str
    severity: str  # critical, warning, info
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None
    file_path: Optional[str] = None


@dataclass 
class ValidationResult:
    """Result of file validation"""
    file_path: str
    violations: List[Violation]
    stats: Dict[str, Any]
    execution_time: float
    timestamp: str


class ValidatorEngine:
    """Zero Tolerance main validation engine"""
    
    def __init__(self):
        self.rules = {}
        self.patterns = {}
        self.load_rules()
        logger.info("Validator engine initialized with rules loaded")
    
    def load_rules(self) -> None:
        """Load rules from configuration file"""
        try:
            self.rules = load_contract_rules()
            self._compile_patterns()
            logger.info(f"Loaded {len(self.rules)} validation rules")
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            self.rules = self._get_default_rules()
            self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for better performance"""
        self.patterns = {}
        
        # Common patterns
        self.patterns['print_statements'] = re.compile(
            r'(?:^|\s)(print|console\.log|echo|puts|println|printf)\s*\(',
            re.MULTILINE | re.IGNORECASE
        )
        
        self.patterns['hardcoded_strings'] = re.compile(
            r'(?:password|token|key|secret|api_key)\s*[=:]\s*["\'][^"\']{3,}["\']',
            re.IGNORECASE
        )
        
        self.patterns['absolute_imports'] = re.compile(
            r'^from\s+(?!\.)',
            re.MULTILINE
        )
        
        self.patterns['long_lines'] = re.compile(r'^.{121,}$', re.MULTILINE)
        
        logger.debug("Regex patterns compiled successfully")
    
    def validate_file(self, file_path: Union[str, Path]) -> ValidationResult:
        """Validate a complete file"""
        start_time = datetime.now()
        file_path = Path(file_path)
        violations = []
        
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect file type
            file_type = self._detect_file_type(file_path)
            
            if file_type == 'unsupported':
                logger.warning(f"Unsupported file type: {file_path}")
                return self._create_result(file_path, [], start_time, {"skipped": True})
            
            # Run various checks
            violations.extend(self._check_basic_rules(content, file_path))
            
            if file_type == 'python':
                violations.extend(self._check_python_specific(content, file_path))
            elif file_type in ['javascript', 'typescript']:
                violations.extend(self._check_js_specific(content, file_path))
            
            # File statistics
            stats = self._calculate_file_stats(content, violations)
            
            logger.info(f"Validated {file_path}: {len(violations)} violations found")
            
        except Exception as e:
            logger.error(f"Validation failed for {file_path}: {e}")
            violations.append(Violation(
                rule_id="validation_error",
                message=f"Validation failed: {str(e)}",
                severity="critical",
                file_path=str(file_path)
            ))
            stats = {"error": True}
        
        return self._create_result(file_path, violations, start_time, stats)
    
    def validate_content(self, content: str, file_path: str = "unknown", 
                        language: str = "python") -> ValidationResult:
        """Validate content directly (for API usage)"""
        start_time = datetime.now()
        violations = []
        
        try:
            # Basic checks
            violations.extend(self._check_basic_rules(content, file_path))
            
            # Language-specific checks
            if language == 'python':
                violations.extend(self._check_python_specific(content, file_path))
            elif language in ['javascript', 'typescript']:
                violations.extend(self._check_js_specific(content, file_path))
            
            stats = self._calculate_file_stats(content, violations)
            
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            violations.append(Violation(
                rule_id="validation_error", 
                message=f"Validation failed: {str(e)}",
                severity="critical",
                file_path=file_path
            ))
            stats = {"error": True}
        
        return self._create_result(file_path, violations, start_time, stats)
    
    def _check_basic_rules(self, content: str, file_path: Union[str, Path]) -> List[Violation]:
        """Check basic common rules"""
        violations = []
        lines = content.split('\n')
        
        # Check line length
        max_line_length = self.rules.get('max_line_length', {}).get('limit', 120)
        for i, line in enumerate(lines, 1):
            if len(line) > max_line_length:
                violations.append(Violation(
                    rule_id="max_line_length",
                    message=f"Line too long ({len(line)} > {max_line_length})",
                    severity="warning",
                    line=i,
                    column=max_line_length + 1,
                    context=line[:50] + "..." if len(line) > 50 else line,
                    suggestion=f"Break this line into multiple lines",
                    file_path=str(file_path)
                ))
        
        # Check print statements
        if self.rules.get('no_print', {}).get('enabled', True):
            for match in self.patterns['print_statements'].finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                violations.append(Violation(
                    rule_id="no_print",
                    message="Print statement found - use structured logging instead",
                    severity="critical",
                    line=line_num,
                    column=match.start() - content.rfind('\n', 0, match.start()),
                    context=match.group().strip(),
                    suggestion="Replace with proper logging: logger.info(...)",
                    file_path=str(file_path)
                ))
        
        # Check hardcoded values
        if self.rules.get('no_hardcoded_values', {}).get('enabled', True):
            for match in self.patterns['hardcoded_strings'].finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                violations.append(Violation(
                    rule_id="no_hardcoded_values",
                    message="Hardcoded sensitive value detected",
                    severity="critical", 
                    line=line_num,
                    column=match.start() - content.rfind('\n', 0, match.start()),
                    context=match.group()[:30] + "...",
                    suggestion="Use environment variables or config files",
                    file_path=str(file_path)
                ))
        
        # Check large files
        max_file_length = self.rules.get('max_file_length', {}).get('limit', 500)
        if len(lines) > max_file_length:
            violations.append(Violation(
                rule_id="max_file_length",
                message=f"File too long ({len(lines)} > {max_file_length} lines)",
                severity="warning",
                line=len(lines),
                suggestion="Consider breaking this file into smaller modules",
                file_path=str(file_path)
            ))
        
        return violations
    
    def _check_python_specific(self, content: str, file_path: Union[str, Path]) -> List[Violation]:
        """Python-specific checks"""
        violations = []
        
        try:
            # Parse AST for complex checks
            tree = ast.parse(content)
            
            # Check type hints
            if self.rules.get('type_hints_required', {}).get('enabled', True):
                violations.extend(self._check_type_hints(tree, file_path))
            
            # Check complexity
            violations.extend(self._check_complexity(tree, file_path))
            
            # Check absolute imports
            violations.extend(self._check_absolute_imports(content, file_path))
            
        except SyntaxError as e:
            violations.append(Violation(
                rule_id="syntax_error",
                message=f"Python syntax error: {e.msg}",
                severity="critical",
                line=e.lineno,
                column=e.offset,
                suggestion="Fix the syntax error",
                file_path=str(file_path)
            ))
        except Exception as e:
            logger.warning(f"Python AST analysis failed for {file_path}: {e}")
        
        return violations
    
    def _check_js_specific(self, content: str, file_path: Union[str, Path]) -> List[Violation]:
        """JavaScript/TypeScript specific checks"""
        violations = []
        
        # Check console.log
        for match in re.finditer(r'console\.log\s*\(', content):
            line_num = content[:match.start()].count('\n') + 1
            violations.append(Violation(
                rule_id="no_console_log",
                message="console.log statement found",
                severity="warning",
                line=line_num,
                suggestion="Use proper logging framework",
                file_path=str(file_path)
            ))
        
        # Check var declarations
        for match in re.finditer(r'\bvar\s+\w+', content):
            line_num = content[:match.start()].count('\n') + 1
            violations.append(Violation(
                rule_id="no_var_declarations",
                message="Use 'let' or 'const' instead of 'var'",
                severity="warning",
                line=line_num,
                suggestion="Replace 'var' with 'let' or 'const'",
                file_path=str(file_path)
            ))
        
        return violations
    
    def _check_type_hints(self, tree: ast.AST, file_path: Union[str, Path]) -> List[Violation]:
        """Check type hints in Python"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check return type
                if node.returns is None and node.name != '__init__':
                    violations.append(Violation(
                        rule_id="missing_return_type",
                        message=f"Function '{node.name}' missing return type annotation",
                        severity="warning",
                        line=node.lineno,
                        suggestion="Add -> ReturnType to function signature",
                        file_path=str(file_path)
                    ))
                
                # Check parameter types
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != 'self':
                        violations.append(Violation(
                            rule_id="missing_parameter_type",
                            message=f"Parameter '{arg.arg}' in function '{node.name}' missing type annotation",
                            severity="info",
                            line=node.lineno,
                            suggestion=f"Add type annotation: {arg.arg}: Type",
                            file_path=str(file_path)
                        ))
        
        return violations
    
    def _check_complexity(self, tree: ast.AST, file_path: Union[str, Path]) -> List[Violation]:
        """Check Cyclomatic complexity"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                max_complexity = self.rules.get('max_complexity', {}).get('limit', 10)
                
                if complexity > max_complexity:
                    violations.append(Violation(
                        rule_id="high_complexity",
                        message=f"Function '{node.name}' has high complexity ({complexity} > {max_complexity})",
                        severity="warning",
                        line=node.lineno,
                        suggestion="Consider breaking this function into smaller functions",
                        file_path=str(file_path)
                    ))
        
        return violations
    
    def _check_absolute_imports(self, content: str, file_path: Union[str, Path]) -> List[Violation]:
        """Check use of absolute imports"""
        violations = []
        
        if self.rules.get('absolute_imports_only', {}).get('enabled', False):
            for match in re.finditer(r'^from\s+\.', content, re.MULTILINE):
                line_num = content[:match.start()].count('\n') + 1
                violations.append(Violation(
                    rule_id="relative_import",
                    message="Relative import found - use absolute imports",
                    severity="info",
                    line=line_num,
                    suggestion="Convert to absolute import",
                    file_path=str(file_path)
                ))
        
        return violations
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate Cyclomatic complexity"""
        complexity = 1  # base
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _detect_file_type(self, file_path: Path) -> str:
        """Detect file type"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.py':
            return 'python'
        elif suffix in ['.js', '.jsx']:
            return 'javascript'
        elif suffix in ['.ts', '.tsx']:
            return 'typescript'
        else:
            return 'unsupported'
    
    def _calculate_file_stats(self, content: str, violations: List[Violation]) -> Dict[str, Any]:
        """Calculate file statistics"""
        lines = content.split('\n')
        
        return {
            "total_lines": len(lines),
            "code_lines": len([line for line in lines if line.strip() and not line.strip().startswith('#')]),
            "comment_lines": len([line for line in lines if line.strip().startswith('#')]),
            "blank_lines": len([line for line in lines if not line.strip()]),
            "violations_count": len(violations),
            "violations_by_severity": {
                "critical": len([v for v in violations if v.severity == "critical"]),
                "warning": len([v for v in violations if v.severity == "warning"]), 
                "info": len([v for v in violations if v.severity == "info"])
            },
            "file_size_bytes": len(content.encode('utf-8'))
        }
    
    def _create_result(self, file_path: Union[str, Path], violations: List[Violation], 
                      start_time: datetime, stats: Dict[str, Any]) -> ValidationResult:
        """Create final result"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationResult(
            file_path=str(file_path),
            violations=violations,
            stats=stats,
            execution_time=execution_time,
            timestamp=datetime.now().isoformat()
        )
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """Default rules when configuration file is unavailable"""
        return {
            "max_line_length": {"enabled": True, "limit": 120},
            "no_print": {"enabled": True},
            "no_hardcoded_values": {"enabled": True},
            "max_file_length": {"enabled": True, "limit": 500},
            "type_hints_required": {"enabled": True},
            "max_complexity": {"enabled": True, "limit": 10},
            "absolute_imports_only": {"enabled": False}
        }
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """Summary of active rules"""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.get('enabled', True)]),
            "rule_list": list(self.rules.keys()),
            "patterns_compiled": len(self.patterns)
        }


# Helper function for direct usage
def quick_validate(file_path: str) -> Dict[str, Any]:
    """Quick validation of a file"""
    engine = ValidatorEngine()
    result = engine.validate_file(file_path)
    
    return {
        "file": result.file_path,
        "violations": len(result.violations),
        "critical": len([v for v in result.violations if v.severity == "critical"]),
        "warnings": len([v for v in result.violations if v.severity == "warning"]),
        "execution_time": result.execution_time
    }


if __name__ == "__main__":
    # Simple test
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = quick_validate(file_path)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python validator_engine.py <file_path>")

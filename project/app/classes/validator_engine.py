"""Zero Tolerance Python Contract Enforcer
Validator Engine Class
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import ast
from app.utils.helpers import (
    validate_line_length,
    extract_hardcoded_values,
    find_print_statements,
    validate_imports,
    validate_type_hints
)


class ValidatorEngine:
    """Core validation engine for contract enforcement."""
    
    def __init__(self, rules: Dict[str, Any]):
        """Initialize validator engine with rules.
        
        Args:
            rules: Contract validation rules
        """
        self.rules = rules
        self.max_line_length = rules.get('max_line_length', 79)
        self.main_max_lines = rules.get('main_max_lines', 4)
        self.no_print = rules.get('no_print', True)
        self.type_hints_required = rules.get('type_hints_required', True)
        self.max_file_lines = rules.get('max_file_lines', 300)
        self.no_hardcoded_values = rules.get('no_hardcoded_values', True)
        self.absolute_imports_only = rules.get('absolute_imports_only', True)
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single file against all rules.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dictionary containing validation results
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252']:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return {
                    'file': str(file_path),
                    'errors': ['Could not decode file'],
                    'violations': []
                }
        
        violations = []
        file_lines = content.split('\n')
        tree = None
        
        # Parse AST for more complex validations
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {
                'file': str(file_path),
                'errors': [f'Syntax error: {str(e)}'],
                'violations': []
            }
        
        # Check main.py line count
        if file_path.name == 'main.py' and len(file_lines) > \
        self.main_max_lines:
            violations.append({
                'rule': 'main_max_lines',
                'message': f'main.py exceeds {self.main_max_lines} lines \
                ({len(file_lines)} lines)',
                'line': len(file_lines),
                'severity': 'error'
            })
        
        # Check file size
        if len(file_lines) > self.max_file_lines:
            violations.append({
                'rule': 'max_file_lines',
                'message': f'File exceeds {self.max_file_lines} lines \
                ({len(file_lines)} lines)',
                'line': len(file_lines),
                'severity': 'warning'
            })
        
        # Validate line length
        if len(file_lines) > 1:  # Only check if file has content
            line_violations = validate_line_length(content, \
            self.max_line_length)
            for violation in line_violations:
                violations.append({
                    'rule': 'line_length',
                    'message': f'Line {violation["line"]} exceeds \
                    {self.max_line_length} characters ({violation["length"]} \
                    chars)',
                    'line': violation['line'],
                    'severity': 'warning'
                })
        
        # Validate hardcoded values
        if self.no_hardcoded_values and tree:
            hardcoded_values = extract_hardcoded_values(content)
            for value in hardcoded_values:
                violations.append({
                    'rule': 'hardcoded_values',
                    'message': f'Hardcoded {value["type"]}: \
                    {repr(value["value"])} at line {value["line"]}',
                    'line': value['line'],
                    'severity': 'error'
                })
        
        # Validate print statements
        if self.no_print and tree:
            print_calls = find_print_statements(content)
            for call in print_calls:
                violations.append({
                    'rule': 'no_print',
                    'message': f'Print statement found at line {call["line"]}',
                    'line': call['line'],
                    'severity': 'error'
                })
        
        # Validate imports
        if self.absolute_imports_only and tree:
            import_violations = validate_imports(content)
            for violation in import_violations:
                violations.append({
                    'rule': 'absolute_imports_only',
                    'message': f'Relative import found: \
                    {violation["module"]} at line {violation["line"]}',
                    'line': violation['line'],
                    'severity': 'error'
                })
        
        # Validate type hints
        if self.type_hints_required and tree:
            type_hint_violations = validate_type_hints(content)
            for violation in type_hint_violations:
                violations.append({
                    'rule': 'type_hints_required',
                    'message': f'Function {violation["function"]} missing \
                    type hints at line {violation["line"]}',
                    'line': violation['line'],
                    'severity': 'warning'
                })
        
        return {
            'file': str(file_path),
            'errors': [],
            'violations': violations
        }
    
    def validate_project(self, project_path: Path) -> Dict[str, Any]:
        """Validate entire project against all rules.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary containing comprehensive validation results
        """
        results = {
            'project': str(project_path),
            'files_validated': 0,
            'total_violations': 0,
            'violations_by_file': {},
            'summary': {
                'errors': 0,
                'warnings': 0,
                'errors_by_rule': {},
                'warnings_by_rule': {}
            }
        }
        
        # Get include/exclude patterns from rules
        include_patterns = self.rules.get('include_globs', ['**/*.py'])
        exclude_patterns = self.rules.get('exclude_globs', [])
        
        # Find Python files to validate
        python_files = set()
        for pattern in include_patterns:
            python_files.update(project_path.glob(pattern))
        
        # Remove excluded files
        for pattern in exclude_patterns:
            excluded_files = set(project_path.glob(pattern))
            python_files -= excluded_files
        
        # Validate each file
        for file_path in python_files:
            if file_path.suffix == '.py':
                validation_result = self.validate_file(file_path)
                results['files_validated'] += 1
                
                # Add violations to results
                if validation_result['violations']:
                    results['violations_by_file'][str(file_path)] = \
                    validation_result['violations']
                    results['total_violations'] += \
                    len(validation_result['violations'])
                    
                    # Count by severity and rule
                    for violation in validation_result['violations']:
                        rule = violation['rule']
                        severity = violation['severity']
                        
                        if severity == 'error':
                            results['summary']['errors'] += 1
                            results['summary']['errors_by_rule'][rule] = \
                            results['summary']['errors_by_rule'].get(rule, \
                            0) + 1
                        else:
                            results['summary']['warnings'] += 1
                            results['summary']['warnings_by_rule'][rule] = \
                            results['summary']['warnings_by_rule'].get(rule, \
                            0) + 1
        
        # Calculate compliance score
        # Assume max 10 violations per file for scoring
        total_possible_violations = results['files_validated'] * 10
        if total_possible_violations > 0:
            compliance_score = ((total_possible_violations - \
            results['total_violations']) / total_possible_violations) * 100
            results['compliance_score'] = max(0, min(100, compliance_score))
        else:
            results['compliance_score'] = 100.0
        
        return results


class ValidationReport:
    """Container for validation report data."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize validation report.
        
        Args:
            data: Raw validation data
        """
        self.data = data
        self.files_scanned = data.get('files_validated', 0)
        self.total_violations = data.get('total_violations', 0)
        self.violations_by_file = data.get('violations_by_file', {})
        self.compliance_score = data.get('compliance_score', 0.0)
        self.project_path = data.get('project', '')
        self.summary = data.get('summary', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format.
        
        Returns:
            Dictionary representation of the report
        """
        return self.data
    
    def get_compliance_score(self) -> float:
        """Get compliance score as percentage.
        
        Returns:
            Compliance score (0-100)
        """
        return float(self.compliance_score)
    
    def has_violations(self) -> bool:
        """Check if report has any violations.
        
        Returns:
            True if violations exist, False otherwise
        """
        return self.total_violations > 0
    
    def get_violations_by_severity(self, severity: str) -> int:
        """Get count of violations by severity level.
        
        Args:
            severity: 'error' or 'warning'
            
        Returns:
            Number of violations with specified severity
        """
        if severity == 'error':
            return self.summary.get('errors', 0)
        elif severity == 'warning':
            return self.summary.get('warnings', 0)
        return 0
    
    def get_violations_by_rule(self, rule: str, severity: str = None) -> int:
        """Get count of violations by rule name.
        
        Args:
            rule: Rule name to count
            severity: Optional severity filter ('error' or 'warning')
            
        Returns:
            Number of violations for the specified rule
        """
        if severity == 'error':
            return self.summary.get('errors_by_rule', {}).get(rule, 0)
        elif severity == 'warning':
            return self.summary.get('warnings_by_rule', {}).get(rule, 0)
        else:
            # Return total for rule across all severities
            error_count = self.summary.get('errors_by_rule', {}).get(rule, 0)
            warning_count = self.summary.get('warnings_by_rule', \
            {}).get(rule, 0)
            return error_count + warning_count

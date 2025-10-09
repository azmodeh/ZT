"""Zero Tolerance Python Contract Enforcer
Utility Helper Functions
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import ast
import re


def validate_line_length(content: str, max_length: int = 79) -> List[Dict[str, Any]]:
    """Validate line length compliance.
    
    Args:
        content: File content to check
        max_length: Maximum line length allowed
        
    Returns:
        List of violations with line numbers and details
    """
    violations = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        if len(line) > max_length:
            violations.append({
                'line': i,
                'length': len(line),
                'max_length': max_length,
                'content': line[:50] + '...' if len(line) > 50 else line
            })
    
    return violations


def extract_hardcoded_values(content: str) -> List[Dict[str, Any]]:
    """Extract hardcoded strings and numbers from content.
    
    Args:
        content: File content to analyze
        
    Returns:
        List of hardcoded values with their locations
    """
    tree = ast.parse(content)
    hardcoded_values = []
    
    class HardcodedValueVisitor(ast.NodeVisitor):
        def visit_Str(self, node):
            if len(node.s) > 0:  # Non-empty strings
                hardcoded_values.append({
                    'type': 'string',
                    'value': node.s,
                    'line': node.lineno,
                    'col': node.col_offset
                })
            self.generic_visit(node)
        
        def visit_Num(self, node):
            # Exclude common numeric literals that are usually OK
            if not isinstance(node.n, (int, float)) or abs(node.n) > 1:
                hardcoded_values.append({
                    'type': 'number',
                    'value': node.n,
                    'line': node.lineno,
                    'col': node.col_offset
                })
            self.generic_visit(node)
        
        def visit_Constant(self, node):
            # Handle different constant types safely
            if isinstance(node.value, (str, int, float)):
                if node.value != 0 and node.value != 1 and node.value != '':
                    hardcoded_values.append({
                        'type': type(node.value).__name__,
                        'value': node.value,
                        'line': node.lineno,
                        'col': node.col_offset
                    })
            self.generic_visit(node)
    
    visitor = HardcodedValueVisitor()
    visitor.visit(tree)
    
    return hardcoded_values


def find_print_statements(content: str) -> List[Dict[str, Any]]:
    """Find print statements in content.
    
    Args:
        content: File content to analyze
        
    Returns:
        List of print statements with their locations
    """
    tree = ast.parse(content)
    print_calls = []
    
    class PrintCallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if (isinstance(node.func, ast.Name) and 
                node.func.id == 'print'):
                print_calls.append({
                    'line': node.lineno,
                    'col': node.col_offset,
                    'type': 'print_call'
                })
            self.generic_visit(node)
    
    visitor = PrintCallVisitor()
    visitor.visit(tree)
    
    return print_calls


def validate_imports(content: str) -> List[Dict[str, Any]]:
    """Validate import statements for relative import violations.
    
    Args:
        content: File content to analyze
        
    Returns:
        List of relative import violations
    """
    tree = ast.parse(content)
    violations = []
    
    class ImportVisitor(ast.NodeVisitor):
        def visit_ImportFrom(self, node):
            if node.module and node.module.startswith('.'):
                violations.append({
                    'line': node.lineno,
                    'col': node.col_offset,
                    'module': node.module,
                    'type': 'relative_import'
                })
            self.generic_visit(node)
    
    visitor = ImportVisitor()
    visitor.visit(tree)
    
    return violations


def validate_type_hints(content: str) -> List[Dict[str, Any]]:
    """Validate type hints on functions.
    
    Args:
        content: File content to analyze
        
    Returns:
        List of functions without type hints
    """
    tree = ast.parse(content)
    violations = []
    
    class TypeHintVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            # Check if function has return type annotation
            has_return_type = node.returns is not None
            
            # Check if all parameters have type annotations (except self/cls)
            missing_hints = []
            for arg in node.args.args:
                if arg.annotation is None:
                    if arg.arg not in ['self', 'cls']:
                        missing_hints.append(arg.arg)
            
            # Check if function has type hints
            has_param_hints = len(missing_hints) < len([a for a in node.args.args if a.arg not in ['self', 'cls']])
            
            if not (has_return_type or has_param_hints):
                violations.append({
                    'line': node.lineno,
                    'function': node.name,
                    'missing_params': missing_hints,
                    'has_return_type': has_return_type
                })
            
            self.generic_visit(node)
        
        def visit_AsyncFunctionDef(self, node):
            # Check if async function has return type annotation
            has_return_type = node.returns is not None
            
            # Check if all parameters have type annotations (except self/cls)
            missing_hints = []
            for arg in node.args.args:
                if arg.annotation is None:
                    if arg.arg not in ['self', 'cls']:
                        missing_hints.append(arg.arg)
            
            # Check if function has type hints
            has_param_hints = len(missing_hints) < len([a for a in node.args.args if a.arg not in ['self', 'cls']])
            
            if not (has_return_type or has_param_hints):
                violations.append({
                    'line': node.lineno,
                    'function': node.name,
                    'missing_params': missing_hints,
                    'has_return_type': has_return_type
                })
            
            self.generic_visit(node)
    
    visitor = TypeHintVisitor()
    visitor.visit(tree)
    
    return violations


def format_code_content(content: str) -> str:
    """Format code content for consistency.
    
    Args:
        content: Raw code content
        
    Returns:
        Formatted code content
    """
    # Ensure consistent line endings
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove trailing whitespace
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    
    # Ensure file ends with newline
    if lines and lines[-1] != '':
        lines.append('')
    
    return '\n'.join(lines)


def get_file_encoding(file_path: Path) -> str:
    """Detect file encoding.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected encoding
    """
    # Try common encodings in order of preference
    encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    
    return 'utf-8'  # Default fallback


def safe_read_file(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """Safely read file content with encoding detection.
    
    Args:
        file_path: Path to the file
        encoding: File encoding (auto-detected if not provided)
        
    Returns:
        File content or None if error
    """
    try:
        if encoding == 'auto':
            encoding = get_file_encoding(file_path)
        
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encodings
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return None
    except Exception:
        return None


def safe_write_file(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """Safely write file content.
    
    Args:
        file_path: Path to write to
        content: Content to write
        encoding: File encoding
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False

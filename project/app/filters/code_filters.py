"""Zero Tolerance Python Contract Enforcer
Code Filters and Transformers
"""

from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import ast
import re


class CodeFilter:
    """Base class for code filters and transformations."""
    
    def __init__(self, name: str, description: str):
        """Initialize code filter.
        
        Args:
            name: Filter name
            description: Filter description
        """
        self.name = name
        self.description = description
    
    def apply(self, content: str, file_path: Path) -> str:
        """Apply filter to code content.
        
        Args:
            content: Original code content
            file_path: Path to the file being filtered
            
        Returns:
            Filtered code content
        """
        raise NotImplementedError("Subclasses must implement apply method")


class LineLengthFilter(CodeFilter):
    """Filter to handle line length violations by wrapping long lines."""
    
    def __init__(self, max_length: int = 79):
        """Initialize line length filter.
        
        Args:
            max_length: Maximum line length allowed
        """
        super().__init__("line_length_filter", "Wrap lines exceeding maximum length")
        self.max_length = max_length
    
    def apply(self, content: str, file_path: Path) -> str:
        """Apply line wrapping to long lines.
        
        Args:
            content: Original code content
            file_path: Path to the file being filtered
            
        Returns:
            Content with wrapped long lines
        """
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            if len(line) <= self.max_length:
                filtered_lines.append(line)
            else:
                # Try to wrap at logical break points
                wrapped = self._wrap_line(line)
                filtered_lines.extend(wrapped)
        
        return '\n'.join(filtered_lines)
    
    def _wrap_line(self, line: str) -> List[str]:
        """Wrap a single line at appropriate break points.
        
        Args:
            line: Line to wrap
            
        Returns:
            List of wrapped line segments
        """
        if len(line) <= self.max_length:
            return [line]
        
        # Look for function call parentheses
        if '(' in line and ')' in line:
            return self._wrap_function_call(line)
        
        # Look for list/dict/set brackets
        if '[' in line or '{' in line or '(' in line:
            return self._wrap_collection(line)
        
        # Simple word-based wrapping as fallback
        return self._wrap_simple(line)
    
    def _wrap_function_call(self, line: str) -> List[str]:
        """Wrap function call lines."""
        # Find the opening parenthesis
        paren_pos = line.find('(')
        if paren_pos == -1:
            return self._wrap_simple(line)
        
        function_part = line[:paren_pos + 1]
        args_part = line[paren_pos + 1:]
        
        if len(line) <= self.max_length:
            return [line]
        
        # Try to break at commas
        args = []
        current_arg = ""
        paren_count = 0
        i = 0
        
        while i < len(args_part):
            char = args_part[i]
            if char in '([{':
                paren_count += 1
                current_arg += char
            elif char in ')]}':
                paren_count -= 1
                current_arg += char
            elif char == ',' and paren_count == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
            i += 1
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        if len(args) <= 1:
            return self._wrap_simple(line)
        
        # Format with each argument on separate line
        result = [function_part]
        for i, arg in enumerate(args):
            if i == len(args) - 1:  # Last argument includes closing paren
                closing = arg.split(')')
                if len(closing) > 1:
                    result.append(f"    {closing[0].strip()}")
                    result.append(f"){closing[1]}")
                else:
                    result.append(f"    {arg.strip()}")
            else:
                result.append(f"    {arg.strip()},")
        
        # Combine with proper indentation
        wrapped = [result[0]]
        for part in result[1:]:
            current_line = wrapped[-1] + part
            if len(current_line) > self.max_length:
                wrapped.append(part)
            else:
                wrapped[-1] = current_line
        
        return wrapped if len(wrapped) > 1 else [line]  # Fallback if wrapping didn't help
    
    def _wrap_collection(self, line: str) -> List[str]:
        """Wrap collection literal lines."""
        # Simple wrapping for long collections
        words = line.split()
        wrapped = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) <= self.max_length:
                current_line = test_line
            else:
                if current_line:
                    wrapped.append(current_line)
                current_line = word
        
        if current_line:
            wrapped.append(current_line)
        
        return wrapped if len(wrapped) > 1 else [line]
    
    def _wrap_simple(self, line: str) -> List[str]:
        """Simple word-based line wrapping."""
        words = line.split()
        wrapped = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) <= self.max_length:
                current_line = test_line
            else:
                if current_line:
                    wrapped.append(current_line)
                current_line = word
        
        if current_line:
            wrapped.append(current_line)
        
        return wrapped if len(wrapped) > 1 else [line]


class ImportFilter(CodeFilter):
    """Filter to convert relative imports to absolute imports."""
    
    def __init__(self):
        """Initialize import filter."""
        super().__init__("import_filter", "Convert relative imports to absolute imports")
    
    def apply(self, content: str, file_path: Path) -> str:
        """Convert relative imports to absolute imports.
        
        Args:
            content: Original code content
            file_path: Path to the file being filtered
            
        Returns:
            Content with absolute imports
        """
        lines = content.split('\n')
        filtered_lines = []
        project_root = self._find_project_root(file_path)
        
        for line in lines:
            if line.strip().startswith('from .') and ' import ' in line:
                new_line = self._convert_relative_import(line, file_path, project_root)
                filtered_lines.append(new_line)
            else:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _find_project_root(self, file_path: Path) -> Path:
        """Find project root by looking for common markers."""
        current = file_path.parent
        while current != current.parent:
            if (current / 'setup.py').exists() or (current / 'pyproject.toml').exists():
                return current
            current = current.parent
        return file_path.parent
    
    def _convert_relative_import(self, line: str, file_path: Path, project_root: Path) -> str:
        """Convert a relative import to absolute import."""
        # Extract the relative import part and what's being imported
        import_match = re.match(r'from\s+(\.+(?:\.\w*)?)\s+import\s+(.+)', line.strip())
        if not import_match:
            return line
        
        relative_part = import_match.group(1)
        imported_items = import_match.group(2)
        
        # Calculate the absolute module path
        current_module_parts = file_path.relative_to(project_root).with_suffix('').parts
        level = len(relative_part) - len(relative_part.lstrip('.'))
        target_parts = current_module_parts[:-level] if level > 0 else current_module_parts
        remaining = relative_part.lstrip('.')
        if remaining:
            target_parts = target_parts + (remaining,)
        
        absolute_module = '.'.join(target_parts) if target_parts else ''
        if absolute_module:
            return f'from {absolute_module} import {imported_items}'
        else:
            return f'import {imported_items}'


class PrintToLoggerFilter(CodeFilter):
    """Filter to convert print statements to logger calls."""
    
    def __init__(self):
        """Initialize print to logger filter."""
        super().__init__("print_to_logger_filter", "Convert print statements to logger calls")
        self.logger_import_added = False
    
    def apply(self, content: str, file_path: Path) -> str:
        """Convert print statements to logger calls.
        
        Args:
            content: Original code content
            file_path: Path to the file being filtered
            
        Returns:
            Content with print statements converted to logger calls
        """
        tree = ast.parse(content)
        self.logger_import_added = False
        
        # Check if logger import exists
        has_logger_import = self._has_logger_import(content)
        if not has_logger_import:
            content = self._add_logger_import(content)
            self.logger_import_added = True
        
        # Find and replace print calls
        lines = content.split('\n')
        modified_lines = []
        print_found = False
        
        for i, line in enumerate(lines):
            if self._is_print_line(line):
                new_line = self._convert_print_to_logger(line, i + 1)
                if new_line != line:
                    print_found = True
                modified_lines.append(new_line)
            else:
                modified_lines.append(line)
        
        return '\n'.join(modified_lines)
    
    def _has_logger_import(self, content: str) -> bool:
        """Check if logger import exists in content."""
        return 'get_logger(' in content or 'logger.' in content
    
    def _add_logger_import(self, content: str) -> str:
        """Add logger import to content."""
        lines = content.split('\n')
        insert_pos = 0
        
        # Find position to insert logger setup (after imports)
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and not line.startswith('import ') and not line.startswith('from '):
                insert_pos = i
                break
        
        logger_setup = [
            'from app.core.logger import get_logger',
            'logger = get_logger(__name__)'
        ]
        
        # Insert logger setup
        lines = lines[:insert_pos] + logger_setup + lines[insert_pos:]
        return '\n'.join(lines)
    
    def _is_print_line(self, line: str) -> bool:
        """Check if line contains a print statement."""
        line = line.strip()
        if line.startswith('print(') and line.endswith(')'):
            return True
        if line.startswith('print ') and 'print(' not in line:
            return True
        return False
    
    def _convert_print_to_logger(self, line: str, line_num: int) -> str:
        """Convert print statement to logger call."""
        stripped = line.strip()
        if stripped.startswith('print('):
            args = stripped[6:-1]  # Remove 'print(' and ')'
            return line.replace(f'print({args})', f'logger.info("line_{line_num}_output", extra={{"output": {args}}})')
        elif stripped.startswith('print '):
            args = stripped[6:]  # Remove 'print '
            return line.replace(f'print {args}', f'logger.info("line_{line_num}_output", extra={{"output": {args}}})')
        return line


class HardcodedValueFilter(CodeFilter):
    """Filter to extract hardcoded values to configuration."""
    
    def __init__(self):
        """Initialize hardcoded value filter."""
        super().__init__("hardcoded_value_filter", "Extract hardcoded values to configuration")
    
    def apply(self, content: str, file_path: Path) -> str:
        """Extract hardcoded values to configuration.
        
        Args:
            content: Original code content
            file_path: Path to the file being filtered
            
        Returns:
            Content with hardcoded values extracted
        """
        # This is a complex transformation that would require more sophisticated
        # analysis. For now, we'll return the content as-is but mark it for
        # future enhancement.
        return content


# Predefined filter collections
STANDARD_FILTERS = [
    LineLengthFilter(),
    ImportFilter(),
    PrintToLoggerFilter(),
    HardcodedValueFilter()
]


def apply_filters(content: str, file_path: Path, filters: List[CodeFilter]) -> str:
    """Apply a list of filters to content.
    
    Args:
        content: Original content
        file_path: Path to file
        filters: List of filters to apply
        
    Returns:
        Filtered content
    """
    result = content
    for filter_obj in filters:
        result = filter_obj.apply(result, file_path)
    return result

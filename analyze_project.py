"""
ZT Server Project Analysis Script
Analyzes all Python files and determines completion status
"""
import json
import sys
from pathlib import Path
import ast
import re

ROOT = Path('d:/Workdir/ZeroToleranceSystem/ZT')

def analyze_file(file_path):
    """Analyze a Python file and return its status"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = len(content.split('\n'))
        
        # Check for broken syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            return {
                'status': 'broken',
                'lines': lines,
                'reason': f'Syntax error: {e.msg}',
                'hint': 'Fix syntax errors'
            }
        
        # Check for common partial indicators
        todo_count = len(re.findall(r'#\s*TODO', content, re.IGNORECASE))
        pass_count = len(re.findall(r'^\s+pass\s*$', content, re.MULTILINE))
        not_impl_count = content.count('NotImplementedError')
        
        # Check for complete indicators
        has_logging = 'logger.' in content or 'logging.' in content
        has_error_handling = 'try:' in content and 'except' in content
        has_type_hints = '->' in content or ': ' in content
        has_docstrings = '"""' in content or "'''" in content
        
        # Count functions and classes
        func_count = len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE))
        class_count = len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE))
        
        # Determine status
        if lines < 50 and (pass_count > 2 or not_impl_count > 0):
            status = 'stub'
            reason = f'{pass_count} pass statements, {not_impl_count} NotImplementedError'
            percent = 20
        elif todo_count > 3 or (pass_count > 0 and lines < 100):
            status = 'partial'
            reason = f'{todo_count} TODOs, {pass_count} incomplete functions'
            percent = 50
        elif has_logging and has_error_handling and func_count > 3:
            status = 'complete'
            reason = 'Full logic, error handling, logging'
            percent = 100
        elif func_count > 5 and lines > 100:
            status = 'partial'
            reason = f'{func_count} functions but missing some polish'
            percent = 70
        else:
            status = 'partial'
            reason = 'Basic implementation'
            percent = 60
        
        return {
            'status': status,
            'lines': lines,
            'reason': reason,
            'percent': percent
        }
        
    except Exception as e:
        return {
            'status': 'broken',
            'lines': 0,
            'reason': str(e),
            'hint': 'File read error'
        }

def scan_project(root_path):
    """Scan entire project"""
    results = {
        'complete': [],
        'partial': [],
        'broken': [],
        'stub': []
    }
    
    # Find all Python files
    for py_file in root_path.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        rel_path = str(py_file.relative_to(root_path)).replace('\\', '/')
        analysis = analyze_file(py_file)
        
        file_info = {
            'file': rel_path,
            'lines': analysis['lines'],
            'reason': analysis['reason']
        }
        
        if analysis['status'] == 'complete':
            file_info['percent'] = 100
            results['complete'].append(file_info)
        elif analysis['status'] == 'partial':
            file_info['percent'] = analysis.get('percent', 60)
            results['partial'].append(file_info)
        elif analysis['status'] == 'stub':
            file_info['hint'] = analysis.get('hint', 'Implement functionality')
            results['stub'].append(file_info)
        else:
            file_info['hint'] = analysis.get('hint', 'Fix errors')
            results['broken'].append(file_info)
    
    return results

def analyze_architecture():
    """Analyze architectural issues"""
    issues = []
    
    # Check for duplicate validators
    main_validator = ROOT / 'enforcement' / 'validator_engine.py'
    sample_validator = ROOT / 'project' / 'app' / 'classes' / 'validator_engine.py'
    
    if main_validator.exists() and sample_validator.exists():
        issues.append("Duplicate validator_engine.py in enforcement/ and project/app/classes/")
    
    # Check for missing TypeScript components
    ts_watcher = ROOT / 'tools' / 'watch-zt.ts'
    if not ts_watcher.exists():
        issues.append("TypeScript watcher (tools/watch-zt.ts) referenced but missing")
    
    return issues

def generate_priorities(files_status):
    """Generate completion priority order"""
    priorities = []
    
    # Core dependencies first
    core_files = [
        ('enforcement/validator_engine.py', 'high', 'Core validation engine'),
        ('enforcement/diff_analyzer.py', 'high', 'Required by agents and learning'),
        ('enforcement/agent_manager.py', 'high', 'Orchestrates AI agents'),
        ('enforcement/auto_learning.py', 'medium', 'Learning system'),
        ('api_server/server.py', 'medium', 'REST API integration'),
        ('contract-enforcer-mcp/server.py', 'medium', 'MCP integration')
    ]
    
    for file, priority, reason in core_files:
        # Check if file is in partial status
        for f in files_status.get('partial', []):
            if f['file'] == file:
                priorities.append({
                    'file': file,
                    'priority': priority,
                    'reason': reason,
                    'estimated_effort': '2-4h' if priority == 'high' else '1-2h'
                })
                break
    
    return priorities

# Run full analysis
print("🔍 Analyzing ZT Server Project...")
results = scan_project(ROOT)
issues = analyze_architecture()
priorities = generate_priorities(results)

# Determine duplicates to remove
duplicates = []
if (ROOT / 'project' / 'app' / 'classes' / 'validator_engine.py').exists():
    duplicates.append('project/app/classes/validator_engine.py')

# Build final report
report = {
    'analysis_summary': {
        'total_files': sum(len(v) for v in results.values()),
        'complete': len(results['complete']),
        'partial': len(results['partial']),
        'broken': len(results['broken']),
        'stub': len(results['stub']),
        'missing_referenced': 1  # tools/watch-zt.ts
    },
    'files_by_status': results,
    'priority_completion_order': priorities,
    'architectural_issues': issues,
    'recommendations': {
        'start_with': 'enforcement/diff_analyzer.py',
        'remove_duplicates': duplicates,
        'next_phase': 'Complete async agent orchestration and improve VSCode extension build'
    },
    'missing_referenced': [
        {
            'file': 'tools/watch-zt.ts',
            'referenced_in': ['README.md', 'docs'],
            'priority': 'low'
        }
    ]
}

print(json.dumps(report, indent=2, ensure_ascii=False))

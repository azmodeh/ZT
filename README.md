# Zero Tolerance Python Contract Enforcer

A sophisticated Python code quality enforcement system that automatically validates, fixes, and maintains 12/12 contract compliance scores with MCP (Model Context Protocol) integration.

## 🎯 System Overview

This is a **Zero Tolerance Python Contract Enforcer** system that enforces strict Python coding standards through automated validation, fixing, and continuous integration. The system ensures 100% compliance with 12 critical Python development rules.

### 📋 12 Contract Rules (12/12 Required)

| Rule | Status | Description |
|------|--------|-------------|
| 1 | ✅ | `main.py` ≤4 lines maximum |
| 2 | ✅ | No hardcoded strings/numbers/URLs |
| 3 | ✅ | Zero `print()` statements |
| 4 | ✅ | All configuration from YAML files |
| 5 | ✅ | Type hints on every function |
| 6 | ✅ | PEP8 compliance (≤79 chars/line) |
| 7 | ✅ | Files ≤300 lines maximum |
| 8 | ✅ | Absolute imports only |
| 9 | ✅ | English logs / Persian UI |
| 10 | ✅ | Modular architecture |
| 11 | ✅ | Centralized logging |
| 12 | ✅ | Automated validation & fixing |

## 🏗️ Architecture

```
project/
├── main.py                    # ≤4 lines ABSOLUTE MAXIMUM
├── app/
│   ├── __init__.py           # Version info
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config_loader.py  # Configuration management
│   │   ├── logger.py         # Centralized logging
│   │   └── main_runner.py    # Application entry point
│   ├── classes/
│   │   ├── __init__.py
│   │   └── validator_engine.py # Validation engine
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py        # Utility functions
│   └── filters/
│       ├── __init__.py
│       └── code_filters.py   # Code transformation filters
├── enforcement/              # Core enforcement engine
│   ├── validator.py          # AST-based validation
│   ├── rewriter.py           # Auto-fixing system
│   ├── ai_agent.py           # AI-powered fixes
│   ├── ai_indexer.py         # Code indexing
│   ├── ai_queue.py           # Task queue
│   ├── ai_reviewer.py        # AI review system
│   ├── report_generator.py   # Compliance reporting
│   ├── utils.py              # Core utilities
│   ├── contract_rules.yml    # Rule definitions
│   └── requirements.txt      # Dependencies
├── data/
│   ├── config/
│   │   ├── settings.yml      # App configuration
│   │   └── logging.yml       # Log configuration
│   ├── templates/
│   ├── cache/                # Runtime cache
│   └── sessions/             # Session data
├── logs/                     # Validation logs
├── hooks/                    # Git hooks
├── contract-enforcer-mcp/    # MCP server
│   ├── server.py            # MCP server implementation
│   └── requirements.txt     # MCP dependencies
├── vscode/                   # VSCode integration
│   ├── settings.json        # MCP configuration
│   ├── tasks.json           # Build tasks
│   └── hooks/               # VSCode hooks
└── README.md               # This file
```

## 🚀 Features

### 1. **MCP Server Integration**
- `validate_code` - Full contract validation
- `fix_violations` - Auto-fixing system
- `generate_self_assessment` - Compliance reporting
- `check_compliance` - Overall status checking

### 2. **MCP Resources**
- `validation://latest-report` - Latest validation results
- `validation://history` - Complete validation history
- `validation://compliance-status` - Current compliance status

### 3. **VSCode Integration**
- 5 specialized build tasks:
  - ZT: Validate Contract
 - ZT: Auto Rewrite
  - ZT: Build AI Index
  - ZT: Run AI Agent (with prompt input)
 - ZT: Run Queue

### 4. **AI-Powered Enforcement**
- AI Agent for intelligent code fixes
- Code indexer for context-aware improvements
- Task queue for batch processing
- AI reviewer for quality assurance

### 5. **Advanced Validation**
- AST-based code analysis
- Line length validation (≤79 chars)
- Hardcoded value detection
- Print statement detection
- Import validation (absolute only)
- Type hint validation
- File size validation (≤300 lines)

## 🔧 Usage

### Command Line Usage
```bash
# Run the main application
python project/main.py

# Run validation directly
python enforcement/validator.py

# Run auto-fixer
python enforcement/rewriter.py

# Run AI agent with custom prompt
python enforcement/ai_agent.py "Fix line length violations"
```

### MCP Tools Usage
```python
# From any MCP-compatible client:
await client.call_tool("validate_code", {"base_path": "./project"})
await client.call_tool("fix_violations", {"base_path": "./project"})
await client.call_tool("check_compliance", {"base_path": "./project"})
```

### VSCode Tasks
Access through VSCode Command Palette (`Ctrl+Shift+P`):
- `Tasks: Run Task` → Select "ZT:" tasks

## 🎯 Self-Assessment Framework

The system provides comprehensive self-assessment with:

### Validation Report Structure
```json
{
  "project": "path/to/project",
  "files_validated": 15,
  "total_violations": 0,
  "compliance_score": 100.0,
  "violations_by_file": {},
  "summary": {
    "errors": 0,
    "warnings": 0,
    "errors_by_rule": {},
    "warnings_by_rule": {}
  }
}
```

### Compliance Scoring
- **100%**: All 12 rules passed
- **90-99%**: Minor violations allowed
- **<90%**: Fail - requires fixing

## 🤖 AI Integration

### AI Agent Capabilities
- Context-aware code fixes
- Pattern recognition
- Best practice recommendations
- Automated refactoring

### AI Queue System
- Batch processing of files
- Priority-based task management
- Progress tracking
- Error handling

## 📊 Validation Rules

### Rule 1: Main.py Size
- Maximum 4 lines in `main.py`
- Enforced automatically
- Violation: Immediate failure

### Rule 2: No Hardcoded Values
- No strings, numbers, or URLs in code
- Must use YAML configuration
- Enforced by AST analysis

### Rule 3: No Print Statements
- Zero `print()` allowed
- Use `logger.info()` instead
- Auto-converted by rewriter

### Rule 4: YAML Configuration
- All config from YAML files
- Centralized management
- Type-safe loading

### Rule 5: Type Hints
- Every function must have type hints
- Parameter and return types
- Enforced by validation

### Rule 6: PEP8 Compliance
- Maximum 79 characters per line
- Auto-wrapping by filters
- Line length validation

### Rule 7: File Size Limits
- Maximum 300 lines per file
- Modular architecture enforced
- Split large files automatically

### Rule 8: Absolute Imports
- No relative imports allowed
- `from .module` → `from package.module`
- Auto-conversion by filters

### Rule 9: Logging Standards
- English for logs
- Persian for UI (if applicable)
- Centralized logging system

### Rule 10: Modular Architecture
- Proper directory structure
- Separation of concerns
- Clean imports

### Rule 11: Centralized Logging
- Single logging system
- Configurable levels
- Structured logging

### Rule 12: Automated Validation
- Continuous compliance checking
- Pre-commit hooks
- Real-time feedback

## 🛠️ MCP Server Setup

The system includes a complete MCP server for integration with AI development tools:

### Server Location
`contract-enforcer-mcp/server.py`

### Required Dependencies
```bash
pip install mcp
```

### Configuration
```json
{
  "mcp.servers": {
    "zero-tolerance-contract-enforcer": {
      "command": "python",
      "args": ["contract-enforcer-mcp/server.py"],
      "env": {"PYTHONPATH": "."}
    }
  }
}
```

## 📈 Validation History

All validation results are stored in `logs/` directory:
- JSON reports with timestamps
- Detailed violation tracking
- Compliance score history
- File-by-file analysis

## 🔒 Zero Tolerance Enforcement

This system operates under **strict zero tolerance**:
- Any violation = automatic failure
- No exceptions or improvements allowed
- Complete rewrite required for violations
- 12/12 score mandatory for acceptance

## 🚀 Quick Start

1. **Clone the repository**
```bash
git clone <repository>
cd <repository>
```

2. **Install dependencies**
```bash
pip install -r enforcement/requirements.txt
pip install -r contract-enforcer-mcp/requirements.txt
```

3. **Run validation**
```bash
python project/main.py
```

4. **Check MCP integration**
```bash
python contract-enforcer-mcp/server.py
```

## 📊 Compliance Dashboard

The system provides real-time compliance monitoring through:
- MCP resources
- VSCode integration
- Automated reports
- Validation history

## 🤝 Integration

### With AI Development Tools
- MCP protocol support
- Real-time validation
- Automated fixing
- Context-aware suggestions

### With CI/CD
- Pre-commit hooks
- Build validation
- Quality gates
- Automated reporting

### With VSCode
- Task integration
- MCP server configuration
- Real-time feedback
- Automated fixes

## 📄 License

This system operates under the Zero Tolerance Python Contract License - all rules must be followed without exception.

---

**Zero Tolerance Python Contract Enforcer** - Ensuring 100% compliance, 100% of the time.

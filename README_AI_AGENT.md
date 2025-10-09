# ZT AI Agent Setup Guide

## Overview
The Zero Tolerance (ZT) AI Agent is configured with a comprehensive system prompt and tool definitions to ensure consistent, high-quality code analysis across different IDEs and AI models.

## System Prompt Location
- **File**: `data/prompts/zt_agent_system_prompt.md`
- **Purpose**: Provides complete instructions for AI models on how to use ZT tools
- **Auto-loaded**: Referenced in `contract_rules.yml` for automatic loading

## Configuration Files

### 1. Agent Configuration
**File**: `data/config/ai_agent_config.yml`
- Model settings (Gemini 2.0 Flash)
- Generation parameters (temperature: 0.1)
- Tool configuration
- Response formatting

### 2. Contract Rules Integration
**File**: `enforcement/contract_rules.yml`
- AI config with API keys
- System prompt file path
- Agent config file path
- Generation parameters

### 3. Helper Module
**File**: `enforcement/zt_agent_helper.py`
- Loads system prompt and config
- Provides utility functions
- Handles fallbacks and error cases

## Using the System Prompt in Other IDEs

### Method 1: Direct File Reference
```python
from pathlib import Path

# Load system prompt
prompt_file = Path("data/prompts/zt_agent_system_prompt.md")
with open(prompt_file, 'r', encoding='utf-8') as f:
    system_prompt = f.read()
```

### Method 2: Using Helper
```python
from enforcement.zt_agent_helper import get_system_prompt, get_ai_config_for_agent

# Get system prompt
system_prompt = get_system_prompt()

# Get AI configuration
ai_config = get_ai_config_for_agent()
```

### Method 3: Quick Access Function
```python
from enforcement.utils import get_ai_config

# Get basic AI config from contract rules
config = get_ai_config()
api_key = config["api_key"]
base_url = config["base_url"]
model = config["model"]
```

## Tool Definitions for AI Models

The system prompt includes these ZT tools:

1. **validate_code(base_path: str)**
   - Analyzes Python codebase for violations
   - Returns compliance score and detailed violations

2. **fix_violations(base_path: str)**  
   - Automatically fixes detected issues
   - Returns summary of changes made

3. **check_compliance(base_path: str)**
   - Quick compliance status check
   - Returns pass/fail and score

4. **generate_self_assessment(base_path: str)**
   - Creates detailed assessment report
   - Stores report in logs directory

## Usage Examples

### For IDE Integration
```markdown
System Prompt: {content of zt_agent_system_prompt.md}

Available Tools:
- validate_code
- fix_violations  
- check_compliance
- generate_self_assessment

Model: gemini-2.0-flash
Temperature: 0.1
Max Tokens: 2048
```

### For API Calls
```python
import requests

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "gemini-2.0-flash",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Please validate my Python project at d:/MyProject"}
    ],
    "temperature": 0.1,
    "max_tokens": 2048
}
```

## Troubleshooting

### If Tools Fail
1. **Check Path Format**: Use absolute paths with proper escaping
2. **Verify Project Structure**: Ensure valid Python project
3. **API Rate Limits**: Wait if rate limited
4. **File Permissions**: Check read/write access

### If System Prompt Not Loading
1. **File Exists**: Verify `data/prompts/zt_agent_system_prompt.md` exists
2. **Encoding**: Ensure UTF-8 encoding
3. **Fallback**: Helper provides default prompt if file missing

## Integration with MCP Servers

The system prompt is designed to work with:
- Windsurf MCP integration
- VS Code MCP extension
- Custom MCP implementations
- Direct API integrations

## Best Practices

1. **Always load system prompt** before AI interactions
2. **Use absolute paths** for tool parameters
3. **Handle errors gracefully** with fallback prompts
4. **Monitor compliance scores** and improvements
5. **Test tools** before deployment

## Files Summary

```
ZT/
├── data/prompts/zt_agent_system_prompt.md     # Main system prompt
├── data/config/ai_agent_config.yml           # Agent configuration  
├── enforcement/contract_rules.yml            # AI config integration
├── enforcement/zt_agent_helper.py            # Helper utilities
└── README_AI_AGENT.md                        # This documentation
```

This setup ensures consistent ZT behavior across all AI integrations and IDEs!

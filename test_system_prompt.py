#!/usr/bin/env python3
"""
Test System Prompt for ZT AI Agent
Use this script to test the system prompt in other IDEs
"""

import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def load_system_prompt():
    """Load the ZT system prompt"""
    prompt_file = Path("data/prompts/zt_agent_system_prompt.md")
    
    if prompt_file.exists():
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return get_fallback_prompt()

def get_fallback_prompt():
    """Get fallback prompt if file doesn't exist"""
    return """You are the Zero Tolerance Code Quality Agent, an expert AI assistant specialized in Python code analysis and quality enforcement.

Your tools:
- validate_code(base_path) - Analyze code for violations
- fix_violations(base_path) - Auto-fix detected issues  
- check_compliance(base_path) - Get compliance status
- generate_self_assessment(base_path) - Create detailed reports

Zero Tolerance Standards:
- Max 4 lines in main.py
- No print() statements
- Type hints required
- Max 300 lines per file
- Max 79 characters per line
- No hardcoded values
- Absolute imports only
- 90% compliance target

Always provide:
1. Summary of findings
2. Compliance score
3. Specific violations
4. Actionable recommendations
5. Offer to run auto-fix

Be concise, helpful, and focus on code quality improvements."""

def get_ai_config():
    """Get AI configuration"""
    try:
        from enforcement.zt_agent_helper import get_ai_config_for_agent
        return get_ai_config_for_agent()
    except:
        # Fallback config
        return {
            "api_key": "AIzaSyDz3bfQ1iLNg_BvYgx5wzI9z6964_8v1Wo",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-2.0-flash"
        }

def get_tool_definitions():
    """Get tool definitions for other IDEs"""
    return [
        {
            "name": "validate_code",
            "description": "Validate Python codebase against Zero Tolerance contract rules",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_path": {
                        "type": "string",
                        "description": "Absolute path to the project directory to validate"
                    }
                },
                "required": ["base_path"]
            }
        },
        {
            "name": "fix_violations", 
            "description": "Auto-fix contract violations in Python codebase",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_path": {
                        "type": "string",
                        "description": "Absolute path to the project directory to fix"
                    }
                },
                "required": ["base_path"]
            }
        },
        {
            "name": "check_compliance",
            "description": "Check overall compliance status of a codebase", 
            "parameters": {
                "type": "object",
                "properties": {
                    "base_path": {
                        "type": "string",
                        "description": "Absolute path to the project directory to check"
                    }
                },
                "required": ["base_path"]
            }
        },
        {
            "name": "generate_self_assessment",
            "description": "Generate self-assessment report for contract compliance",
            "parameters": {
                "type": "object", 
                "properties": {
                    "base_path": {
                        "type": "string",
                        "description": "Absolute path to the project directory to assess"
                    }
                },
                "required": ["base_path"]
            }
        }
    ]

def export_for_ide():
    """Export configuration for use in other IDEs"""
    system_prompt = load_system_prompt()
    ai_config = get_ai_config() 
    tool_definitions = get_tool_definitions()
    
    export_data = {
        "system_prompt": system_prompt,
        "ai_config": ai_config,
        "tool_definitions": tool_definitions,
        "generation_params": {
            "temperature": 0.1,
            "max_tokens": 2048,
            "top_p": 0.9
        },
        "instructions": {
            "setup": "Load system_prompt as the system message for your AI model",
            "tools": "Configure these 4 tools as available functions",
            "model": "Use the specified model and generation parameters",
            "usage": "User can now ask to validate, fix, check compliance, or assess their Python projects"
        }
    }
    
    return export_data

def main():
    """Main function for testing"""
    print("=== ZT System Prompt Test ===")
    
    # Test system prompt loading
    prompt = load_system_prompt()
    print(f"✅ System prompt loaded: {len(prompt)} characters")
    
    # Test AI config
    config = get_ai_config()
    print(f"✅ AI config loaded: {config['model']}")
    
    # Test tool definitions
    tools = get_tool_definitions()
    print(f"✅ Tool definitions: {len(tools)} tools")
    
    # Export for IDE use
    export = export_for_ide()
    
    # Save to file for easy copying
    with open("zt_agent_export.json", "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)
    
    print("✅ Configuration exported to: zt_agent_export.json")
    print("\n=== For IDE Setup ===")
    print("1. Copy system_prompt to your AI model's system message")
    print("2. Configure the 4 tools with their definitions")
    print("3. Use model: gemini-2.0-flash with temperature: 0.1")
    print("4. Test with: 'Please validate my project at [path]'")
    
    print(f"\n=== System Prompt Preview (first 200 chars) ===")
    print(prompt[:200] + "...")

if __name__ == "__main__":
    main()

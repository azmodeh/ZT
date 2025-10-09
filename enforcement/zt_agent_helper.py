#!/usr/bin/env python3
"""
ZT AI Agent Helper
Loads system prompts and configuration for the AI agent
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from enforcement.utils import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class ZTAgentHelper:
    """Helper class for ZT AI Agent configuration and prompts"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("data/config/ai_agent_config.yml")
        self.config = self.load_config()
        self.system_prompt = self.load_system_prompt()
    
    def load_config(self) -> Dict[str, Any]:
        """Load AI agent configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                logger.info(f"AI agent config loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return self.get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.get_default_config()
    
    def load_system_prompt(self) -> str:
        """Load system prompt from markdown file"""
        try:
            prompt_file = self.config.get("system_prompt", {}).get("file", "data/prompts/zt_agent_system_prompt.md")
            prompt_path = Path(prompt_file)
            
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt = f.read()
                logger.info(f"System prompt loaded from {prompt_path}")
                return prompt
            else:
                logger.warning(f"System prompt file not found: {prompt_path}")
                return self.get_default_prompt()
        except Exception as e:
            logger.error(f"Failed to load system prompt: {e}")
            return self.get_default_prompt()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file is not available"""
        return {
            "agent_settings": {
                "name": "Zero Tolerance Code Quality Agent",
                "version": "1.0.0",
                "model": {
                    "provider": "google",
                    "model_name": "gemini-2.0-flash",
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                },
                "generation": {
                    "max_tokens": 2048,
                    "temperature": 0.1,
                    "top_p": 0.9
                },
                "tools": {
                    "enabled": True,
                    "available_tools": [
                        "validate_code",
                        "fix_violations", 
                        "check_compliance",
                        "generate_self_assessment"
                    ]
                }
            }
        }
    
    def get_default_prompt(self) -> str:
        """Get default system prompt if file is not available"""
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

    def get_ai_config(self) -> Dict[str, str]:
        """Get AI model configuration for API calls"""
        model_config = self.config.get("agent_settings", {}).get("model", {})
        
        # Get from contract rules as fallback
        try:
            from enforcement.utils import get_ai_config as get_contract_ai_config
            contract_config = get_contract_ai_config()
            
            return {
                "api_key": model_config.get("api_key", contract_config.get("api_key", "")),
                "base_url": model_config.get("base_url", contract_config.get("base_url", "")),
                "model": model_config.get("model_name", contract_config.get("model", ""))
            }
        except Exception as e:
            logger.error(f"Failed to get AI config: {e}")
            return {
                "api_key": model_config.get("api_key", ""),
                "base_url": model_config.get("base_url", ""),
                "model": model_config.get("model_name", "")
            }
    
    def get_generation_params(self) -> Dict[str, Any]:
        """Get generation parameters for AI model"""
        return self.config.get("agent_settings", {}).get("generation", {
            "max_tokens": 2048,
            "temperature": 0.1,
            "top_p": 0.9
        })
    
    def get_tool_config(self) -> Dict[str, Any]:
        """Get tool configuration"""
        return self.config.get("agent_settings", {}).get("tools", {
            "enabled": True,
            "available_tools": ["validate_code", "fix_violations", "check_compliance", "generate_self_assessment"]
        })
    
    def format_response(self, content: str, include_emojis: bool = None) -> str:
        """Format response according to configuration"""
        if include_emojis is None:
            include_emojis = self.config.get("agent_settings", {}).get("response", {}).get("include_emojis", True)
        
        if not include_emojis:
            # Remove common emojis
            emojis = ["📊", "🔧", "✅", "❌", "⚠️", "🎉", "🚀", "📝", "🔍", "💡"]
            for emoji in emojis:
                content = content.replace(emoji, "")
        
        return content.strip()

def get_zt_agent_helper() -> ZTAgentHelper:
    """Get ZT Agent Helper instance"""
    return ZTAgentHelper()

def get_system_prompt() -> str:
    """Quick function to get system prompt"""
    helper = get_zt_agent_helper()
    return helper.system_prompt

def get_ai_config_for_agent() -> Dict[str, str]:
    """Quick function to get AI config"""
    helper = get_zt_agent_helper()
    return helper.get_ai_config()

if __name__ == "__main__":
    # Test the helper
    helper = get_zt_agent_helper()
    print("=== ZT Agent Helper Test ===")
    print(f"Config loaded: {bool(helper.config)}")
    print(f"System prompt length: {len(helper.system_prompt)}")
    print(f"AI config: {helper.get_ai_config()}")
    print(f"Available tools: {helper.get_tool_config().get('available_tools', [])}")

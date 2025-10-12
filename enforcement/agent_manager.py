"""
Zero Tolerance Python Contract Enforcer
Agent Manager - Multi-Agent Orchestration System

هدف: مدیریت و هماهنگی ایجنت‌های مختلف برای انجام وظایف تخصصی
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml
import time
from datetime import datetime
import json

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

# Base AIAgent class defined inline
from enforcement.auto_learning import LearningManager
from enforcement.utils import get_logger

logger = get_logger(__name__)

class AIAgent:
    """Base class for AI agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = "BaseAgent"
        self.specialties = []
    
    async def process(self, task_type: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task and return result"""
        return {
            "success": False,
            "message": "Not implemented",
            "agent_name": self.name
        }

class CodeFixAgent(AIAgent):
    """ایجنت تخصصی برای رفع خطاهای کد و refactoring"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "CodeFixAgent"
        self.specialties = [
            "syntax_errors", "print_removal", "console_log_fix", 
            "complexity_reduction", "function_refactor"
        ]
    
    def get_system_prompt(self) -> str:
        return """You are CodeFixAgent, specialized in fixing code syntax and structure issues.

Your primary tasks:
- Fix syntax errors and compilation issues
- Replace print() and console.log() statements with proper logging
- Reduce cyclomatic complexity by refactoring complex functions
- Improve code structure and readability
- Enforce Zero Tolerance contract rules

Guidelines:
- Always use structured logging instead of print statements
- Break down complex functions into smaller, focused ones
- Follow Python/JavaScript best practices
- Maintain code functionality while improving structure
- Return complete, executable code

Output format: JSON array of fixes in format:
[{"path": "file_path", "content": "complete_file_content"}]"""


class DocAgent(AIAgent):
    """ایجنت تخصصی برای مستندسازی و type hints"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "DocAgent"
        self.specialties = [
            "type_hints", "docstrings", "readme_generation", 
            "api_documentation", "code_comments"
        ]
    
    def get_system_prompt(self) -> str:
        return """You are DocAgent, specialized in code documentation and type safety.

Your primary tasks:
- Add proper type hints to all functions and variables
- Generate comprehensive docstrings for functions, classes, and modules
- Create or update README files with clear documentation
- Add helpful inline comments for complex logic
- Ensure code is self-documenting

Guidelines:
- Use proper Python type hints (typing module)
- Follow Google or NumPy docstring conventions
- Write clear, concise documentation in English
- Include examples in docstrings where helpful
- Document all public APIs thoroughly

Output format: JSON array of documentation fixes:
[{"path": "file_path", "content": "complete_file_content"}]"""


class SecurityAgent(AIAgent):
    """ایجنت تخصصی برای امنیت و حذف hardcoded values"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "SecurityAgent"
        self.specialties = [
            "hardcoded_secrets", "env_config", "security_vulnerabilities",
            "input_validation", "credential_removal"
        ]
    
    def get_system_prompt(self) -> str:
        return """You are SecurityAgent, specialized in code security and best practices.

Your primary tasks:
- Identify and remove hardcoded passwords, API keys, and secrets
- Replace hardcoded configuration with environment variables
- Add input validation and sanitization
- Fix security vulnerabilities and unsafe practices
- Enforce secure coding standards

Guidelines:
- Never leave credentials in code - use environment variables
- Add proper input validation for all external inputs
- Use secure defaults and fail-safe mechanisms
- Follow OWASP security guidelines
- Suggest secure alternatives for unsafe patterns

Output format: JSON array of security fixes:
[{"path": "file_path", "content": "complete_secure_file_content"}]"""


class AgentManager:
    """مدیر ایجنت‌ها برای هماهنگی و dispatch وظایف"""
    
    def __init__(self, config_path: str = "data/config/agents.yml"):
        """مقداردهی مدیر ایجنت‌ها
        
        Args:
            config_path: مسیر فایل پیکربندی ایجنت‌ها
        """
        self.config_path = Path(config_path)
        self.agents: Dict[str, AIAgent] = {}
        self.learning_manager = LearningManager()
        self.agent_configs = {}
        self.task_queue = asyncio.Queue()
        self.results_cache = {}
        
        # بارگذاری پیکربندی
        self._load_agent_config()
        self._initialize_agents()
        
        logger.info(f"Agent Manager initialized with {len(self.agents)} agents")
    
    def _load_agent_config(self) -> None:
        """بارگذاری پیکربندی ایجنت‌ها از فایل YAML"""
        
        # پیکربندی پیش‌فرض
        default_config = {
            "agents": [
                {
                    "name": "CodeFixAgent",
                    "prompt": "Fix syntax and refactor issues; enforce contract rules.",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 2000,
                    "temperature": 0.1,
                    "enabled": True
                },
                {
                    "name": "DocAgent", 
                    "prompt": "Add missing docstrings, type hints, and project-level README.",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 1500,
                    "temperature": 0.2,
                    "enabled": True
                },
                {
                    "name": "SecurityAgent",
                    "prompt": "Find and remove hardcoded secrets; enforce env-based config.",
                    "model": "gpt-4",
                    "max_tokens": 1800,
                    "temperature": 0.0,
                    "enabled": True
                }
            ],
            "execution_order": ["SecurityAgent", "CodeFixAgent", "DocAgent"],
            "parallel_execution": False,
            "max_retries": 2,
            "timeout_seconds": 30
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    # ادغام با پیش‌فرض
                    self.agent_configs = {**default_config, **loaded_config}
            else:
                self.agent_configs = default_config
                # ایجاد فایل پیش‌فرض
                self._save_default_config()
                
        except Exception as e:
            logger.error(f"Error loading agent config: {e}")
            self.agent_configs = default_config
    
    def _save_default_config(self) -> None:
        """ذخیره پیکربندی پیش‌فرض"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.agent_configs, f, default_flow_style=False, 
                         allow_unicode=True)
            logger.info(f"Default agent config saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving default config: {e}")
    
    def _initialize_agents(self) -> None:
        """مقداردهی ایجنت‌ها بر اساس پیکربندی"""
        
        for agent_config in self.agent_configs.get("agents", []):
            if not agent_config.get("enabled", True):
                continue
                
            agent_name = agent_config["name"]
            
            try:
                # انتخاب کلاس ایجنت مناسب
                if agent_name == "CodeFixAgent":
                    agent = CodeFixAgent(agent_config)
                elif agent_name == "DocAgent":
                    agent = DocAgent(agent_config)
                elif agent_name == "SecurityAgent":
                    agent = SecurityAgent(agent_config)
                else:
                    logger.warning(f"Unknown agent type: {agent_name}")
                    continue
                
                self.agents[agent_name] = agent
                logger.info(f"Initialized agent: {agent_name}")
                
            except Exception as e:
                logger.error(f"Error initializing agent {agent_name}: {e}")
    
    async def dispatch_task(self, task_type: str, file_path: str, 
                           content: str, context: Dict[str, Any] = None) -> \
                           Dict[str, Any]:
        """ارسال وظیفه به ایجنت مناسب
        
        Args:
            task_type: نوع وظیفه (print_removal, type_hints, etc.)
            file_path: مسیر فایل
            content: محتوای فایل
            context: اطلاعات اضافی
            
        Returns:
            نتیجه اجرا شامل agent_name، success، result
        """
        
        # انتخاب بهترین ایجنت برای این وظیفه
        best_agent = self._select_best_agent(task_type)
        
        if not best_agent:
            return {
                "success": False,
                "error": f"No suitable agent found for task: {task_type}",
                "agent_name": None
            }
        
        # اجرای وظیفه
        start_time = time.time()
        
        try:
            agent = self.agents[best_agent]
            
            # ساخت prompt
            task_prompt = self._build_task_prompt(task_type, file_path, 
                                                content, context)
            
            # اجرای ایجنت
            result = await agent.process_request(task_prompt)
            
            execution_time = time.time() - start_time
            
            # ثبت نتیجه در سیستم یادگیری
            success = self._validate_result(result)
            score = self._calculate_score(result, task_type)
            
            self.learning_manager.record_result(
                task_name=task_type,
                success=success,
                score=score,
                agent_name=best_agent,
                execution_time=execution_time,
                violations=[task_type] if context and 
                          context.get("violations") else []
            )
            
            return {
                "success": success,
                "result": result,
                "agent_name": best_agent,
                "execution_time": execution_time,
                "score": score
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Task execution failed: {e}")
            
            # ثبت شکست
            self.learning_manager.record_result(
                task_name=task_type,
                success=False,
                score=0,
                agent_name=best_agent,
                execution_time=execution_time
            )
            
            return {
                "success": False,
                "error": str(e),
                "agent_name": best_agent,
                "execution_time": execution_time
            }
    
    def _select_best_agent(self, task_type: str) -> Optional[str]:
        """انتخاب بهترین ایجنت برای نوع وظیفه
        
        Args:
            task_type: نوع وظیفه
            
        Returns:
            نام بهترین ایجنت
        """
        
        # اول از سیستم یادگیری پرس‌وجو کن
        learned_best = self.learning_manager.get_best_agent_for_task(task_type)
        if learned_best and learned_best in self.agents:
            logger.debug(f"Learning system suggests {learned_best} for {task_type}")
            return learned_best
        
        # نقشه‌برداری بر اساس نوع وظیفه
        task_mapping = {
            "print_removal": "CodeFixAgent",
            "console_log_fix": "CodeFixAgent", 
            "syntax_error": "CodeFixAgent",
            "complexity_reduction": "CodeFixAgent",
            "refactoring": "CodeFixAgent",
            
            "type_hints": "DocAgent",
            "docstrings": "DocAgent",
            "documentation": "DocAgent",
            "comments": "DocAgent",
            "readme": "DocAgent",
            
            "hardcoded_secrets": "SecurityAgent",
            "env_config": "SecurityAgent",
            "security_fix": "SecurityAgent",
            "input_validation": "SecurityAgent",
            "credential_removal": "SecurityAgent"
        }
        
        # جستجوی مستقیم
        if task_type in task_mapping:
            agent_name = task_mapping[task_type]
            if agent_name in self.agents:
                return agent_name
        
        # جستجوی فازی
        for pattern, agent_name in task_mapping.items():
            if pattern in task_type.lower() or task_type.lower() in pattern:
                if agent_name in self.agents:
                    logger.debug(f"Fuzzy match: {task_type} -> {agent_name}")
                    return agent_name
        
        # ایجنت پیش‌فرض
        if self.agents:
            default_agent = list(self.agents.keys())[0]
            logger.debug(f"Using default agent {default_agent} for {task_type}")
            return default_agent
        
        return None
    
    def _build_task_prompt(self, task_type: str, file_path: str, 
                          content: str, context: Dict[str, Any] = None) -> str:
        """ساخت prompt برای وظیفه
        
        Args:
            task_type: نوع وظیفه
            file_path: مسیر فایل  
            content: محتوای فایل
            context: اطلاعات اضافی
            
        Returns:
            prompt آماده برای ایجنت
        """
        
        prompt = f"Task: {task_type}\n"
        prompt += f"File: {file_path}\n\n"
        
        if context:
            if "violations" in context:
                prompt += f"Violations found: {', '.join(context['violations'])}\n"
            if "requirements" in context:
                prompt += f"Requirements: {context['requirements']}\n"
            prompt += "\n"
        
        prompt += "Current file content:\n"
        prompt += "```\n"
        prompt += content
        prompt += "\n```\n\n"
        
        prompt += "Please fix the issues and return the complete corrected file content in JSON format:\n"
        prompt += '[{"path": "' + file_path + '", "content": "corrected_content"}]'
        
        return prompt
    
    def _validate_result(self, result: Any) -> bool:
        """اعتبارسنجی نتیجه ایجنت
        
        Args:
            result: نتیجه برگشتی از ایجنت
            
        Returns:
            True اگر نتیجه معتبر باشد
        """
        
        if not result:
            return False
            
        try:
            # بررسی فرمت JSON
            if isinstance(result, str):
                import json
                parsed = json.loads(result)
                if isinstance(parsed, list) and len(parsed) > 0:
                    first_item = parsed[0]
                    return "path" in first_item and "content" in first_item
            
            elif isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                return isinstance(first_item, dict) and \
                       "path" in first_item and "content" in first_item
                       
            return False
            
        except Exception as e:
            logger.debug(f"Result validation error: {e}")
            return False
    
    def _calculate_score(self, result: Any, task_type: str) -> int:
        """محاسبه امتیاز نتیجه
        
        Args:
            result: نتیجه ایجنت
            task_type: نوع وظیفه
            
        Returns:
            امتیاز از 0 تا 100
        """
        
        base_score = 60  # امتیاز پایه برای نتیجه معتبر
        
        if not self._validate_result(result):
            return 0
        
        try:
            # تحلیل کیفیت محتوا
            if isinstance(result, str):
                import json
                content_list = json.loads(result)
            else:
                content_list = result
            
            if not content_list:
                return base_score
                
            content = content_list[0].get("content", "")
            
            # معیارهای کیفی
            quality_bonus = 0
            
            # طول محتوا (نباید خیلی کوتاه یا طولانی باشد)
            if 50 <= len(content) <= 10000:
                quality_bonus += 10
            
            # برای task های مختلف معیارهای متفاوت
            if task_type in ["print_removal", "console_log_fix"]:
                if "print(" not in content and "console.log(" not in content:
                    quality_bonus += 20
                if "logger" in content or "logging" in content:
                    quality_bonus += 10
                    
            elif task_type in ["type_hints", "docstrings"]:
                if "def " in content and "->" in content:
                    quality_bonus += 15
                if '"""' in content or "'''" in content:
                    quality_bonus += 15
                    
            elif task_type in ["hardcoded_secrets", "env_config"]:
                if "os.environ" in content or "getenv" in content:
                    quality_bonus += 20
                # کاهش امتیاز برای مقادیر مشکوک
                suspicious_patterns = ["password", "api_key", "secret", "token"]
                for pattern in suspicious_patterns:
                    if f'"{pattern}"' in content.lower():
                        quality_bonus -= 10
            
            return min(100, base_score + quality_bonus)
            
        except Exception as e:
            logger.debug(f"Score calculation error: {e}")
            return base_score
    
    async def process_file_chain(self, file_path: str, content: str,
                                violations: List[str] = None) -> Dict[str, Any]:
        """پردازش فایل با زنجیره ایجنت‌ها
        
        Args:
            file_path: مسیر فایل
            content: محتوای اولیه فایل
            violations: لیست تخلفات
            
        Returns:
            نتیجه نهایی پس از پردازش همه ایجنت‌ها
        """
        
        execution_order = self.agent_configs.get("execution_order", 
                                               list(self.agents.keys()))
        
        current_content = content
        results = []
        
        for agent_name in execution_order:
            if agent_name not in self.agents:
                logger.warning(f"Agent {agent_name} not found, skipping")
                continue
            
            # تعیین نوع وظیفه بر اساس ایجنت
            task_type = self._get_task_type_for_agent(agent_name, violations)
            
            if task_type:
                logger.info(f"Processing {file_path} with {agent_name} for {task_type}")
                
                result = await self.dispatch_task(
                    task_type=task_type,
                    file_path=file_path,
                    content=current_content,
                    context={"violations": violations}
                )
                
                results.append(result)
                
                # اگر موفق بود، محتوا را به‌روزرسانی کن
                if result["success"] and result.get("result"):
                    try:
                        if isinstance(result["result"], str):
                            import json
                            content_list = json.loads(result["result"])
                        else:
                            content_list = result["result"]
                            
                        if content_list and "content" in content_list[0]:
                            current_content = content_list[0]["content"]
                    except Exception as e:
                        logger.error(f"Error updating content: {e}")
        
        return {
            "final_content": current_content,
            "chain_results": results,
            "success": all(r.get("success", False) for r in results),
            "total_agents": len(results)
        }
    
    def _get_task_type_for_agent(self, agent_name: str, 
                                violations: List[str] = None) -> Optional[str]:
        """تعیین نوع وظیفه برای ایجنت بر اساس تخلفات
        
        Args:
            agent_name: نام ایجنت
            violations: لیست تخلفات
            
        Returns:
            نوع وظیفه مناسب
        """
        
        if not violations:
            # وظایف پیش‌فرض برای هر ایجنت
            default_tasks = {
                "CodeFixAgent": "syntax_review",
                "DocAgent": "documentation_review", 
                "SecurityAgent": "security_review"
            }
            return default_tasks.get(agent_name)
        
        # انتخاب وظیفه بر اساس تخلفات
        agent_task_mapping = {
            "CodeFixAgent": ["print", "console", "syntax", "complexity"],
            "DocAgent": ["type", "hint", "doc", "comment"],
            "SecurityAgent": ["hardcode", "secret", "password", "key"]
        }
        
        agent_patterns = agent_task_mapping.get(agent_name, [])
        
        for violation in violations:
            for pattern in agent_patterns:
                if pattern.lower() in violation.lower():
                    return violation
        
        return None
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """دریافت آمار ایجنت‌ها
        
        Returns:
            آمار کلی ایجنت‌ها
        """
        
        stats = {
            "total_agents": len(self.agents),
            "active_agents": list(self.agents.keys()),
            "learning_stats": self.learning_manager.get_learning_stats(),
            "agent_performance": {}
        }
        
        # آمار عملکرد از سیستم یادگیری
        learning_data = self.learning_manager.learning_data
        
        for agent_name in self.agents.keys():
            if agent_name in learning_data["agent_performance"]:
                agent_perf = learning_data["agent_performance"][agent_name]
                stats["agent_performance"][agent_name] = {
                    "total_tasks": agent_perf["total_tasks"],
                    "success_rate": (agent_perf["successful_tasks"] / 
                                   agent_perf["total_tasks"]) if agent_perf["total_tasks"] > 0 else 0,
                    "avg_score": agent_perf["average_score"],
                    "avg_time": agent_perf["average_execution_time"],
                    "specialties": dict(agent_perf["specialties"].most_common(5))
                }
        
        return stats


# تابع کمکی برای استفاده آسان
def create_agent_manager(config_path: str = None) -> AgentManager:
    """ایجاد instance جدید از AgentManager
    
    Args:
        config_path: مسیر فایل پیکربندی
        
    Returns:
        AgentManager instance
    """
    if not config_path:
        config_path = "data/config/agents.yml"
    
    return AgentManager(config_path)
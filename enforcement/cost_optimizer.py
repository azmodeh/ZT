"""
Zero Tolerance Cost Optimizer
Manages AI API costs with budget limits, model routing, and token optimization
"""

from __future__ import annotations

import os
import yaml
import logging
import operator
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Operators for condition evaluation
OPS = {
    "==": operator.eq,
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
    "!=": operator.ne,
}


def _eval_condition(expr: str, ctx: Dict[str, Any]) -> bool:
    """
    Evaluate routing condition safely
    
    Supports:
    - risk <= 20
    - task == 'type_hints'
    - sensitive_data == true
    - risk > 10 and risk <= 20
    - task in ['security', 'type_hints']
    
    Args:
        expr: Condition expression
        ctx: Context dictionary with variables
    
    Returns:
        True if condition matches, False otherwise
    """
    if not expr or not expr.strip():
        return False
    
    try:
        # Normalize operators
        expr = expr.replace(" and ", " && ").replace(" or ", " || ")
        
        # Replace context variables
        for key, val in ctx.items():
            if isinstance(val, bool):
                rep = "True" if val else "False"
            elif isinstance(val, str):
                rep = f"'{val}'"
            else:
                rep = str(val)
            expr = expr.replace(key, rep)
        
        # Restore Python operators
        expr = expr.replace("&&", " and ").replace("||", " or ")
        expr = expr.replace("true", "True").replace("false", "False")
        
        # Safe evaluation
        result = eval(expr, {"__builtins__": {}}, {})
        return bool(result)
        
    except Exception as e:
        logger.debug(f"Failed to evaluate condition '{expr}': {e}")
        return False


@dataclass
class BudgetStatus:
    """Budget tracking status"""
    daily_spent_cents: int = 0
    run_spent_cents: int = 0
    daily_limit_cents: int = 1500
    run_limit_cents: int = 400
    last_reset: datetime = None
    
    def can_proceed(self) -> bool:
        """Check if we can make another API call"""
        return (self.daily_spent_cents < self.daily_limit_cents and 
                self.run_spent_cents < self.run_limit_cents)
    
    def add_cost(self, cents: int):
        """Add cost to both daily and run budgets"""
        self.daily_spent_cents += cents
        self.run_spent_cents += cents
    
    def reset_daily_if_needed(self):
        """Reset daily budget if new day"""
        if self.last_reset is None:
            self.last_reset = datetime.now()
            return
        
        if datetime.now() - self.last_reset > timedelta(days=1):
            self.daily_spent_cents = 0
            self.last_reset = datetime.now()
            logger.info("Daily budget reset")
    
    def reset_run(self):
        """Reset run budget for new queue run"""
        self.run_spent_cents = 0


class CostOptimizer:
    """
    Cost optimization manager for AI API calls
    
    Features:
    - Budget limits (daily and per-run)
    - Model routing based on task type and risk
    - Token limits and chunking
    - Batch processing optimization
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize cost optimizer with config"""
        self.config_path = config_path or os.getenv('ZT_CFG')
        self.config: Dict[str, Any] = {}
        self.budget_status = BudgetStatus()
        
        if self.config_path:
            self.load_config()
        else:
            logger.warning("No cost optimizer config specified, using defaults")
            self._load_defaults()
    
    def load_config(self):
        """Load cost optimizer configuration from YAML"""
        try:
            config_file = Path(self.config_path)
            if not config_file.is_absolute():
                # Try relative to ZT_HOME
                zt_home = os.getenv('ZT_HOME', '.')
                config_file = Path(zt_home) / config_file
            
            if not config_file.exists():
                logger.error(f"Config file not found: {config_file}")
                self._load_defaults()
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # Initialize budget from config
            budget_cfg = self.config.get('budget', {})
            self.budget_status.daily_limit_cents = budget_cfg.get('daily_cents', 1500)
            self.budget_status.run_limit_cents = budget_cfg.get('per_run_cents', 400)
            
            logger.info(f"Cost optimizer loaded from {config_file}")
            logger.info(f"Daily budget: ${self.budget_status.daily_limit_cents/100:.2f}")
            logger.info(f"Per-run budget: ${self.budget_status.run_limit_cents/100:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to load cost optimizer config: {e}")
            self._load_defaults()
    
    def _load_defaults(self):
        """Load default configuration"""
        self.config = {
            'budget': {
                'daily_cents': 1500,
                'per_run_cents': 400,
                'stop_if_exceeded': True
            },
            'models': {
                'fast': 'gpt-4o-mini',
                'medium': 'mistralai/mixtral-8x7b',
                'deep': 'anthropic/claude-3-opus'
            },
            'limits': {
                'max_tokens_request': 2000,
                'max_tokens_response': 1200,
                'chunk_lines': 160
            },
            'batching': {
                'batch_size': 100,
                'max_workers': 4
            },
            'policy': {
                'min_score': 90,
                'max_passes': 3,
                'proof_of_change': True,
                'risk_block_threshold': 70
            }
        }
    
    def select_model(self, task: str, risk_score: int = 50, sensitive_data: bool = False) -> str:
        """
        Select appropriate model based on task type, risk score, and data sensitivity
        
        Args:
            task: Task type (e.g., 'remove_prints', 'security', 'type_hints')
            risk_score: Risk score (0-100)
            sensitive_data: Whether data is sensitive (forces local model)
        
        Returns:
            Model identifier string
        
        Examples:
            >>> opt.select_model('pep8', risk_score=5)
            'meta-llama/llama-3.3-70b-instruct:free'
            
            >>> opt.select_model('security', risk_score=60)
            'anthropic/claude-3-opus'
            
            >>> opt.select_model('any', risk_score=10, sensitive_data=True)
            'ollama/llama3.2'
        """
        models = self.config.get('models', {})
        routing = self.config.get('routing', {})
        
        # Build context for condition evaluation
        ctx = {
            'task': task,
            'risk': risk_score,
            'sensitive_data': sensitive_data
        }
        
        # RULE 1: Sensitive data ALWAYS goes to local model regardless of risk
        if sensitive_data:
            local_model = models.get('local')
            if local_model:
                logger.info(f"Using local model for sensitive data: {local_model}")
                return local_model
            # Fallback if no local model defined
            logger.warning("No local model defined for sensitive data, using ollama/llama3.2")
            return "ollama/llama3.2"
        
        # RULE 2: Risk-based routing
        # risk≤10→free, 10<risk≤20→fast, 20<risk≤50→medium, 50<risk≤80→deep, risk>80→local
        if risk_score <= 10:
            model_tier = 'free'
        elif 10 < risk_score <= 20:
            model_tier = 'fast'
        elif 20 < risk_score <= 50:
            model_tier = 'medium'
        elif 50 < risk_score <= 80:
            model_tier = 'deep'
        else:  # risk > 80
            model_tier = 'local'
        
        # Try to get the model for the selected tier
        model = models.get(model_tier)
        if model:
            logger.info(f"Selected model: {model} (tier: {model_tier}, risk: {risk_score})")
            return model
        
        # Try alternative models for the tier
        for alt_suffix in ['_alt', '_groq', '_nvidia']:
            alt_model = models.get(f"{model_tier}{alt_suffix}")
            if alt_model:
                logger.info(f"Selected alt model: {alt_model} (tier: {model_tier}{alt_suffix})")
                return alt_model
        
        # RULE 3: Apply custom routing rules if no match yet
        for rule in routing.get('rules', []):
            when_condition = rule.get('when', '').strip()
            if not when_condition:
                continue
            
            if _eval_condition(when_condition, ctx):
                rule_model_tier = rule.get('use', 'fast')
                
                # Try primary model
                rule_model = models.get(rule_model_tier)
                if rule_model:
                    logger.debug(f"Selected model from custom rule: {rule_model} (tier: {rule_model_tier}, rule: {when_condition})")
                    return rule_model
                
                # Try alternative models
                for alt_suffix in ['_alt', '_groq', '_nvidia']:
                    alt_model = models.get(f"{rule_model_tier}{alt_suffix}")
                    if alt_model:
                        logger.debug(f"Selected alt model from custom rule: {alt_model} (tier: {rule_model_tier}{alt_suffix})")
                        return alt_model
        
        # Default fallback priority: fast → free → local
        for fallback in ['fast', 'free', 'local']:
            model = models.get(fallback)
            if model:
                logger.warning(f"No routing rule matched, using fallback: {model}")
                return model
        
        # Ultimate fallback
        logger.error("No model found in config, using hardcoded fallback")
        return 'gpt-4o-mini'
    
    def get_token_limits(self) -> Dict[str, int]:
        """Get token limits for requests"""
        limits = self.config.get('limits', {})
        return {
            'max_tokens_request': limits.get('max_tokens_request', 2000),
            'max_tokens_response': limits.get('max_tokens_response', 1200),
            'chunk_lines': limits.get('chunk_lines', 160)
        }
    
    def get_batch_config(self) -> Dict[str, Any]:
        """Get batching configuration"""
        batching = self.config.get('batching', {})
        return {
            'batch_size': batching.get('batch_size', 100),
            'max_workers': batching.get('max_workers', 4),
            'skip_globs': batching.get('skip_globs', [])
        }
    
    def get_policy_config(self) -> Dict[str, Any]:
        """Get policy configuration"""
        policy = self.config.get('policy', {})
        return {
            'min_score': policy.get('min_score', 90),
            'max_passes': policy.get('max_passes', 3),
            'proof_of_change': policy.get('proof_of_change', True),
            'risk_block_threshold': policy.get('risk_block_threshold', 70)
        }
    
    def check_budget(self) -> bool:
        """
        Check if we have budget remaining
        
        Returns:
            True if we can proceed, False if budget exceeded
        """
        self.budget_status.reset_daily_if_needed()
        
        if not self.budget_status.can_proceed():
            stop_if_exceeded = self.config.get('budget', {}).get('stop_if_exceeded', True)
            
            if stop_if_exceeded:
                logger.error(f"Budget exceeded! Daily: ${self.budget_status.daily_spent_cents/100:.2f}, "
                           f"Run: ${self.budget_status.run_spent_cents/100:.2f}")
                return False
            else:
                logger.warning("Budget exceeded but continuing (stop_if_exceeded=false)")
        
        return True
    
    def record_api_call(self, model: str, input_tokens: int, output_tokens: int):
        """
        Record API call cost
        
        Approximate pricing (cents per 1M tokens):
        FREE MODELS:
        - meta-llama/llama-3.3-70b-instruct:free: $0/$0
        - google/gemini-2.0-flash-exp:free: $0/$0
        - ollama/*: $0/$0 (local)
        
        CHEAP MODELS:
        - gpt-4o-mini: $15/$60
        - groq/llama-3.3-70b-versatile: $9/$9 (very fast)
        
        MEDIUM MODELS:
        - mistralai/mixtral-8x7b: $27/$27
        - mistralai/mistral-large: $200/$600
        - nvidia/llama-3.1-nemotron-70b: $35/$40
        
        EXPENSIVE MODELS:
        - anthropic/claude-3-opus: $1500/$7500
        - google/gemini-exp-1206: $0/$0 (experimental, free for now)
        """
        # Comprehensive pricing model
        pricing = {
            # Free models
            'meta-llama/llama-3.3-70b-instruct:free': (0, 0),
            'google/gemini-2.0-flash-exp:free': (0, 0),
            'ollama/llama3.2': (0, 0),
            
            # Fast models
            'gpt-4o-mini': (15, 60),
            'groq/llama-3.3-70b-versatile': (9, 9),
            
            # Medium models
            'mistralai/mixtral-8x7b': (27, 27),
            'mistralai/mistral-large': (200, 600),
            'nvidia/llama-3.1-nemotron-70b': (35, 40),
            
            # Deep models
            'anthropic/claude-3-opus': (1500, 7500),
            'google/gemini-exp-1206': (0, 0),  # Experimental, currently free
        }
        
        # Get pricing or default to fast pricing
        input_price, output_price = pricing.get(model, (15, 60))
        
        # Calculate cost in cents
        cost_cents = (
            (input_tokens / 1_000_000) * input_price +
            (output_tokens / 1_000_000) * output_price
        )
        
        self.budget_status.add_cost(int(cost_cents))
        
        if cost_cents > 0:
            logger.debug(f"API call recorded: {model}, {input_tokens}+{output_tokens} tokens, ${cost_cents/100:.4f}")
        else:
            logger.debug(f"API call recorded (FREE): {model}, {input_tokens}+{output_tokens} tokens")
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        return {
            'daily_spent': f"${self.budget_status.daily_spent_cents/100:.2f}",
            'daily_limit': f"${self.budget_status.daily_limit_cents/100:.2f}",
            'daily_remaining': f"${(self.budget_status.daily_limit_cents - self.budget_status.daily_spent_cents)/100:.2f}",
            'run_spent': f"${self.budget_status.run_spent_cents/100:.2f}",
            'run_limit': f"${self.budget_status.run_limit_cents/100:.2f}",
            'run_remaining': f"${(self.budget_status.run_limit_cents - self.budget_status.run_spent_cents)/100:.2f}",
            'can_proceed': self.budget_status.can_proceed()
        }
    
    def reset_run_budget(self):
        """Reset budget for new queue run"""
        self.budget_status.reset_run()
        logger.info("Run budget reset")


# Global instance
_optimizer: Optional[CostOptimizer] = None

def get_optimizer() -> CostOptimizer:
    """Get global cost optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = CostOptimizer()
    return _optimizer

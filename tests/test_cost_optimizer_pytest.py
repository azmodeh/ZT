"""
Pytest tests for Cost Optimizer
Tests model selection routing with sensitive_data parameter
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enforcement.cost_optimizer import CostOptimizer, _eval_condition

CFG = "data/config/cost_optimizer.yml"


class TestConditionEvaluation:
    """Test condition evaluation function"""
    
    def test_simple_equality(self):
        """Test simple equality conditions"""
        assert _eval_condition("risk <= 10", {"risk": 5})
        assert not _eval_condition("risk <= 10", {"risk": 15})
        
    def test_boolean_sensitive_data(self):
        """Test boolean sensitive_data condition"""
        assert _eval_condition("sensitive_data == true", {"sensitive_data": True})
        assert not _eval_condition("sensitive_data == true", {"sensitive_data": False})
        
    def test_range_conditions(self):
        """Test range conditions with and"""
        assert _eval_condition("risk > 10 and risk <= 20", {"risk": 15})
        assert not _eval_condition("risk > 10 and risk <= 20", {"risk": 25})
        
    def test_task_in_list(self):
        """Test task in list condition"""
        ctx = {"task": "type_hints"}
        assert _eval_condition("task in ['type_hints', 'imports']", ctx)


class TestModelSelection:
    """Test model selection with different scenarios"""
    
    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance"""
        return CostOptimizer(CFG)
    
    def test_sensitive_data_always_local_low_risk(self, optimizer):
        """Sensitive data with LOW risk must go LOCAL"""
        model = optimizer.select_model(task="any", risk_score=5, sensitive_data=True)
        assert "ollama" in model or "local" in model.lower(), \
            f"Expected local model for sensitive data, got {model}"
    
    def test_sensitive_data_always_local_high_risk(self, optimizer):
        """Sensitive data with HIGH risk must go LOCAL"""
        model = optimizer.select_model(task="security", risk_score=70, sensitive_data=True)
        assert "ollama" in model or "local" in model.lower(), \
            f"Expected local model for sensitive data, got {model}"
    
    def test_free_model_low_risk(self, optimizer):
        """Risk ≤10 without sensitive data should use FREE model"""
        model = optimizer.select_model(task="pep8", risk_score=8, sensitive_data=False)
        assert "free" in model or "llama" in model.lower(), \
            f"Expected free model for risk≤10, got {model}"
    
    def test_fast_model_low_mid_risk(self, optimizer):
        """Risk 10-20 should use FAST model"""
        model = optimizer.select_model(task="remove_prints", risk_score=15, sensitive_data=False)
        assert any(x in model for x in ("gpt-4o-mini", "gemini", "groq")), \
            f"Expected fast model for risk 10-20, got {model}"
    
    def test_medium_model_mid_risk(self, optimizer):
        """Risk 20-50 should use MEDIUM model"""
        model = optimizer.select_model(task="type_hints", risk_score=35, sensitive_data=False)
        assert any(x in model for x in ("mixtral", "mistral", "nemotron", "nvidia")), \
            f"Expected medium model for risk 20-50, got {model}"
    
    def test_deep_model_high_risk(self, optimizer):
        """Risk 50-80 should use DEEP model"""
        model = optimizer.select_model(task="security", risk_score=65, sensitive_data=False)
        assert any(x in model for x in ("claude", "gemini", "opus")), \
            f"Expected deep model for risk 50-80, got {model}"
    
    def test_local_model_extreme_risk(self, optimizer):
        """Risk >80 should use LOCAL model"""
        model = optimizer.select_model(task="massive_refactor", risk_score=95, sensitive_data=False)
        assert "ollama" in model or "local" in model.lower(), \
            f"Expected local model for risk>80, got {model}"
    
    def test_priority_order(self, optimizer):
        """Sensitive data takes priority over risk level"""
        # Even with low risk, sensitive data should be local
        model_low = optimizer.select_model("simple", risk_score=5, sensitive_data=True)
        model_high = optimizer.select_model("complex", risk_score=95, sensitive_data=True)
        
        assert model_low == model_high, \
            "Both sensitive data calls should return same local model"
        assert "ollama" in model_low, \
            f"Both should be local, got {model_low}"


class TestTokenLimitsAndBudget:
    """Test token limits and budget configuration"""
    
    @pytest.fixture
    def optimizer(self):
        return CostOptimizer(CFG)
    
    def test_token_limits(self, optimizer):
        """Test token limits are loaded correctly"""
        limits = optimizer.get_token_limits()
        assert limits['max_tokens_request'] == 2000
        assert limits['max_tokens_response'] == 1200
        assert limits['chunk_lines'] == 160
    
    def test_budget_config(self, optimizer):
        """Test budget configuration"""
        budget_status = optimizer.get_budget_status()
        assert budget_status['can_proceed'] == True
        assert '$' in budget_status['daily_limit']
    
    def test_policy_config(self, optimizer):
        """Test policy configuration"""
        policy = optimizer.get_policy_config()
        assert policy['min_score'] == 90
        assert policy['max_passes'] == 3
        assert policy['proof_of_change'] == True
        assert policy['risk_block_threshold'] == 70


class TestCostRecording:
    """Test cost recording and budget tracking"""
    
    @pytest.fixture
    def optimizer(self):
        opt = CostOptimizer(CFG)
        opt.budget_status.daily_spent_cents = 0
        opt.budget_status.run_spent_cents = 0
        return opt
    
    def test_free_model_no_cost(self, optimizer):
        """Free models should record zero cost"""
        optimizer.record_api_call('meta-llama/llama-3.3-70b-instruct:free', 1000, 500)
        status = optimizer.get_budget_status()
        assert status['run_spent'] == '$0.00'
    
    def test_paid_model_records_cost(self, optimizer):
        """Paid models should record cost"""
        # Use larger token counts to ensure measurable cost
        optimizer.record_api_call('gpt-4o-mini', 1_000_000, 500_000)
        status = optimizer.get_budget_status()
        # Cost should be > $0
        assert status['run_spent'] != '$0.00', f"Expected cost > $0, got {status['run_spent']}"


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def optimizer(self):
        return CostOptimizer(CFG)
    
    def test_invalid_risk_score_handled(self, optimizer):
        """Invalid risk scores should be handled gracefully"""
        # Should not crash
        model = optimizer.select_model("test", risk_score=-10, sensitive_data=False)
        assert model is not None
        
    def test_missing_task_handled(self, optimizer):
        """Missing task should be handled"""
        model = optimizer.select_model("", risk_score=50, sensitive_data=False)
        assert model is not None
    
    def test_fallback_works(self, optimizer):
        """Fallback mechanism should work"""
        # Even with weird inputs, should return a valid model
        model = optimizer.select_model("unknown_task", risk_score=999, sensitive_data=False)
        assert model is not None
        assert len(model) > 0


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_cost_optimizer_pytest.py -v
    pytest.main([__file__, "-v", "--tb=short"])

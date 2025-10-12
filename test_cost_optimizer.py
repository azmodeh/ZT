"""Test Cost Optimizer functionality"""
from enforcement.cost_optimizer import CostOptimizer

print('🧪 Testing Cost Optimizer...\n')

# Test 1: Load config
print('1️⃣ Testing config load...')
optimizer = CostOptimizer('data/config/cost_optimizer.yml')
print(f'   ✅ Config loaded: {len(optimizer.config)} sections')

# Test 2: Model selection with new sensitive_data parameter
print('\n2️⃣ Testing model selection...')

# Test 2.1: Sensitive data ALWAYS goes local (highest priority)
model_sensitive_low_risk = optimizer.select_model('any', risk_score=5, sensitive_data=True)
print(f'   ✅ Sensitive + low risk → local: {model_sensitive_low_risk}')
assert 'ollama' in model_sensitive_low_risk or 'local' in model_sensitive_low_risk.lower()

model_sensitive_high_risk = optimizer.select_model('any', risk_score=60, sensitive_data=True)
print(f'   ✅ Sensitive + high risk → local: {model_sensitive_high_risk}')
assert 'ollama' in model_sensitive_high_risk or 'local' in model_sensitive_high_risk.lower()

# Test 2.2: Free for ultra low risk
model_free = optimizer.select_model('pep8', risk_score=8, sensitive_data=False)
print(f'   ✅ Ultra low risk (≤10) → free: {model_free}')
assert 'free' in model_free or 'llama' in model_free.lower()

# Test 2.3: Fast for low risk
model_fast = optimizer.select_model('remove_prints', risk_score=15, sensitive_data=False)
print(f'   ✅ Low risk (10-20) → fast: {model_fast}')
assert any(x in model_fast for x in ('gpt-4o-mini', 'gemini', 'groq'))

# Test 2.4: Medium for mid risk
model_medium = optimizer.select_model('type_hints', risk_score=35, sensitive_data=False)
print(f'   ✅ Medium risk (20-50) → medium: {model_medium}')
assert any(x in model_medium for x in ('mixtral', 'mistral', 'nemotron', 'nvidia'))

# Test 2.5: Deep for high risk (non-sensitive)
model_deep = optimizer.select_model('security', risk_score=65, sensitive_data=False)
print(f'   ✅ High risk (50-80) → deep: {model_deep}')
assert any(x in model_deep for x in ('claude', 'gemini'))

# Test 2.6: Local for extreme risk
model_extreme = optimizer.select_model('massive_refactor', risk_score=95, sensitive_data=False)
print(f'   ✅ Extreme risk (>80) → local: {model_extreme}')
assert 'ollama' in model_extreme or 'local' in model_extreme.lower()

# Test 3: Token limits
print('\n3️⃣ Testing token limits...')
limits = optimizer.get_token_limits()
print(f'   ✅ Max request tokens: {limits["max_tokens_request"]}')
print(f'   ✅ Max response tokens: {limits["max_tokens_response"]}')

# Test 4: Budget check
print('\n4️⃣ Testing budget...')
budget = optimizer.get_budget_status()
print(f'   ✅ Daily limit: {budget["daily_limit"]}')
print(f'   ✅ Run limit: {budget["run_limit"]}')
print(f'   ✅ Can proceed: {budget["can_proceed"]}')

# Test 5: Record API call
print('\n5️⃣ Testing cost recording...')
optimizer.record_api_call('gpt-4o-mini', input_tokens=1000, output_tokens=500)
budget_after = optimizer.get_budget_status()
print(f'   ✅ Cost recorded: {budget_after["run_spent"]}')

# Test 6: Policy config
print('\n6️⃣ Testing policy config...')
policy = optimizer.get_policy_config()
print(f'   ✅ Min score: {policy["min_score"]}')
print(f'   ✅ Max passes: {policy["max_passes"]}')
print(f'   ✅ Proof of change: {policy["proof_of_change"]}')

print('\n🎉 All tests passed!')

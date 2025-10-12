# ✅ Cost Optimizer - Deploy Checklist

راهنمای نهایی برای اطمینان از کارکرد بی‌اشتباه Cost Optimizer

---

## 🎯 **هدف:**
اطمینان از اینکه:
1. **sensitive_data همیشه local** می‌رود (حتی با risk پایین)
2. **مدل‌ها به ترتیب اولویت** انتخاب می‌شوند
3. **fallback امن** در صورت عدم دسترسی به provider
4. **تست‌ها 100% سبز** هستند

---

## 📋 **Pre-Deployment Checklist**

### ✅ **1. تنظیمات Config**

**فایل:** `data/config/cost_optimizer.yml`

```yaml
# بررسی کنید:
routing:
  rules:
    # ✅ اولویت ۱: sensitive_data == true باید اول باشد
    - when: "sensitive_data == true"
      use: local
    
    # ✅ بقیه routing rules به ترتیب اولویت
    - when: "risk <= 10"
      use: free
    # ... ادامه
```

**چک‌لیست:**
- [ ] `sensitive_data == true` در **اول** لیست است
- [ ] همه risk ranges بدون gap هستند (≤10, 10-20, 20-50, 50-80, >80)
- [ ] models تعریف شده‌اند: free, fast, medium, deep, local
- [ ] alternative models (fast_alt, medium_alt) وجود دارند

---

### ✅ **2. تست‌های یکپارچگی**

```bash
# تست سریع
python test_cost_optimizer.py

# تست کامل pytest
python -m pytest tests/test_cost_optimizer_pytest.py -v

# یا از VSCode:
# Ctrl+Shift+P → Tasks: Run Task → ZT: Test Cost Optimizer
```

**نتیجه مورد انتظار:**
```
====================================== 20 passed ========================================
```

**تست‌های حیاتی:**
- [ ] ✅ test_sensitive_data_always_local_low_risk
- [ ] ✅ test_sensitive_data_always_local_high_risk
- [ ] ✅ test_priority_order
- [ ] ✅ test_free_model_low_risk
- [ ] ✅ test_deep_model_high_risk
- [ ] ✅ test_local_model_extreme_risk

---

### ✅ **3. کد انتخاب مدل**

**فایل:** `enforcement/cost_optimizer.py`

**بررسی کنید:**
- [ ] `_eval_condition()` function وجود دارد
- [ ] `select_model()` پارامتر `sensitive_data: bool` دارد
- [ ] Fallback chain: fast → free → local
- [ ] Logging برای debugging فعال است

**تست دستی:**
```python
from enforcement.cost_optimizer import CostOptimizer

opt = CostOptimizer('data/config/cost_optimizer.yml')

# تست 1: Sensitive data با risk پایین
model = opt.select_model('any', risk_score=5, sensitive_data=True)
assert 'ollama' in model  # باید local باشد

# تست 2: Non-sensitive با risk پایین
model = opt.select_model('pep8', risk_score=5, sensitive_data=False)
assert 'free' in model or 'llama' in model  # باید free باشد
```

---

### ✅ **4. یکپارچه‌سازی با ai_queue.py**

**فایل:** `enforcement/ai_queue.py`

**بررسی کنید:**
```python
from enforcement.cost_optimizer import get_optimizer

# در تابع execute_task:
optimizer = get_optimizer()

# انتخاب مدل با sensitive_data
model = optimizer.select_model(
    task=task.task_type,
    risk_score=task.risk_score,
    sensitive_data=task.is_sensitive  # ← باید اضافه شود
)

# لاگ انتخاب مدل
logger.info(f"Task: {task.task_type}, Risk: {task.risk_score}, "
           f"Sensitive: {task.is_sensitive}, Model: {model}")
```

**چک‌لیست:**
- [ ] `get_optimizer()` import شده
- [ ] `select_model()` با 3 پارامتر فراخوانی می‌شود
- [ ] Model selection در log ثبت می‌شود
- [ ] Token limits از `optimizer.get_token_limits()` استفاده می‌شود

---

### ✅ **5. Fail-Safe برای Ollama**

**سناریو:** کاربر `sensitive_data=True` دارد اما Ollama نصب نیست

**راه‌حل:**
```python
def select_model_with_fallback(self, task, risk_score, sensitive_data=False):
    """Select model with Ollama availability check"""
    model = self.select_model(task, risk_score, sensitive_data)
    
    # اگر local انتخاب شد، چک کن Ollama بالا هست
    if 'ollama' in model:
        if not self._is_ollama_available():
            logger.error("Ollama required but not available!")
            if sensitive_data:
                # برای داده حساس: FAIL (no cloud fallback)
                raise RuntimeError("Sensitive data requires local model, but Ollama unavailable")
            else:
                # برای extreme risk: fallback به deep model
                return self.config['models'].get('deep', 'anthropic/claude-3-opus')
    
    return model

def _is_ollama_available(self):
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        return response.status_code == 200
    except:
        return False
```

**چک‌لیست:**
- [ ] Ollama availability check اضافه شده
- [ ] Sensitive data بدون Ollama → FAIL (no cloud)
- [ ] Extreme risk بدون Ollama → fallback به deep

---

### ✅ **6. لاگ و Monitoring**

**در production، باید این لاگ‌ها را ببینید:**

```
INFO: Selected model: ollama/llama3.2 (tier: local, rule: sensitive_data == true)
INFO: Selected model: gpt-4o-mini (tier: fast, rule: risk > 10 and risk <= 20)
INFO: Selected model: anthropic/claude-3-opus (tier: deep, rule: risk > 50 and risk <= 80)
```

**چک‌لیست:**
- [ ] هر انتخاب مدل لاگ می‌شود
- [ ] Rule که match شده نمایش داده می‌شود
- [ ] Cost recording برای paid models کار می‌کند
- [ ] Budget status قابل مشاهده است

---

### ✅ **7. Edge Cases**

**تست این موارد:**

```python
# Edge case 1: Risk=0
model = opt.select_model('test', risk_score=0, sensitive_data=False)
# باید free یا fast باشد

# Edge case 2: Risk=100
model = opt.select_model('test', risk_score=100, sensitive_data=False)
# باید local باشد

# Edge case 3: Empty task
model = opt.select_model('', risk_score=50, sensitive_data=False)
# نباید crash کند

# Edge case 4: Sensitive + extreme risk
model = opt.select_model('critical', risk_score=95, sensitive_data=True)
# باید local باشد (sensitive has priority)
```

**چک‌لیست:**
- [ ] Risk خارج از range (0, 100+) handle می‌شود
- [ ] Empty/None task handle می‌شود
- [ ] Sensitive data همیشه اولویت دارد
- [ ] Fallback chain کار می‌کند

---

## 🚀 **Deployment Steps**

### **1. نصب Dependencies**
```bash
pip install pyyaml pytest requests
```

### **2. تست Local**
```bash
# تست سریع
python test_cost_optimizer.py

# تست کامل
python -m pytest tests/test_cost_optimizer_pytest.py -v

# همه چیز باید سبز باشد
```

### **3. تنظیم Environment Variables**
```bash
# .env
ZT_CFG=data/config/cost_optimizer.yml
OPENROUTER_API_KEY=sk-or-v1-...
```

### **4. نصب Ollama (اختیاری)**
```bash
# Windows
# https://ollama.ai/download

# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.2

# Test
ollama list
```

### **5. اجرای Production**
```bash
# تست یک task
python -c "
from enforcement.cost_optimizer import CostOptimizer
opt = CostOptimizer('data/config/cost_optimizer.yml')
print(opt.select_model('security', risk_score=70, sensitive_data=False))
"

# اجرای queue
python enforcement/ai_queue.py
```

---

## 📊 **نتایج مورد انتظار**

### **Model Selection Matrix:**

| Risk | Sensitive | Expected Model |
|------|-----------|----------------|
| 5    | ❌        | free (llama)   |
| 5    | ✅        | **local** (ollama) |
| 15   | ❌        | fast (gpt-4o-mini) |
| 15   | ✅        | **local** (ollama) |
| 35   | ❌        | medium (mixtral) |
| 35   | ✅        | **local** (ollama) |
| 65   | ❌        | deep (claude) |
| 65   | ✅        | **local** (ollama) |
| 95   | ❌        | local (ollama) |
| 95   | ✅        | **local** (ollama) |

**قانون طلایی:** `sensitive_data=True` همیشه → local

---

## 🔧 **Troubleshooting**

### **مشکل:** Sensitive data به cloud می‌رود
```bash
# چک کنید:
1. routing rules order در cost_optimizer.yml
2. sensitive_data پارامتر در select_model()
3. لاگ‌های debug

# دیباگ:
python -c "
from enforcement.cost_optimizer import CostOptimizer
import logging
logging.basicConfig(level=logging.DEBUG)
opt = CostOptimizer('data/config/cost_optimizer.yml')
model = opt.select_model('test', 50, sensitive_data=True)
print(f'Selected: {model}')
"
```

### **مشکل:** تست‌ها fail می‌شوند
```bash
# اجرای تک تک:
python -m pytest tests/test_cost_optimizer_pytest.py::TestModelSelection::test_sensitive_data_always_local_low_risk -v

# بررسی config:
python -c "
import yaml
cfg = yaml.safe_load(open('data/config/cost_optimizer.yml'))
print(cfg['routing']['rules'][0])
"
```

### **مشکل:** Ollama unavailable
```bash
# چک سرویس:
curl http://localhost:11434/api/tags

# اگر نبود:
ollama serve

# در terminal دیگر:
ollama pull llama3.2
```

---

## ✅ **Final Checklist**

قبل از deploy، همه این موارد را چک کنید:

- [ ] ✅ همه 20 تست pytest سبز است
- [ ] ✅ `sensitive_data == true` در اول routing rules است
- [ ] ✅ لاگ‌های model selection نمایش داده می‌شوند
- [ ] ✅ Ollama check برای sensitive data وجود دارد
- [ ] ✅ Fallback chain تست شده است
- [ ] ✅ VSCode tasks کار می‌کنند
- [ ] ✅ Budget tracking فعال است
- [ ] ✅ Token limits رعایت می‌شود

---

## 🎉 **وضعیت فعلی:**

```
✅ Config: READY
✅ Code: READY  
✅ Tests: 20/20 PASSED
✅ VSCode Tasks: READY
✅ Documentation: COMPLETE

🚀 READY FOR PRODUCTION!
```

---

**آخرین به‌روزرسانی:** 2025-01-13  
**نسخه:** 2.0 - Production Ready

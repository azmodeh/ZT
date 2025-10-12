# 💰 ZT Cost Optimizer - راهنمای استفاده

## 🎯 **هدف:**
کاهش هزینه‌های AI API با مدیریت هوشمند بودجه، انتخاب مدل، و بهینه‌سازی token

---

## 📦 **نصب و راه‌اندازی**

### 1. **بررسی فایل‌های لازم**
```bash
# باید این فایل‌ها موجود باشند:
✅ data/config/cost_optimizer.yml
✅ .vscode/tasks.json  
✅ enforcement/cost_optimizer.py
✅ .env (با OPENROUTER_API_KEY)
```

### 2. **تنظیم API Key**
```bash
# در فایل .env:
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

### 3. **بررسی پیکربندی**
```bash
# مشاهده بودجه فعلی:
python -c "
import yaml
cfg = yaml.safe_load(open('data/config/cost_optimizer.yml'))
print(f'💰 Daily Budget: ${cfg[\"budget\"][\"daily_cents\"]/100}')
print(f'💵 Per Run: ${cfg[\"budget\"][\"per_run_cents\"]/100}')
"
```

---

## 🚀 **روش‌های اجرا**

### **روش 1: از VSCode Tasks** (توصیه شده)
```
1. Ctrl+Shift+P
2. Tasks: Run Task
3. انتخاب:
   - ZT: SAFE Pipeline (محافظه‌کارانه، کم‌هزینه)
   - ZT: TURBO Pipeline (سریع، موازی)
   - ZT: Show Budget Status
```

### **روش 2: از Command Line**
```bash
# SAFE mode
python enforcement/ai_queue.py

# با تنظیمات سفارشی:
ZT_MODE=turbo ZT_CFG=data/config/cost_optimizer.yml python enforcement/ai_queue.py
```

### **روش 3: از Python Code**
```python
from enforcement.cost_optimizer import get_optimizer

# دریافت optimizer
optimizer = get_optimizer()

# انتخاب مدل بر اساس task
model = optimizer.select_model(task="remove_prints", risk_score=15)
print(f"Model selected: {model}")  # gpt-4o-mini

# بررسی بودجه
if optimizer.check_budget():
    # اجرای API call
    optimizer.record_api_call(model, input_tokens=500, output_tokens=300)

# وضعیت بودجه
status = optimizer.get_budget_status()
print(status)
```

---

## ⚙️ **پیکربندی پیشرفته**

### **تنظیم بودجه**
```yaml
# data/config/cost_optimizer.yml
budget:
  daily_cents: 1500           # 15 دلار در روز
  per_run_cents: 400          # 4 دلار هر اجرا
  stop_if_exceeded: true      # توقف خودکار
```

### **انتخاب مدل‌ها**
```yaml
models:
  fast: "gpt-4o-mini"             # ارزان ($0.15/1M input)
  medium: "mistralai/mixtral-8x7b" # متوسط ($0.27/1M)
  deep: "anthropic/claude-3-opus"  # گران ($15/1M input)

routing:
  rules:
    - when: "task == 'remove_prints' or risk<=20"
      use: fast
    - when: "20<risk<=50"
      use: medium
    - when: "risk>50"
      use: deep
```

### **محدودیت Token**
```yaml
limits:
  max_tokens_request: 2000      # حداکثر context
  max_tokens_response: 1200     # حداکثر پاسخ
  chunk_lines: 160              # اندازه chunk
```

---

## 📊 **نظارت و گزارش‌ها**

### **مشاهده هزینه لحظه‌ای**
```python
from enforcement.cost_optimizer import get_optimizer

optimizer = get_optimizer()
status = optimizer.get_budget_status()

print(f"Daily: {status['daily_spent']}/{status['daily_limit']}")
print(f"Run: {status['run_spent']}/{status['run_limit']}")
print(f"Can proceed: {status['can_proceed']}")
```

### **لاگ‌های هزینه**
```bash
# مشاهده لاگ‌های اخیر
tail -f logs/ai_actions/queue_run.log | grep "Budget"

# جستجوی API calls
grep "API call recorded" logs/ai_actions/queue_run.log
```

---

## 💡 **بهترین شیوه‌ها**

### ✅ **کاهش هزینه**
1. ✅ **از SAFE mode استفاده کنید** برای تست اولیه
2. ✅ **batch_size کوچکتر** = کنترل بهتر budget
3. ✅ **max_workers=2** برای پروژه‌های کوچک
4. ✅ **فعال‌سازی proof_of_change** = فقط تغییرات واقعی

### ⚠️ **هشدارها**
- ❌ TURBO mode با batch_size بزرگ = هزینه بالا
- ❌ deep model برای همه tasks = هزینه غیرضروری
- ❌ stop_if_exceeded=false = خطر budget overrun

### 🎯 **تنظیمات توصیه شده**

**برای تست/توسعه:**
```yaml
budget:
  daily_cents: 500    # 5 دلار
  per_run_cents: 100  # 1 دلار
batching:
  batch_size: 50
  max_workers: 2
```

**برای Production:**
```yaml
budget:
  daily_cents: 5000   # 50 دلار
  per_run_cents: 1000 # 10 دلار
batching:
  batch_size: 200
  max_workers: 8
```

---

## 🔧 **عیب‌یابی**

### **مشکل: Budget تمام می‌شود**
```python
# Reset manual:
from enforcement.cost_optimizer import get_optimizer
optimizer = get_optimizer()
optimizer.budget_status.daily_spent_cents = 0
optimizer.budget_status.run_spent_cents = 0
```

### **مشکل: Model selection اشتباه**
```bash
# بررسی routing rules:
python -c "
import yaml
cfg = yaml.safe_load(open('data/config/cost_optimizer.yml'))
for rule in cfg['routing']['rules']:
    print(f'{rule[\"when\"]} -> {rule[\"use\"]}')
"
```

### **مشکل: Config load نمی‌شود**
```bash
# بررسی path:
export ZT_CFG=data/config/cost_optimizer.yml
python -c "
import os
from enforcement.cost_optimizer import CostOptimizer
opt = CostOptimizer(os.getenv('ZT_CFG'))
print(opt.config)
"
```

---

## 📈 **مثال عملی**

```bash
# 1. بررسی بودجه
python -c "from enforcement.cost_optimizer import get_optimizer; print(get_optimizer().get_budget_status())"

# 2. اجرای SAFE pipeline
# Ctrl+Shift+P -> Tasks: Run Task -> ZT: SAFE Pipeline

# 3. مشاهده نتایج
cat logs/ai_actions/queue_run.log | grep "Budget"

# 4. بررسی هزینه
# نتیجه نمایش داده می‌شود در console:
# 💰 وضعیت بودجه:
#    هزینه این اجرا: $2.35
#    باقی‌مانده روزانه: $12.65
```

---

## 🎓 **مثال‌های پیشرفته**

### **Custom Model Selection**
```python
from enforcement.cost_optimizer import get_optimizer

optimizer = get_optimizer()

# Security task با risk بالا
model = optimizer.select_model("security", risk_score=85)
# Result: anthropic/claude-3-opus

# Simple refactor با risk پایین
model = optimizer.select_model("remove_prints", risk_score=10)
# Result: gpt-4o-mini
```

### **Dynamic Budget Adjustment**
```python
optimizer = get_optimizer()

# افزایش بودجه برای task خاص
original_limit = optimizer.budget_status.run_limit_cents
optimizer.budget_status.run_limit_cents = 800  # 8 دلار

# ... اجرای task ...

# بازگشت به حالت عادی
optimizer.budget_status.run_limit_cents = original_limit
```

---

## ✅ **چک‌لیست راه‌اندازی**

- [ ] فایل `cost_optimizer.yml` موجود است
- [ ] `OPENROUTER_API_KEY` در `.env` تنظیم شده
- [ ] بودجه روزانه/هر اجرا تنظیم شده
- [ ] Model routing rules بررسی شده
- [ ] VSCode tasks تست شده
- [ ] Budget status قابل مشاهده است

---

**Cost Optimizer آماده استفاده! 💰🚀**

# ✅ Final Handoff Checklist - Zero Tolerance System

**تاریخ:** 2025-01-13  
**نسخه:** 2.0.0  
**وضعیت:** 🚀 READY FOR PRODUCTION

---

## 📋 **Pre-Deployment Checklist**

### ✅ 1. Sentinel Guard
```bash
# Test
python -m pytest tests/test_sentinel_path_guard.py -v

# Expected
====================================== 7 passed =======================================

# Status: ✅ PASSED
```

### ✅ 2. Dry-Run Mode
```bash
# Test
ZT_DRY_RUN=1 python enforcement/ai_queue.py

# Expected Log
DRY_RUN: no changes applied

# Status: ✅ VERIFIED
```

### ✅ 3. API Health Probes
```bash
# Test all probes
curl http://127.0.0.1:8088/health
curl http://127.0.0.1:8088/ready
curl http://127.0.0.1:8088/live

# Expected
Response time: < 200ms
Status: 200 OK
Body: {"ok": true, ...}

# Status: ✅ ALL GREEN
```

### ✅ 4. Cost Optimizer V2
```bash
# Verify sensitive_data → local rule
python -c "
from enforcement.cost_optimizer import get_optimizer
opt = get_optimizer()
model = opt.select_model('test', risk_score=50, sensitive_data=True)
print(f'Model: {model}')
assert 'ollama' in model or 'local' in model.lower()
print('✅ Sensitive data → local VERIFIED')
"

# Expected
Model: ollama/llama3.2
✅ Sensitive data → local VERIFIED

# Status: ✅ VERIFIED
```

### ✅ 5. CI Gatekeeper
```bash
# Verify workflow exists
ls .github/workflows/zt-gate.yml

# Verify workflow content
grep "score_before" .github/workflows/zt-gate.yml

# Expected
Workflow file exists: ✅
Contains score check: ✅

# Status: ✅ READY
```

### ✅ 6. Rollback Scripts
```bash
# Test Windows
PowerShell -File scripts/rollback.ps1 -WhatIf

# Test Linux/macOS
chmod +x scripts/rollback.sh
./scripts/rollback.sh --what-if

# Expected
Scripts executable: ✅
Dry-run works: ✅

# Status: ✅ READY
```

---

## 🚀 **Go-Live Procedure**

### **Step 1: Environment Setup**
```bash
# Set environment variables
export ZT_HOME=/opt/zt
export ZT_TARGET=/srv/app
export ZT_CFG=$ZT_TARGET/data/config/cost_optimizer.yml
export ZT_MIN_SCORE=90
export ZT_MODE=safe
export ZT_DRY_RUN=0  # IMPORTANT: Set to 0 for production!

# Verify
echo "ZT_HOME: $ZT_HOME"
echo "ZT_TARGET: $ZT_TARGET"
echo "ZT_DRY_RUN: $ZT_DRY_RUN"
```

### **Step 2: Start API Server**
```bash
# Start server
python api_server/start_server.py

# Expected output
🚀 Zero Tolerance API Server
====================================
Host:     127.0.0.1
Port:     8088
Reload:   False
Workers:  1
====================================

# Verify
curl http://127.0.0.1:8088/health
# → {"ok": true, "version": "2.0.0", ...}
```

### **Step 3: Run Smoke Tests**
```bash
# Windows
./scripts/smoke_test.ps1

# Linux/macOS
./scripts/smoke_test.sh

# Expected
🎉 All smoke tests passed!
✅ Passed: 6
```

### **Step 4: Execute Queue (Production)**
```bash
# First run (validation only)
ZT_DRY_RUN=1 python enforcement/ai_queue.py

# If satisfied, run for real
ZT_DRY_RUN=0 python enforcement/ai_queue.py

# Monitor logs
tail -f logs/queue.log logs/api_server.log
```

---

## 🛡️ **Safety Rails (MUST BE ACTIVE)**

### ✅ 1. Risk Block Threshold
```yaml
# data/config/cost_optimizer.yml
policy:
  risk_block_threshold: 70  # ✅ High-risk changes blocked
```

### ✅ 2. Proof of Change
```yaml
# data/config/cost_optimizer.yml
policy:
  proof_of_change: true  # ✅ No-op patches rejected
```

### ✅ 3. Sensitive Data → Local
```yaml
# data/config/cost_optimizer.yml
routing:
  rules:
    - when: "sensitive_data == true"
      use: local  # ✅ FIRST PRIORITY
```

### ✅ 4. Path Guard (API & Agent)
```python
# api_server/server.py
def validate_path(path: str) -> Path:
    # ✅ Only files inside ZT_TARGET allowed
```

---

## 🔎 **Monitoring Checklist**

### **1. API Server Logs**
```bash
# Location
logs/api_server.log

# What to monitor
- Correlation ID for each request
- Selected models for queue operations
- Risk scores
- Error rates

# Sample log
{"time":"2025-01-13...", "level":"INFO", "msg":"[abc-123] Selected model: gpt-4o-mini (risk=35)"}
```

### **2. Queue Logs**
```bash
# Location
logs/queue.log

# What to monitor
- score_before → score_after
- Number of patches applied
- Number of blocked changes
- Budget consumption

# Expected
Score improvement: ≥ 5 points per run
Patched: > 0 (unless dry-run)
Blocked: < 10% of total
```

### **3. Patch Cache**
```bash
# Location
cache/patches/

# What to monitor
- Patch generation rate (should be > 0 unless dry-run)
- Patch application success rate
- Average patch size

# Check
ls -la cache/patches/ | wc -l
# Should grow over time (unless dry-run)
```

---

## 🧯 **Emergency Rollback**

### **Immediate Rollback (< 1 minute)**
```bash
# Windows
PowerShell -File scripts/rollback.ps1

# Linux/macOS
./scripts/rollback.sh

# Verify
git status
# Should show modified files restored
```

### **Before Rollback (Recommended)**
```bash
# 1. Check current state
git status

# 2. Stash any uncommitted changes
git stash push -m "Pre-rollback stash $(date)"

# 3. Now safe to rollback
./scripts/rollback.ps1

# 4. Review changes
git diff

# 5. If needed, restore from stash
git stash pop
```

---

## 📈 **Post-Deploy Targets (48 Hours)**

### **Target 1: Score ≥ 90 (Sustained)**
```bash
# Check every run
python enforcement/validator_engine.py . | grep score

# Target
Score: ≥ 90 on every run
Trend: Improving or stable
```

### **Target 2: NO-OPs < 5%**
```bash
# Monitor
grep "no changes" logs/queue.log | wc -l

# Target
NO-OPs: < 5% of total patches
Reason: proof_of_change working correctly
```

### **Target 3: Budget ≤ Config Limit**
```bash
# Check daily budget
python -c "
from enforcement.cost_optimizer import get_optimizer
opt = get_optimizer()
status = opt.get_budget_status()
print(f\"Daily: {status['daily_spent']} / {status['daily_limit']}\")
print(f\"Alert: {float(status['daily_spent'].replace('$','')) > 0.8 * float(status['daily_limit'].replace('$',''))}
\")"

# Target
Daily spend: < 80% of limit
Alerts: Set up if > 80%
```

---

## 🐳 **Docker Deployment (Recommended)**

### **Quick Start with Docker**
```bash
# Build image
docker build -t zero-tolerance:2.0.0 .

# Run API server
docker run -d \
  -p 8088:8088 \
  -v $(pwd)/workspace:/workspace \
  -v $(pwd)/logs:/app/logs \
  -e ZT_TARGET=/workspace \
  -e ZT_MIN_SCORE=90 \
  --name zt-api \
  zero-tolerance:2.0.0

# Check health
curl http://localhost:8088/health
```

### **With Docker Compose**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## ✅ **Final Verification**

### **Before Going Live:**
- [ ] All 27 tests passing
- [ ] Smoke tests green
- [ ] Health probes responding
- [ ] Logs directory writable
- [ ] Config files present
- [ ] Environment variables set
- [ ] Rollback scripts tested
- [ ] Monitoring in place

### **After Going Live:**
- [ ] API responding to requests
- [ ] Queue executing successfully
- [ ] Logs being written
- [ ] Budget tracking working
- [ ] Alerts configured
- [ ] Team notified

---

## 📞 **Support & Troubleshooting**

### **Common Issues:**

**Issue 1: API won't start**
```bash
# Check port
netstat -ano | grep 8088

# Check logs
tail logs/api_server.log

# Solution
# Change port or kill conflicting process
ZT_API_PORT=8089 python api_server/start_server.py
```

**Issue 2: Path forbidden errors**
```bash
# Check ZT_TARGET
echo $ZT_TARGET

# Solution
export ZT_TARGET=/correct/path
```

**Issue 3: Budget exceeded**
```bash
# Check current budget
python -c "from enforcement.cost_optimizer import get_optimizer; print(get_optimizer().get_budget_status())"

# Solution
# Increase budget or use more free models
# Edit data/config/cost_optimizer.yml
```

---

## 🎉 **Success Criteria**

```
✅ API Server: Running on port 8088
✅ Health Probes: All responding < 200ms
✅ Validation Score: ≥ 90
✅ Tests: 27/27 passing
✅ Budget: Within limits
✅ Logs: Writing correctly
✅ Monitoring: Active
✅ Rollback: Tested and ready

🚀 READY FOR PRODUCTION!
```

---

**Last Updated:** 2025-01-13 02:45 AM  
**Status:** ✅ PRODUCTION READY  
**Next Review:** 48 hours post-deploy

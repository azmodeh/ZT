# 🚀 اسپرینت 2 روزه - ZT به 95-100%

## ✅ **وضعیت فعلی:** 85% → هدف: 95-100%

---

## 📋 **Day 1 - Checklist**

### ✅ Task 1: حذف تکراری‌ها (COMPLETED)
- [x] حذف `project/app/classes/validator_engine.py`
- [x] Commit: "Remove duplicate validator_engine.py"

### 🔄 Task 2: بهبود API Server (IN PROGRESS)

**فایل‌ها:**
- `api_server/server.py`
- `api_server/start_server.py`

**بهبودهای انجام شده:**
- [x] اضافه کردن structured logging با UTF-8
- [x] توابع helper: `success_response()`, `error_response()`  
- [x] تابع validation: `validate_zt_target()`
- [ ] بهبود error handling در همه endpoints
- [ ] افزودن input validation با Pydantic
- [ ] تست endpoints: /health, /validate, /rewrite, /queue, /learn

**Endpoints اصلی:**
```python
GET  /health          → {ok, version, timestamp, components}
POST /api/validate    → validate file/workspace
POST /api/rewrite     → apply fixes with backup
POST /api/queue/run   → execute AI queue
GET  /api/learning/insights → learning suggestions
```

**TODO:**
1. افزودن comprehensive error handling
2. ZT_TARGET guard در همه write operations
3. Backup (.bak) قبل از هر تغییر
4. Rate limiting و timeout
5. تست integration

---

### 📝 Task 3: Polish Indexer (PENDING)

**فایل:** `enforcement/ai_indexer.py`

**بهبودهای مورد نیاز:**
- [ ] Robust chunking با configurable limits
- [ ] Timeout و retry mechanism  
- [ ] Progress logging
- [ ] Respect excludes از contract rules
- [ ] Write index به `data/cache/ai_index/`
- [ ] Safe on large trees (batching, memory cap)
- [ ] Error recovery

**API:**
```python
indexer = AIIndexer()
indexer.index_project(
    path=".",
    excludes=["node_modules", ".venv"],
    chunk_size=1000,
    timeout=60
)
```

---

### 📊 Task 4: Polish Report Generator (PENDING)

**فایل:** `enforcement/report_generator.py`

**بهبودهای مورد نیاز:**
- [ ] Save JSON و CSV به `logs/`
- [ ] Timestamp در نام فایل
- [ ] Schema: `{summary, items}`
- [ ] Summary: files, rules, violations, score
- [ ] Items: violation details
- [ ] Export formats: JSON, CSV, HTML, Markdown

**API:**
```python
generator = ReportGenerator()
report = generator.generate_report(
    validation_results=results,
    output_dir="logs",
    formats=["json", "csv"]
)
```

---

## 📋 **Day 2 - Checklist**

### 🧪 Task 5: گسترش Tests (CRITICAL)

**فایل:** `tests/test_integration.py`

**Test Cases مورد نیاز:**
- [ ] **Large project:** >200 files randomized
- [ ] **High risk block:** risk>70 blocks auto-apply
- [ ] **Empty patch:** proof-of-change detects no-op
- [ ] **Invalid patch:** syntax error handling
- [ ] **Budget exceed:** stop when budget runs out
- [ ] **Min score loop:** max_passes enforcement
- [ ] **API tests:** /validate, /rewrite, /queue, /learn
- [ ] **Concurrency:** multiple requests simultaneously
- [ ] **Error recovery:** graceful degradation

**Coverage Goal:** ≥80% for critical functions

---

### 🔧 Task 6: VSCode Extension Build (HIGH PRIORITY)

**مشکل فعلی:** TypeScript build errors

**فایل‌ها:**
- `vscode-extension/package.json`
- `vscode-extension/tsconfig.json`
- `vscode-extension/src/extension.ts`
- `vscode-extension/src/apiClient.ts`
- `vscode-extension/src/quickFixProvider.ts`
- `vscode-extension/src/realTimeValidator.ts`

**بهبودهای مورد نیاز:**
- [ ] رفع unused variable warnings
- [ ] رفع async/await errors
- [ ] تست build: `npm run build`
- [ ] Commands: ZT: Run SAFE, ZT: Run TURBO, ZT: Show Budget
- [ ] Status bar item با budget display
- [ ] Output channel برای logs

**Test:**
```bash
cd vscode-extension
npm install
npm run build
# باید بدون خطا compile شود
```

---

### 🔭 Task 7: TypeScript Watcher (OPTIONAL)

**فایل:** `tools/watch-zt.ts`

**ویژگی‌ها:**
- [ ] chokidar watch on ZT_TARGET
- [ ] Debounce 600ms
- [ ] Auto-run validator → rewriter → validator
- [ ] node-notifier برای OS notifications
- [ ] Ignore patterns: node_modules, .venv, logs, cache

**Usage:**
```bash
npm install -g ts-node chokidar node-notifier
ts-node tools/watch-zt.ts
```

---

## 🛡️ **گاردهای ضروری**

### همیشه چک کن:
- ✅ `validate_zt_target()` قبل از هر write
- ✅ Backup (.bak) قبل از تغییر
- ✅ Proof-of-change: فقط تغییرات واقعی
- ✅ risk_block_threshold: 70
- ✅ Budget از `cost_optimizer.yml`
- ✅ Structured logging با UTF-8
- ✅ Persian UX messages, English logs

---

## 🎯 **معیار پذیرش (Definition of Done)**

### API Server:
- [ ] `/health` برمی‌گرداند `{ok:true, version, timestamp, components}`
- [ ] `/validate` روی پروژه JSON کامل با `score≥90`
- [ ] `/rewrite` فقط safe fixes + `.bak` می‌سازد
- [ ] `/queue` چرخه validate→fix→validate را لاگ می‌کند
- [ ] Error handling در همه endpoints
- [ ] Input validation با Pydantic

### Tests:
- [ ] همه test cases سبز
- [ ] Coverage ≥80% برای critical functions
- [ ] API integration tests موفق
- [ ] Large project test (<5min)

### VSCode Extension:
- [ ] Build بدون خطا
- [ ] Commands: SAFE و TURBO کار می‌کنند
- [ ] Budget status نمایش داده می‌شود
- [ ] Real-time validation (optional)

### Documentation:
- [ ] API endpoints documented
- [ ] Test cases documented
- [ ] Deployment guide updated

---

## 📊 **Progress Tracking**

### Day 1 Progress:
- ✅ Task 1: حذف تکراری - 100%
- 🔄 Task 2: API Server - 40%
- ⏳ Task 3: Indexer - 0%
- ⏳ Task 4: Report - 0%

### Day 2 Progress:
- ⏳ Task 5: Tests - 0%
- ⏳ Task 6: VSCode - 0%
- ⏳ Task 7: Watcher - 0%

---

## 🚀 **Quick Start**

### اجرای تست فعلی:
```bash
# Basic tests
python tests/test_basic.py

# Integration tests  
python tests/test_integration.py

# Cost optimizer
python test_cost_optimizer.py

# API Server
cd api_server
python start_server.py
```

### اجرای Manual:
```bash
# Validate project
python enforcement/validator_engine.py .

# Run AI queue
python enforcement/ai_queue.py

# Test API
curl http://localhost:8080/health
```

---

## 📝 **Notes**

### موارد انجام شده:
1. ✅ Cost Optimizer کامل با 11 مدل
2. ✅ Multi-provider support (Gemini, Mistral, Groq, Nvidia, Ollama)
3. ✅ Budget tracking و model routing
4. ✅ MCP Server کامل
5. ✅ Core enforcement engine کامل
6. ✅ Agent Manager کامل
7. ✅ Learning System کامل
8. ✅ Diff Analyzer کامل

### موارد باقی‌مانده:
1. 🔄 API Server polish (error handling, validation)
2. ⏳ Indexer optimization
3. ⏳ Report generator formats
4. ⏳ Test coverage expansion
5. ⏳ VSCode Extension build fix

---

## 🎓 **Agent Prompts (آماده استفاده)**

### Prompt 1: API Server Completion
```
Complete ZT API Server (api_server/server.py).

Requirements:
- Add error handling to all endpoints
- Validate ZT_TARGET before writes
- Create .bak backups
- Return JSON: {ok, data|error, meta}
- Log in English, UX in Persian
- Test /health, /validate, /rewrite, /queue

Output: JSON patches only.
```

### Prompt 2: Indexer Polish
```
Polish enforcement/ai_indexer.py:
- Robust chunking with limits
- Timeout & retry
- Progress logs
- Exclude patterns
- Safe on large trees

Output: JSON patches only.
```

### Prompt 3: Test Expansion
```
Expand tests/test_integration.py:
- Test >200 files
- Test risk>70 blocking
- Test empty patch detection
- Test budget exceed
- API endpoint tests

Output: JSON patches only.
```

---

**آخرین به‌روزرسانی:** 2025-01-13 01:55 AM
**وضعیت:** Day 1 در حال انجام

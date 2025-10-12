# Zero Tolerance System 🎯

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Quality](https://img.shields.io/badge/code%20quality-90%2B%25-green.svg)](https://github.com/yourusername/zero-tolerance)

**سیستم اجرای قراردادهای کیفیت کد با Zero Tolerance - هوش مصنوعی پیشرفته برای تضمین کیفیت کد Python**

## 🌟 ویژگی‌های کلیدی

- 🔍 **اعتبارسنجی هوشمند**: تشخیص خودکار تخلف‌های کیفیت کد
- 🤖 **رفع خودکار AI**: اصلاح خودکار مشکلات با Multi-Agent System  
- 📊 **یادگیری مداوم**: بهبود عملکرد بر اساس تجربه
- 🌐 **API Server**: یکپارچگی کامل با IDE ها
- 🔌 **MCP Integration**: پشتیبانی از Windsurf و Claude
- 📈 **Real-time Monitoring**: نظارت زنده بر کیفیت کد

## 🏗️ معماری سیستم

```
Zero Tolerance System
├── 🧠 Core Engine
│   ├── ValidatorEngine     # موتور اعتبارسنجی
│   ├── AgentManager       # مدیریت AI Agents  
│   ├── AutoLearning       # سیستم یادگیری
│   └── DiffAnalyzer       # تحلیل‌گر تغییرات
├── 🌐 Integration Layer
│   ├── API Server         # REST API
│   ├── MCP Server         # Windsurf Integration
│   └── VSCode Extension   # IDE Integration
└── 📊 Intelligence Layer
    ├── Multi-Agent System # ایجنت‌های تخصصی
    ├── Learning System    # یادگیری از تجربه
    └── Risk Analysis      # تحلیل ریسک تغییرات
```

## 🚀 نصب سریع

### پیش‌نیازها
```bash
# Python 3.11+ required
python --version

# Node.js 18+ (برای VSCode Extension)
node --version
```

### نصب سیستم
```bash
# 1. کلون کردن پروژه
git clone https://github.com/yourusername/zero-tolerance.git
cd zero-tolerance

# 2. نصب وابستگی‌ها
pip install -r requirements.txt

# 3. تنظیم environment variables
cp .env.example .env
# ویرایش .env و اضافه کردن API keys

# 4. اجرای تست سیستم
python enforcement/validator_engine.py project/main.py
```

## 🎯 استفاده سریع

### اعتبارسنجی پروژه
```python
from enforcement.validator_engine import ValidatorEngine

# ایجاد validator
validator = ValidatorEngine()

# اعتبارسنجی فایل
result = validator.validate_file("your_project/main.py")
print(f"Violations: {len(result.violations)}")
```

### راه‌اندازی API Server
```bash
# اجرای API Server
cd api_server
python start_server.py

# تست API
curl http://localhost:8080/api/status
```

### یکپارچگی MCP با Windsurf
```json
{
  "mcpServers": {
    "ZT": {
      "command": "python",
      "args": ["d:/path/to/ZT/contract-enforcer-mcp/server.py"],
      "env": {
        "PYTHONPATH": "d:/path/to/ZT"
      }
    }
  }
}
```

## 📋 قوانین Zero Tolerance

### ✅ الزامات اصلی
- **حداکثر 4 خط در main.py** (غیر از docstring)
- **بدون print()** - فقط structured logging
- **Type hints اجباری** برای همه functions
- **حداکثر 300 خط در هر فایل**
- **حداکثر 79 کاراکتر در هر خط**
- **بدون hardcoded values** - استفاده از config
- **فقط absolute imports**
- **YAML برای configuration**

### 🎯 هدف کیفیت
- **حداقل 90% compliance score**
- **صفر تخلف critical**
- **کد تمیز و قابل نگهداری**

## 🛠️ اجزای سیستم

### 🧠 هسته سیستم
| جزء | توضیح | وضعیت |
|-----|--------|--------|
| ValidatorEngine | موتور اصلی اعتبارسنجی | ✅ کامل |
| AgentManager | مدیریت AI Agents | ✅ کامل |
| AutoLearning | یادگیری خودکار | ✅ کامل |
| DiffAnalyzer | تحلیل تغییرات | ✅ کامل |

### 🌐 لایه یکپارچگی
| جزء | توضیح | وضعیت |
|-----|--------|--------|
| API Server | REST API کامل | ✅ آماده |
| MCP Server | یکپارچگی Windsurf | ✅ آماده |
| VSCode Extension | افزونه VSCode | ✅ آماده |

## 🔧 پیکربندی

### Environment Variables
```bash
# API Configuration
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# ZT Settings
ZT_ENV=production
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
```

### Contract Rules
فایل `enforcement/contract_rules.yml`:
```yaml
max_line_length:
  enabled: true
  limit: 79

no_print:
  enabled: true
  
type_hints_required:
  enabled: true
```

## 🧪 تست و کیفیت

```bash
# اجرای تست‌های سیستم
python -m pytest tests/ -v

# بررسی کیفیت کد
flake8 enforcement/
black enforcement/ --check

# تست عملکرد MCP
python contract-enforcer-mcp/server.py --test
```

## 📊 مثال خروجی

```json
{
  "file": "project/main.py",
  "violations": 0,
  "critical": 0,
  "warnings": 0,
  "execution_time": 0.002,
  "compliance_score": 100
}
```

## 🤝 مشارکت

1. Fork کنید
2. Feature branch بسازید (`git checkout -b feature/AmazingFeature`)
3. تغییرات را commit کنید (`git commit -m 'Add AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request بزنید

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است. [LICENSE](LICENSE) را برای جزئیات ببینید.

## 🙏 تشکر

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP implementation
- [FastAPI](https://fastapi.tiangolo.com/) - API framework
- [Pydantic](https://pydantic.dev/) - Data validation

## 📞 پشتیبانی

- 📧 Email: support@zerotolerance.dev
- 💬 Discord: [ZT Community](https://discord.gg/zerotolerance)
- 📖 Docs: [docs.zerotolerance.dev](https://docs.zerotolerance.dev)

---

**Zero Tolerance System - کیفیت کد بدون مصالحه! 🎯**

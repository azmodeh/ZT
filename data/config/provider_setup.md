# 🌐 **AI Provider Setup Guide**

راهنمای تنظیم و استفاده از مدل‌های مختلف AI در ZT Server

---

## 📋 **لیست Providers پشتیبانی شده:**

### 1️⃣ **OpenRouter** (توصیه شده - یک API برای همه)
- ✅ دسترسی به 200+ مدل
- ✅ هزینه یکپارچه
- ✅ یک API key برای همه

### 2️⃣ **OpenAI**
- GPT-4o-mini
- GPT-4-turbo

### 3️⃣ **Google Gemini**
- Gemini 2.0 Flash (رایگان)
- Gemini Pro
- Gemini Experimental

### 4️⃣ **Anthropic Claude**
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

### 5️⃣ **Mistral AI**
- Mixtral 8x7B
- Mistral Large
- Mistral Medium

### 6️⃣ **Groq** (فوق سریع!)
- Llama 3.3 70B
- Mixtral 8x7B

### 7️⃣ **Nvidia**
- Nemotron 70B
- Llama 3.1

### 8️⃣ **Ollama** (محلی/رایگان)
- Llama 3.2
- Mistral
- Qwen

---

## 🔑 **تنظیم API Keys**

### **روش 1: OpenRouter (ساده‌ترین)**
```bash
# فقط یک کلید برای همه مدل‌ها
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

**مزایا:**
- ✅ یک API key برای همه providers
- ✅ قیمت‌گذاری یکپارچه
- ✅ بدون نیاز به مدیریت چند provider

**نحوه دریافت:**
1. ثبت‌نام در https://openrouter.ai
2. Dashboard → API Keys → Create Key
3. کپی کردن key و اضافه به `.env`

---

### **روش 2: Direct Provider Access**

#### **OpenAI:**
```bash
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
```
دریافت: https://platform.openai.com/api-keys

#### **Google Gemini:**
```bash
GEMINI_API_KEY=AIzaSy...your-key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```
دریافت: https://aistudio.google.com/apikey

#### **Anthropic:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
```
دریافت: https://console.anthropic.com/

#### **Groq:**
```bash
GROQ_API_KEY=gsk_your-key
GROQ_BASE_URL=https://api.groq.com/openai/v1
```
دریافت: https://console.groq.com/keys

#### **Mistral:**
```bash
MISTRAL_API_KEY=your-key
MISTRAL_BASE_URL=https://api.mistral.ai/v1
```
دریافت: https://console.mistral.ai/

---

### **روش 3: Ollama (Local/Free)**

```bash
# نصب Ollama
# Windows: https://ollama.ai/download
# Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh

# دانلود مدل
ollama pull llama3.2

# اجرا (پورت پیش‌فرض: 11434)
ollama serve
```

**تنظیم در ZT:**
```bash
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama  # dummy key
```

---

## ⚙️ **پیکربندی در cost_optimizer.yml**

### **مثال 1: استفاده از OpenRouter (توصیه شده)**
```yaml
models:
  free: "meta-llama/llama-3.3-70b-instruct:free"
  fast: "gpt-4o-mini"
  medium: "mistralai/mixtral-8x7b"
  deep: "anthropic/claude-3-opus"
```

**نیاز:** فقط `OPENROUTER_API_KEY`

---

### **مثال 2: Mix & Match Providers**
```yaml
models:
  free: "meta-llama/llama-3.3-70b-instruct:free"  # OpenRouter
  fast: "gpt-4o-mini"                              # OpenAI direct
  fast_groq: "groq/llama-3.3-70b-versatile"       # Groq (سریع!)
  medium: "mistralai/mixtral-8x7b"                 # Mistral
  deep: "claude-3-opus-20240229"                   # Anthropic
  local: "ollama/llama3.2"                         # محلی
```

**نیاز:** API keys مربوط به هر provider

---

### **مثال 3: بودجه صفر (فقط رایگان/محلی)**
```yaml
models:
  free: "meta-llama/llama-3.3-70b-instruct:free"
  fast: "google/gemini-2.0-flash-exp:free"
  medium: "google/gemini-2.0-flash-exp:free"
  deep: "ollama/llama3.2"  # محلی
  local: "ollama/qwen2.5:32b"

budget:
  daily_cents: 0
  per_run_cents: 0
```

---

## 🚀 **سناریوهای استفاده**

### **سناریو 1: توسعه‌دهنده تازه‌کار**
```yaml
# فقط مدل‌های رایگان
models:
  free: "meta-llama/llama-3.3-70b-instruct:free"
  fast: "google/gemini-2.0-flash-exp:free"
  medium: "google/gemini-2.0-flash-exp:free"
  deep: "ollama/llama3.2"

budget:
  daily_cents: 0
```

**هزینه:** $0/روز

---

### **سناریو 2: استارتاپ (بودجه محدود)**
```yaml
models:
  free: "meta-llama/llama-3.3-70b-instruct:free"
  fast: "gpt-4o-mini"
  medium: "groq/llama-3.3-70b-versatile"
  deep: "mistralai/mixtral-8x7b"

budget:
  daily_cents: 500  # $5/روز
```

**هزینه:** ~$5/روز (150 تراکنش)

---

### **سناریو 3: شرکت متوسط**
```yaml
models:
  free: "meta-llama/llama-3.3-70b-instruct:free"
  fast: "gpt-4o-mini"
  medium: "mistralai/mistral-large"
  deep: "anthropic/claude-3-opus"

budget:
  daily_cents: 5000  # $50/روز
```

**هزینه:** ~$50/روز (1000+ تراکنش)

---

### **سناریو 4: Enterprise (بدون محدودیت)**
```yaml
models:
  fast: "gpt-4o-mini"
  fast_groq: "groq/llama-3.3-70b-versatile"
  medium: "mistralai/mistral-large"
  medium_nvidia: "nvidia/llama-3.1-nemotron-70b"
  deep: "anthropic/claude-3-opus"
  deep_alt: "gpt-4-turbo"

budget:
  daily_cents: 50000  # $500/روز
  stop_if_exceeded: false
```

---

## 💡 **توصیه‌های بهینه‌سازی**

### **1. استفاده ترکیبی (Hybrid)**
```yaml
# کارهای ساده → رایگان
# کارهای متوسط → Groq (سریع و ارزان)
# کارهای حساس → Claude (دقیق)

routing:
  rules:
    - when: "risk<=20"
      use: free
    - when: "20<risk<=50"
      use: fast_groq  # Groq فوق سریع!
    - when: "risk>50"
      use: deep
```

**صرفه‌جویی:** تا 80% کاهش هزینه

---

### **2. استفاده از Ollama برای Privacy**
```yaml
# داده‌های حساس → محلی
routing:
  rules:
    - when: "task in ['sensitive_data', 'confidential']"
      use: local  # Ollama
```

**مزیت:** صفر انتقال داده به cloud

---

### **3. کش کردن نتایج**
```python
# در ai_queue.py
if result_in_cache:
    return cached_result  # $0 cost!
```

**صرفه‌جویی:** 40-60% کاهش تماس‌های تکراری

---

## 📊 **جدول مقایسه Providers**

| Provider | Speed | Cost | Quality | Use Case |
|----------|-------|------|---------|----------|
| **Llama (free)** | ⭐⭐⭐ | 🆓 | ⭐⭐⭐ | کارهای ساده |
| **GPT-4o-mini** | ⭐⭐⭐⭐ | $ | ⭐⭐⭐⭐ | همه‌کاره |
| **Groq** | ⭐⭐⭐⭐⭐ | $ | ⭐⭐⭐ | سرعت بالا |
| **Gemini Free** | ⭐⭐⭐⭐ | 🆓 | ⭐⭐⭐⭐ | تست/توسعه |
| **Mixtral** | ⭐⭐⭐ | $$ | ⭐⭐⭐⭐ | کیفیت خوب |
| **Claude Opus** | ⭐⭐⭐ | $$$$ | ⭐⭐⭐⭐⭐ | کار حساس |
| **Ollama** | ⭐⭐ | 🆓 | ⭐⭐⭐ | Privacy/Local |

---

## 🔧 **تست تنظیمات**

```bash
# تست OpenRouter
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# تست Ollama
curl http://localhost:11434/api/tags

# تست ZT با provider
python test_cost_optimizer.py
```

---

## 📞 **پشتیبانی**

- **OpenRouter:** https://openrouter.ai/docs
- **Ollama:** https://ollama.ai/docs
- **مشکل؟** issues در GitHub repository

---

**Providers آماده! انتخاب کنید و شروع کنید! 🚀**

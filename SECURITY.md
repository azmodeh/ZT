# Security Guidelines for ZT Project

## ⚠️ Before Committing to GitHub

### 1. Remove API Keys from contract_rules.yml

**File**: `enforcement/contract_rules.yml`

**Replace this:**
```yaml
ai_config:
  api_key: "AIzaSyDz3bfQ1iLNg_BvYgx5wzI9z6964_8v1Wo"
  base_url: "https://generativelanguage.googleapis.com/v1beta/openai/"
  model: "gemini-2.0-flash"
```

**With this:**
```yaml
ai_config:
  api_key: "${GEMINI_API_KEY}"
  base_url: "https://generativelanguage.googleapis.com/v1beta/openai/"
  model: "gemini-2.0-flash"
```

### 2. Create .env File (Not Committed)

Copy `.env.example` to `.env` and add your actual API key:

```bash
cp .env.example .env
```

Then edit `.env`:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Update ai_agent_config.yml

**File**: `data/config/ai_agent_config.yml`

**Replace:**
```yaml
api_key: "AIzaSyDz3bfQ1iLNg_BvYgx5wzI9z6964_8v1Wo"
```

**With:**
```yaml
api_key: "${GEMINI_API_KEY}"
```

## 🔒 Files to Check Before Commit

1. `enforcement/contract_rules.yml` - Remove API keys
2. `data/config/ai_agent_config.yml` - Remove API keys
3. Any test files with hardcoded credentials

## ✅ Safe to Commit

These files are safe and should be committed:
- `.env.example` (template only)
- `.gitignore` (protects secrets)
- All Python source files
- Documentation files
- Configuration templates

## 🚫 Never Commit

- `.env` file
- Any file with actual API keys
- Test files with real credentials
- Log files with sensitive data

## 📋 Pre-Commit Checklist

- [ ] Removed API keys from `contract_rules.yml`
- [ ] Removed API keys from `ai_agent_config.yml`
- [ ] Created `.env` file locally (not committed)
- [ ] Tested that project works with environment variables
- [ ] Checked no test files with secrets are included
- [ ] Verified `.gitignore` is working

## 🔧 Using Environment Variables

After setup, the project will read API keys from `.env` file automatically.

For manual testing:
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
```

## 📞 If API Key is Accidentally Committed

1. **Immediately revoke the API key** in Google Cloud Console
2. Generate a new API key
3. Update your local `.env` file
4. Remove the key from git history:
   ```bash
   git filter-branch --force --index-filter \
   "git rm --cached --ignore-unmatch enforcement/contract_rules.yml" \
   --prune-empty --tag-name-filter cat -- --all
   ```
5. Force push (if necessary)

## 🛡️ Best Practices

1. Always use environment variables for secrets
2. Never hardcode API keys in source files
3. Review changes before committing
4. Use `.env.example` as template
5. Keep `.gitignore` updated

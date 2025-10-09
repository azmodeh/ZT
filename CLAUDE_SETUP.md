# راه‌اندازی Zero Tolerance MCP در Claude Desktop

## مرحله 1: نصب Claude Desktop

اگر Claude Desktop ندارید، از لینک زیر دانلود کنید:
https://claude.ai/download

## مرحله 2: پیدا کردن فایل کانفیگ

### Windows:
```
%APPDATA%\Claude\claude_desktop_config.json
```

یا به صورت کامل:
```
C:\Users\[USERNAME]\AppData\Roaming\Claude\claude_desktop_config.json
```

### macOS:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Linux:
```
~/.config/Claude/claude_desktop_config.json
```

## مرحله 3: ویرایش فایل کانفیگ

فایل `claude_desktop_config.json` را باز کنید و محتوای زیر را اضافه کنید:

```json
{
  "mcpServers": {
    "zero-tolerance": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "zt-zt-mcp-server:latest"
      ]
    }
  }
}
```

**نکته:** اگر قبلاً سرورهای MCP دیگری دارید، فقط بخش `"zero-tolerance"` را اضافه کنید:

```json
{
  "mcpServers": {
    "existing-server": {
      ...
    },
    "zero-tolerance": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "zt-zt-mcp-server:latest"
      ]
    }
  }
}
```

## مرحله 4: راه‌اندازی مجدد Claude Desktop

1. Claude Desktop را ببندید (کاملاً)
2. دوباره باز کنید
3. در پنجره چت، باید آیکون 🔌 یا منوی MCP را ببینید
4. سرور "zero-tolerance" باید در لیست باشد

## مرحله 5: تست کردن

در Claude Desktop، دستوری مانند این را امتحان کنید:

```
لطفاً از ابزار Zero Tolerance برای بررسی کیفیت کد استفاده کن
```

یا:

```
Can you validate this Python code using the Zero Tolerance tools?
```

## عیب‌یابی

### خطا: "Docker command not found"
- مطمئن شوید Docker Desktop نصب و در حال اجرا است
- Docker را به PATH سیستم اضافه کنید

### خطا: "Image not found"
- مطمئن شوید Docker image ساخته شده است:
  ```bash
  docker images | grep zt-zt-mcp-server
  ```
- اگر image وجود ندارد، دوباره build کنید:
  ```bash
  cd D:\Workdir\ZeroToleranceSystem\ZT
  docker-compose build
  ```

### سرور در لیست نیست
- فایل کانفیگ را دوباره بررسی کنید
- JSON را validate کنید (نباید syntax error داشته باشد)
- Claude Desktop را کاملاً ببندید و دوباره باز کنید

### لاگ‌های Docker
برای دیباگ، می‌توانید لاگ‌های Docker را ببینید:
```bash
docker logs $(docker ps -q --filter ancestor=zt-zt-mcp-server:latest)
```

## استفاده از Docker Hub (اختیاری)

اگر می‌خواهید image را در Docker Hub منتشر کنید:

1. Repository ایجاد کنید در https://hub.docker.com
2. Image را tag و push کنید:
   ```bash
   docker tag zt-zt-mcp-server:latest YOUR_USERNAME/zero-tolerance-mcp:latest
   docker push YOUR_USERNAME/zero-tolerance-mcp:latest
   ```
3. در کانفیگ Claude، از image جدید استفاده کنید:
   ```json
   "args": [
     "run",
     "-i",
     "--rm",
     "YOUR_USERNAME/zero-tolerance-mcp:latest"
   ]
   ```

## پشتیبانی

اگر مشکلی داشتید:
1. لاگ‌های Docker را بررسی کنید
2. مطمئن شوید Docker در حال اجرا است
3. فایل کانفیگ Claude را دوباره چک کنید
4. Claude Desktop را restart کنید

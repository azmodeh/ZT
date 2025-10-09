# Zero Tolerance MCP Server - Docker Deployment

این راهنما نحوه اجرای سرور Zero Tolerance MCP با استفاده از Docker را توضیح می‌دهد.

## پیش‌نیازها

- Docker Desktop نصب شده باشد
- Docker Compose (معمولاً با Docker Desktop نصب می‌شود)

## روش‌های اجرا

### 1. استفاده از Docker Compose (توصیه می‌شود)

```bash
# Build و اجرای container
docker-compose up -d

# مشاهده لاگ‌ها
docker-compose logs -f

# متوقف کردن
docker-compose down
```

### 2. استفاده مستقیم از Docker

```bash
# Build کردن image
docker build -t zero-tolerance-mcp:latest .

# اجرای container
docker run -d \
  --name zt-mcp \
  -p 8080:8080 \
  -e ZT_DOCKER_MODE=1 \
  -v $(pwd)/data:/app/data \
  zero-tolerance-mcp:latest

# مشاهده لاگ‌ها
docker logs -f zt-mcp

# متوقف کردن
docker stop zt-mcp
docker rm zt-mcp
```

### 3. اجرای تعاملی (برای دیباگ)

```bash
docker run -it \
  --name zt-mcp-debug \
  -e ZT_DOCKER_MODE=1 \
  zero-tolerance-mcp:latest \
  /bin/bash
```

## استفاده با Claude Desktop

برای استفاده از سرور MCP در Claude Desktop، فایل کانفیگ را به شکل زیر تنظیم کنید:

### Windows
مسیر: `%APPDATA%\Claude\claude_desktop_config.json`

### macOS
مسیر: `~/Library/Application Support/Claude/claude_desktop_config.json`

### محتوای فایل:

```json
{
  "mcpServers": {
    "zero-tolerance": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "zero-tolerance-mcp:latest"
      ]
    }
  }
}
```

## Deploy به Docker Hub

```bash
# Login به Docker Hub
docker login

# Tag کردن image
docker tag zero-tolerance-mcp:latest YOUR_USERNAME/zero-tolerance-mcp:latest

# Push کردن
docker push YOUR_USERNAME/zero-tolerance-mcp:latest
```

## متغیرهای محیطی

- `ZT_DOCKER_MODE`: فعال‌سازی حالت Docker (مقدار: `1`)
- `PYTHONUNBUFFERED`: غیرفعال کردن buffering برای لاگ‌ها (مقدار: `1`)
- `PYTHONPATH`: مسیر Python (مقدار: `/app`)

## عیب‌یابی

### مشاهده لاگ‌های دقیق:

```bash
docker logs zt-mcp --tail 100 -f
```

### ورود به container:

```bash
docker exec -it zt-mcp /bin/bash
```

### بررسی وضعیت health check:

```bash
docker inspect --format='{{json .State.Health}}' zt-mcp
```

## پورت‌ها

- `8080`: پورت HTTP (در صورت نیاز)

## حجم‌های ذخیره‌سازی

- `./data`: داده‌های پایدار پروژه

## توجه

اگر تغییراتی در کد ایجاد کردید، حتماً image را دوباره build کنید:

```bash
docker-compose build --no-cache
docker-compose up -d
```

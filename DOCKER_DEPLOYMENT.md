# 🐳 Docker Deployment Guide - Zero Tolerance System

**نسخه:** 2.0.0  
**آخرین به‌روزرسانی:** 2025-01-13

---

## 🚀 **Quick Start**

### **1. Prerequisites**
```bash
# Install Docker & Docker Compose
# Windows: Docker Desktop
# Linux: apt install docker.io docker-compose
# macOS: brew install docker docker-compose

# Verify installation
docker --version
docker-compose --version
```

### **2. Setup Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # یا code .env

# Set required variables
OPENROUTER_API_KEY=sk-or-v1-...
WORKSPACE_PATH=./workspace
ZT_DRY_RUN=0
```

### **3. Build & Run**
```bash
# Build image
docker-compose build

# Start API server
docker-compose up -d zt-api

# Check health
curl http://localhost:8088/health

# View logs
docker-compose logs -f zt-api
```

---

## 📋 **Services Overview**

### **1. zt-api (REST API Server)**
- **Port:** 8088
- **Purpose:** REST API for external integrations
- **Endpoints:** /health, /ready, /live, /validate, /rewrite, /queue, /learn
- **Auto-restart:** Yes

```bash
# Start
docker-compose up -d zt-api

# Test
curl http://localhost:8088/health

# Logs
docker-compose logs -f zt-api

# Stop
docker-compose stop zt-api
```

### **2. zt-queue (Background Worker)**
- **Purpose:** AI-powered code fixes
- **Mode:** Run-once (no auto-restart)
- **Dependencies:** Requires zt-api healthy

```bash
# Run queue (one-time)
docker-compose run --rm zt-queue

# Dry-run
ZT_DRY_RUN=1 docker-compose run --rm zt-queue

# Logs
docker-compose logs zt-queue
```

### **3. zt-mcp (Optional - Windsurf Integration)**
- **Purpose:** MCP server for IDE integration
- **Profile:** mcp (not started by default)

```bash
# Start with MCP
docker-compose --profile mcp up -d

# Stop
docker-compose --profile mcp down
```

---

## 🔧 **Configuration**

### **Environment Variables (.env)**

```bash
# ============================================================================
# API Keys
# ============================================================================
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# ============================================================================
# Paths
# ============================================================================
WORKSPACE_PATH=./workspace       # Target code directory
ZT_API_PORT=8088                # API server port

# ============================================================================
# Zero Tolerance Settings
# ============================================================================
ZT_DRY_RUN=0                    # 0=real, 1=dry-run
ZT_MIN_SCORE=90                 # Minimum acceptable score
ZT_MODE=safe                    # safe or turbo
ZT_BATCH_SIZE=100               # Batch size for processing
ZT_MAX_WORKERS=4                # Parallel workers

# ============================================================================
# Logging
# ============================================================================
ZT_LOG_LEVEL=info               # debug, info, warning, error
```

---

## 📊 **Volume Mounts**

### **1. Workspace (Read/Write)**
```yaml
volumes:
  - ${WORKSPACE_PATH}:/workspace:rw
```
- **Purpose:** Target code to validate/fix
- **Permissions:** Read/Write
- **Location:** Configurable via WORKSPACE_PATH

### **2. Logs (Persistent)**
```yaml
volumes:
  - ./logs:/app/logs:rw
```
- **Purpose:** Application logs
- **Files:** api_server.log, queue.log, validator.log
- **Rotation:** Recommended

### **3. Configuration (Read-Only)**
```yaml
volumes:
  - ./data/config:/app/data/config:ro
```
- **Purpose:** ZT configuration files
- **Files:** cost_optimizer.yml, contract_rules.yml
- **Permissions:** Read-only

### **4. Cache (Docker Volume)**
```yaml
volumes:
  - zt-cache:/app/data/cache
  - zt-patches:/app/cache/patches
```
- **Purpose:** Performance optimization
- **Persistence:** Survives container restarts
- **Cleanup:** `docker volume prune`

---

## 🏗️ **Build Options**

### **Development Build**
```bash
# Build with cache
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Build specific service
docker-compose build zt-api
```

### **Production Build**
```bash
# Build optimized image
docker build -t zero-tolerance:2.0.0 \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  .

# Tag for registry
docker tag zero-tolerance:2.0.0 registry.example.com/zt:2.0.0

# Push to registry
docker push registry.example.com/zt:2.0.0
```

---

## 🚦 **Health Checks**

### **Liveness Probe (Fast)**
```bash
# Check if service is alive
curl http://localhost:8088/live

# Response
{"ok": true, "status": "alive", "ts": "2025-01-13T..."}
```

### **Readiness Probe (Deep)**
```bash
# Check if service is ready
curl http://localhost:8088/ready

# Response
{
  "ok": true,
  "status": "ready",
  "checks": {
    "target_accessible": true,
    "logs_writable": true,
    "config_loadable": true
  }
}
```

### **Docker Health Check**
```bash
# Check container health
docker ps
# Look for (healthy) status

# View health check logs
docker inspect zt-api | jq '.[0].State.Health'
```

---

## 📈 **Monitoring**

### **Container Stats**
```bash
# Real-time stats
docker stats zt-api

# One-time stats
docker stats --no-stream zt-api
```

### **Logs**
```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f zt-api

# Last 100 lines
docker-compose logs --tail=100 zt-api

# Since timestamp
docker-compose logs --since 2025-01-13T00:00:00 zt-api
```

### **Disk Usage**
```bash
# Check volumes
docker volume ls

# Volume size
docker system df -v

# Cleanup unused
docker volume prune
```

---

## 🔄 **Common Operations**

### **Restart Services**
```bash
# Restart all
docker-compose restart

# Restart specific
docker-compose restart zt-api

# Hard restart (stop + start)
docker-compose down
docker-compose up -d
```

### **Update Configuration**
```bash
# 1. Edit config
nano data/config/cost_optimizer.yml

# 2. Restart (config is mounted, no rebuild needed)
docker-compose restart zt-api

# 3. Verify
curl http://localhost:8088/health
```

### **Update Code**
```bash
# 1. Pull latest code
git pull

# 2. Rebuild image
docker-compose build

# 3. Restart with new image
docker-compose up -d --force-recreate

# 4. Verify
curl http://localhost:8088/health
```

---

## 🐛 **Troubleshooting**

### **Issue 1: Container won't start**
```bash
# Check logs
docker-compose logs zt-api

# Check last exit code
docker-compose ps

# Solution: Check environment variables
docker-compose config
```

### **Issue 2: Port already in use**
```bash
# Find process using port
netstat -ano | findstr :8088  # Windows
lsof -i :8088                  # Linux/macOS

# Solution: Change port
ZT_API_PORT=8089 docker-compose up -d
```

### **Issue 3: Permission denied**
```bash
# Check volume permissions
docker-compose exec zt-api ls -la /workspace

# Solution: Fix host permissions
chmod -R 755 ./workspace
```

### **Issue 4: Out of disk space**
```bash
# Check usage
docker system df

# Cleanup
docker system prune -a
docker volume prune

# Remove old images
docker image prune -a
```

---

## 🔒 **Security Best Practices**

### **1. Use Secrets (Production)**
```yaml
# Don't use .env for production
# Use Docker secrets instead

secrets:
  openrouter_key:
    external: true

services:
  zt-api:
    secrets:
      - openrouter_key
```

### **2. Run as Non-Root**
```dockerfile
# Already configured in Dockerfile
USER nobody
```

### **3. Read-Only Root Filesystem**
```yaml
services:
  zt-api:
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
```

### **4. Resource Limits**
```yaml
services:
  zt-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 📦 **Complete Deployment Example**

```bash
# 1. Clone repository
git clone https://github.com/your-org/zero-tolerance.git
cd zero-tolerance

# 2. Setup environment
cp .env.example .env
nano .env  # Add your API key

# 3. Build images
docker-compose build

# 4. Start services
docker-compose up -d zt-api

# 5. Verify health
curl http://localhost:8088/health
curl http://localhost:8088/ready

# 6. Run smoke tests
docker-compose run --rm zt-api python scripts/smoke_test.py

# 7. Run queue (dry-run first)
ZT_DRY_RUN=1 docker-compose run --rm zt-queue

# 8. Run queue (for real)
docker-compose run --rm zt-queue

# 9. Check logs
docker-compose logs -f

# 10. Monitor
docker stats
```

---

## 🎯 **Production Checklist**

- [ ] Environment variables configured
- [ ] API key set in .env
- [ ] Workspace path configured
- [ ] Health checks passing
- [ ] Logs directory writable
- [ ] Cache volumes created
- [ ] Smoke tests green
- [ ] Monitoring in place
- [ ] Backups configured
- [ ] Resource limits set

---

## 📞 **Quick Reference**

```bash
# Build
docker-compose build

# Start all
docker-compose up -d

# Start specific
docker-compose up -d zt-api

# Stop all
docker-compose down

# Restart
docker-compose restart

# Logs
docker-compose logs -f

# Health check
curl http://localhost:8088/live

# Run queue
docker-compose run --rm zt-queue

# Shell into container
docker-compose exec zt-api bash

# Cleanup
docker-compose down -v
docker system prune -a
```

---

**Last Updated:** 2025-01-13  
**Docker Version:** 20.10+  
**Docker Compose Version:** 2.0+

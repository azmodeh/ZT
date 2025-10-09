# Smithery Deployment Information

## Project Details

- **Name:** zero-tolerance-system
- **Version:** 1.0.0
- **Runtime:** Python 3.13
- **Transport:** STDIO (MCP Protocol)

## Dockerfile Configuration

### Base Image
```
python:3.13-slim-bookworm
```

### Entry Point
```bash
python -u main.py
```

### Environment Variables Required
```
PYTHONUNBUFFERED=1
ZT_DOCKER_MODE=1
PYTHONPATH=/app
```

### Port Exposure
- **Port 8080** (optional, for HTTP mode)
- **Primary mode:** STDIO (no port needed)

### Health Check
```bash
python -c "import sys; sys.exit(0)"
```
- Interval: 30s
- Timeout: 10s
- Start period: 10s
- Retries: 3

## File Structure in Container

```
/app/
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project metadata
├── contract-enforcer-mcp/    # MCP server code
│   └── server.py
├── enforcement/              # Core enforcement logic
├── app/                      # Application code
└── data/                     # Data files
```

## Dependencies

See `requirements.txt` for full list. Key dependencies:
- fastmcp>=0.9.0
- mcp>=1.0.0
- pyyaml>=6.0
- openai>=1.0.0
- requests>=2.28.0
- colorama>=0.4.0
- tqdm>=4.64.0
- radon>=5.1.0
- watchdog>=3.0.0

## Startup Command

```bash
python -u main.py
```

The `-u` flag ensures unbuffered output for proper logging.

## Expected Startup Logs

When the container starts successfully, you should see:

```
2025-10-09 23:14:01,123 - __main__ - INFO - Starting Zero Tolerance MCP Server...
2025-10-09 23:14:01,123 - __main__ - INFO - Docker mode enabled
2025-10-09 23:14:01,123 - __main__ - INFO - App root: /app
2025-10-09 23:14:01,123 - __main__ - INFO - Python path updated: ['/app/contract-enforcer-mcp', '/app', '/app']
2025-10-09 23:14:01,123 - __main__ - INFO - Server file exists: True
2025-10-09 23:14:01,123 - __main__ - INFO - Enforcement dir exists: True
2025-10-09 23:14:01,124 - __main__ - INFO - Importing server module...
2025-10-09 23:14:02,024 - __main__ - INFO - Server module imported successfully
2025-10-09 23:14:02,025 - __main__ - INFO - Starting MCP server...

╭────────────────────────────────────────────────────────────────╮
│                        FastMCP  2.0                            │
│                                                                │
│                 🖥️  Server name:     ZT                         │
│                 📦 Transport:       STDIO                      │
│                                                                │
│                 🏎️  FastMCP version: 2.12.4                     │
│                 🤝 MCP SDK version: 1.16.0                     │
╰────────────────────────────────────────────────────────────────╯

[10/09/25 23:14:02] INFO     Starting MCP server 'ZT' with transport 'stdio'
```

## Common Deployment Issues

### Issue 1: "ZT project structure validation failed"
**Cause:** The validation check `ZT_ROOT.name == "ZT"` fails in Docker.
**Solution:** Set `ZT_DOCKER_MODE=1` environment variable (already configured).

### Issue 2: "Module not found"
**Cause:** Python path not set correctly.
**Solution:** Ensure `PYTHONPATH=/app` is set (already configured).

### Issue 3: Timeout during deployment
**Cause:** Server not responding to health checks or taking too long to start.
**Solution:** 
- Check that `main.py` runs without errors
- Verify all dependencies are installed
- Ensure no blocking operations during startup

### Issue 4: Permission denied
**Cause:** Container running as root or wrong user.
**Solution:** Container now runs as `ztuser` (UID 1000).

## Testing Locally

### Build the image:
```bash
docker build -t zero-tolerance-mcp:test .
```

### Run the container:
```bash
docker run -it --rm \
  -e ZT_DOCKER_MODE=1 \
  -e PYTHONUNBUFFERED=1 \
  zero-tolerance-mcp:test
```

### Expected behavior:
- Container starts
- Logs appear showing "Starting Zero Tolerance MCP Server..."
- FastMCP banner displays
- Server waits for STDIO input (MCP protocol)

## Smithery-Specific Notes

### Transport Mode
This MCP server uses **STDIO transport**, not HTTP. It communicates via standard input/output, not HTTP requests.

### No Web Server
This is NOT a web server. It's an MCP (Model Context Protocol) server that:
- Reads JSON-RPC messages from stdin
- Writes responses to stdout
- Does not listen on any port (port 8080 is optional)

### Smithery Configuration
In `smithery.yaml`:
```yaml
startCommand:
  type: stdio
  command: python
  args:
    - main.py
  env:
    PYTHONPATH: "."
    ZT_DOCKER_MODE: "1"
```

## Debugging Deployment Failures

If deployment fails, check:

1. **Build logs:** Did all dependencies install?
2. **Startup logs:** Does `main.py` execute without errors?
3. **File permissions:** Can the container read all necessary files?
4. **Environment variables:** Are all required env vars set?
5. **Health check:** Does the health check command succeed?

## Contact & Support

- **Repository:** https://github.com/azmodeh/ZT
- **Docker Image:** Works locally with `docker-compose up`
- **Tested:** ✅ Local Docker build and run successful
- **Status:** ✅ Container runs healthy locally

## Alternative Deployment

If Smithery deployment continues to fail, the Docker image can be:
1. Pushed to Docker Hub
2. Used directly in Claude Desktop
3. Deployed to any Docker-compatible platform

See `CLAUDE_SETUP.md` for direct usage instructions.

Zero Tolerance Contract Enforcer
================================

Prerequisites
-------------
1. Python 3.10+ with virtual environment.
2. Node.js 18+ for VS Code hooks (install the `yaml` package).
3. Environment variable `OPENROUTER_API_KEY` set to your OpenRouter key.
4. Optional: define `ZT_TARGET` with the absolute path of the project to enforce. Defaults to `../app`.

Setup
-----
1. Install Python dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate            # PowerShell
   pip install -r enforcement/requirements.txt
   ```
2. Install Node dependencies for hooks:
   ```bash
   cd vscode
   npm init -y
   npm install yaml
   ```
3. Configure VS Code settings to load `vscode/extension.json`, `vscode/tasks.json`, and `vscode/keybindings.json` (either copy them into your workspace `.vscode/` folder or point settings sync to this directory).

Core Commands
-------------
1. Validate project:
   ```bash
   python enforcement/validator.py
   ```
2. Auto rewrite common issues:
   ```bash
   python enforcement/rewriter.py
   ```
3. Build AI index:
   ```bash
   python enforcement/ai_indexer.py
   ```
4. Run AI agent for a specific task:
   ```bash
   python enforcement/ai_agent.py "Remove hardcoded strings; add type hints"
   ```
5. Execute queued tasks:
   ```bash
   python enforcement/ai_queue.py
   ```

Folder Notes
------------
- `data/cache/ai_index/index.json` stores chunk metadata and embeddings.
- `data/cache/patches/` preserves raw patch payloads produced by the agent.
- `logs/validation_history.log` aggregates validation runs (UTF-8 encoded).
- `logs/ai_actions/queue_run.log` records queue execution history.

Operational Guidance
--------------------
- Logs remain in English to satisfy the contract; interactive console messages for humans are in Persian.
- Every modification performed by the AI agent or rewriter creates a `.bak` backup for safe rollback.
- If `OPENROUTER_API_KEY` is unavailable, the indexer falls back to deterministic hash vectors and the agent aborts gracefully.
- Adjust `enforcement/tasks.yml` to customize queue prompts or append additional tasks such as bespoke validators.
- Always rerun `python enforcement/validator.py` before committing repository changes.

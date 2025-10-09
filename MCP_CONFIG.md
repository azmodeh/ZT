# 🛠️ MCP Server Configuration for IDEs

Complete configuration guide for integrating the Zero Tolerance Python Contract Enforcer MCP server with various IDEs.

## 📋 **MCP Server Configuration Overview**

### Server Details
- **Name**: `zero-tolerance-contract-enforcer`
- **Command**: `python contract-enforcer-mcp/server.py`
- **Protocol**: stdio (stdio server)
- **Type**: Language Server Protocol compatible MCP server

## 🧩 **VSCode Configuration**

### Method 1: Direct Configuration in settings.json
```json
{
  "mcp.servers": {
    "zero-tolerance-contract-enforcer": {
      "command": "python",
      "args": [
        "contract-enforcer-mcp/server.py"
      ],
      "env": {
        "PYTHONPATH": "."
      },
      "stdio": true
    }
  }
}
```

### Method 2: Using extension.json (for extension development)
```json
{
  "contributes": {
    "mcp": {
      "servers": {
        "zero-tolerance-contract-enforcer": {
          "command": "python",
          "args": [
            "${workspaceFolder}/contract-enforcer-mcp/server.py"
          ],
          "options": {
            "env": {
              "PYTHONPATH": "${workspaceFolder}",
              "PATH": "${env:PATH}"
            }
          }
        }
      }
    }
  }
}
```

### Method 3: Workspace-specific configuration (.vscode/settings.json)
```json
{
  "mcp.servers": {
    "zero-tolerance-contract-enforcer": {
      "command": "python",
      "args": [
        "${workspaceFolder}/contract-enforcer-mcp/server.py"
      ],
      "options": {
        "cwd": "${workspaceFolder}",
        "env": {
          "PYTHONPATH": "${workspaceFolder}",
          "VIRTUAL_ENV": "${workspaceFolder}/.venv"
        }
      }
    }
  }
}
```

## 🧩 **PyCharm Configuration**

### Plugin Configuration
1. Install MCP plugin for PyCharm
2. Add server configuration in `Help > Edit Custom Properties`:
```
mcp.servers.zero-tolerance-contract-enforcer.command=python
mcp.servers.zero-tolerance-contract-enforcer.args=contract-enforcer-mcp/server.py
mcp.servers.zero-tolerance-contract-enforcer.env.PYTHONPATH=.
```

### Alternative: Run Configuration
Create a new Run Configuration:
- **Name**: Zero Tolerance MCP Server
- **Script**: `contract-enforcer-mcp/server.py`
- **Parameters**: None
- **Working Directory**: Project root
- **Environment Variables**: `PYTHONPATH=.`

## 🧩 **IntelliJ IDEA Configuration**

### MCP Server Integration
1. Install MCP Integration plugin
2. Configure in Settings (`Ctrl+Alt+S`):
```
Languages & Frameworks > MCP > Servers
```

Add new server:
- **Name**: zero-tolerance-contract-enforcer
- **Command**: `python`
- **Arguments**: `contract-enforcer-mcp/server.py`
- **Environment**: `PYTHONPATH=.`

## 🧩 **Vim/Neovim Configuration**

### Using mcp.nvim plugin
```lua
require('mcp').setup({
  servers = {
    ['zero-tolerance-contract-enforcer'] = {
      cmd = { 'python', 'contract-enforcer-mcp/server.py' },
      settings = {
        env = {
          PYTHONPATH = '.'
        }
      }
    }
  }
})
```

### Using nvim-lspconfig
```lua
local mcp = require('lspconfig').mcp
mcp.setup({
  cmd = { 'python', 'contract-enforcer-mcp/server.py' },
  root_dir = require('lspconfig').util.find_git_ancestor,
  settings = {
    env = { PYTHONPATH = '.' }
  }
})
```

## 🧩 **Emacs Configuration**

### Using lsp-mode
```elisp
(with-eval-after-load 'lsp-mode
  (add-to-list 'lsp-language-id-configuration
               '(python-mode . "zero-tolerance-contract-enforcer"))
  (lsp-register-client
   (make-lsp-client
    :new-connection (lsp-stdio-connection
                     '("python" "contract-enforcer-mcp/server.py"))
    :activation-fn (lsp-activate-on "python")
    :environment-fn (lambda () '(("PYTHONPATH" . ".")))
    :server-id 'zero-tolerance-contract-enforcer)))
```

## 🧩 **Sublime Text Configuration**

### Using LSP Package
Create `LSP.sublime-settings`:
```json
{
  "clients": {
    "zero-tolerance-contract-enforcer": {
      "command": ["python", "contract-enforcer-mcp/server.py"],
      "env": {
        "PYTHONPATH": "."
      },
      "enabled": true,
      "languageId": "python",
      "selector": "source.python"
    }
 }
}
```

## 🧩 **Neovim with Mason Configuration**

### Mason Integration
```lua
-- Install via mason
require('mason').setup()
require('mason-lspconfig').setup({
  ensure_installed = { 'zero-tolerance-contract-enforcer' }
})

-- Custom server registration
local lspconfig = require('lspconfig')
lspconfig.zero_tolerance_contract_enforcer = {
  default_config = {
    cmd = { 'python', 'contract-enforcer-mcp/server.py' },
    filetypes = { 'python' },
    root_dir = lspconfig.util.find_git_ancestor,
    single_file_support = true,
  }
}

lspconfig.zero_tolerance_contract_enforcer.setup({})
```

## 🧩 **Generic MCP Client Configuration**

### Standard Configuration Format
```json
{
  "servers": {
    "zero-tolerance-contract-enforcer": {
      "command": "python",
      "args": ["contract-enforcer-mcp/server.py"],
      "options": {
        "stdio": true,
        "env": {
          "PYTHONPATH": ".",
          "VIRTUAL_ENV": ".venv"
        },
        "cwd": "."
      }
    }
  }
}
```

## 🚀 **Available MCP Tools**

### Validation Tools
- `validate_code` - Validate Python codebase against contract rules
- `fix_violations` - Auto-fix contract violations  
- `check_compliance` - Check overall compliance status
- `generate_self_assessment` - Generate compliance report

### Example Usage
```bash
# Validate code
await client.call_tool("validate_code", {"base_path": "./project"})

# Fix violations
await client.call_tool("fix_violations", {"base_path": "./project"})

# Check compliance
await client.call_tool("check_compliance", {"base_path": "./project"})
```

## 📊 **MCP Resources**

### Available Resources
- `validation://latest-report` - Latest validation report
- `validation://history` - Validation history
- `validation://compliance-status` - Current compliance status

### Example Usage
```bash
# Access latest report
latest_report = await client.read_resource("validation://latest-report")

# Access history
history = await client.read_resource("validation://history")
```

## 🔧 **Troubleshooting**

### Common Issues and Solutions

#### Issue: Server not starting
**Solution**: Ensure Python environment is activated and dependencies are installed
```bash
pip install -r contract-enforcer-mcp/requirements.txt
```

#### Issue: MCP client not connecting
**Solution**: Check that the server command path is correct and file exists

#### Issue: PYTHONPATH errors
**Solution**: Ensure PYTHONPATH points to project root directory

#### Issue: Permission errors
**Solution**: Run IDE with appropriate permissions or check file access rights

## 📝 **Environment Setup**

### Prerequisites
```bash
# Install MCP dependencies
pip install mcp
pip install mcp-server

# Ensure project dependencies are installed
pip install -r enforcement/requirements.txt
```

### Virtual Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r contract-enforcer-mcp/requirements.txt
```

## 🔄 **Auto-Start Configuration**

### VSCode Auto-Start
```json
{
  "mcp.servers": {
    "zero-tolerance-contract-enforcer": {
      "command": "python",
      "args": ["contract-enforcer-mcp/server.py"],
      "options": {
        "stdio": true,
        "env": {"PYTHONPATH": "."}
      },
      "autoStart": true
    }
  }
}
```

### Startup Script Example
```bash
#!/bin/bash
# mcp-startup.sh
cd /path/to/your/project
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python contract-enforcer-mcp/server.py &
```

## 📚 **Best Practices**

1. **Always activate virtual environment** before starting MCP server
2. **Ensure PYTHONPATH** points to project root
3. **Use relative paths** in configuration for portability
4. **Test server connection** before relying on MCP features
5. **Keep MCP server updated** with latest contract rules
6. **Monitor MCP logs** for debugging information

This configuration enables full integration of the Zero Tolerance Python Contract Enforcer with your preferred IDE, providing real-time contract compliance checking and automated fixing capabilities.

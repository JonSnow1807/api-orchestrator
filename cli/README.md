# API Orchestrator CLI 🚀

Transform any codebase into production-ready APIs with a single command.

## Installation

```bash
# Via pip (coming soon to PyPI)
pip install api-orchestrator

# From source
git clone https://github.com/JonSnow1807/api-orchestrator
cd api-orchestrator/cli
pip install -e .
```

## Quick Start

```bash
# 1. Login to API Orchestrator
api-orchestrator login

# 2. Scan your codebase
api-orchestrator scan ./my-project

# 3. Your API artifacts are ready!
ls ./api-output/
```

## Features

### 🔍 Intelligent Code Scanning
```bash
# Auto-detect framework
api-orchestrator scan .

# Specify framework
api-orchestrator scan ./backend --framework fastapi

# Custom output directory
api-orchestrator scan . -o ./my-api-docs
```

### 🎭 Instant Mock Servers
```bash
# Start mock server from OpenAPI spec
api-orchestrator mock ./openapi.json --port 3000
```

### 👀 Watch Mode
```bash
# Auto-regenerate on file changes
api-orchestrator scan . --watch
```

### 📊 Task Management
```bash
# List all tasks
api-orchestrator list

# Check task status
api-orchestrator status <task-id>
```

## Commands

| Command | Description |
|---------|-------------|
| `login` | Authenticate with API Orchestrator |
| `logout` | Logout from current session |
| `scan` | Scan codebase and generate API artifacts |
| `mock` | Start mock server from OpenAPI spec |
| `list` | List all orchestration tasks |
| `status` | Check task status |
| `init` | Initialize project configuration |
| `config` | Show current configuration |

## Configuration

Create `.api-orchestrator.yml` in your project:

```yaml
version: "1.0"
framework: auto  # auto/fastapi/flask/express/django
output: ./api-output
options:
  include_tests: true
  include_mock: true
  include_ai_analysis: true
ignore:
  - node_modules
  - .git
  - __pycache__
  - "*.pyc"
  - .env
```

## Examples

### Basic Usage
```bash
# Scan current directory
api-orchestrator scan .

# Scan with specific framework
api-orchestrator scan ./src --framework express

# Generate only OpenAPI spec (no tests/mocks)
api-orchestrator scan . --no-tests --no-mock
```

### CI/CD Integration
```yaml
# GitHub Actions
- name: Generate API Docs
  run: |
    pip install api-orchestrator
    api-orchestrator login --email ${{ secrets.APO_EMAIL }} --password ${{ secrets.APO_PASSWORD }}
    api-orchestrator scan . -o ./docs/api
```

### Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: api-orchestrator
        name: Update API Documentation
        entry: api-orchestrator scan . -o ./docs/api
        language: system
        pass_filenames: false
```

## Output Structure

```
api-output/
├── openapi.json       # OpenAPI 3.0 specification
├── openapi.yaml       # YAML version
├── tests/             # Generated test suites
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── mock_server/       # Mock server implementation
└── analysis.json      # AI-powered insights
```

## VS Code Integration

Install the API Orchestrator VS Code extension for seamless IDE integration:

```bash
code --install-extension api-orchestrator.vscode-api-orchestrator
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APO_API_URL` | API server URL | `http://localhost:8000` |
| `APO_TOKEN` | Authentication token | - |
| `APO_CONFIG_DIR` | Config directory | `~/.api-orchestrator` |

## Troubleshooting

### Connection Issues
```bash
# Check API server
api-orchestrator config

# Use custom API URL
api-orchestrator login --api-url https://api.your-server.com
```

### Authentication
```bash
# Re-authenticate
api-orchestrator logout
api-orchestrator login
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@api-orchestrator.com
- 💬 Discord: [Join our community](https://discord.gg/api-orchestrator)
- 🐛 Issues: [GitHub Issues](https://github.com/JonSnow1807/api-orchestrator/issues)
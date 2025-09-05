# API Orchestrator VS Code Extension 🚀

Transform your code into production-ready APIs directly from VS Code! This extension brings the power of AI-driven API development right into your IDE.

## Features

### 🔍 **Instant API Discovery**
- Automatically detects API endpoints in your code
- Supports FastAPI, Flask, Django, Express, and more
- Real-time scanning as you type

### 📄 **OpenAPI Generation**
- Generate OpenAPI 3.0 specs with one click
- Automatic documentation from code comments
- Export to JSON/YAML formats

### 🎭 **Mock Servers**
- Start mock servers instantly from your specs
- Test your APIs before implementation
- Customizable response data

### 🧪 **Test Generation**
- Auto-generate test suites (pytest, Jest, Postman)
- Coverage analysis
- Integration and unit tests

### 🤖 **AI-Powered Analysis**
- Security vulnerability detection
- Performance optimization suggestions
- GDPR/HIPAA compliance checks
- Code quality recommendations

## Quick Start

1. **Install the extension** from VS Code Marketplace
2. **Login** to API Orchestrator:
   - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "API Orchestrator: Login"
   - Enter your credentials

3. **Scan your project**:
   - Press `Cmd+Shift+A` (Mac) or `Ctrl+Shift+A` (Windows/Linux)
   - Or right-click on any folder and select "API Orchestrator: Scan"

4. **View discovered APIs** in the sidebar panel

## Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `API Orchestrator: Scan Project` | Scan entire workspace for APIs | `Cmd/Ctrl+Shift+A` |
| `API Orchestrator: Scan Current File` | Scan active file | - |
| `API Orchestrator: Generate OpenAPI Spec` | Create OpenAPI documentation | - |
| `API Orchestrator: Start Mock Server` | Launch mock server | - |
| `API Orchestrator: Generate Tests` | Create test suites | - |
| `API Orchestrator: AI Analysis` | Run security & performance analysis | - |
| `API Orchestrator: Show Dashboard` | Open dashboard view | `Cmd/Ctrl+Shift+D` |

## Sidebar Views

The extension adds a dedicated sidebar with:
- **Discovered APIs**: List of all endpoints found
- **Mock Servers**: Running mock server instances
- **Tasks**: Orchestration task history
- **Statistics**: API metrics and insights

## Configuration

Configure the extension in VS Code settings:

```json
{
  "api-orchestrator.serverUrl": "http://localhost:8000",
  "api-orchestrator.autoScan": true,
  "api-orchestrator.includeMockServer": true,
  "api-orchestrator.includeTests": true,
  "api-orchestrator.includeAiAnalysis": true,
  "api-orchestrator.outputDirectory": "./api-output"
}
```

## Auto-Scan

The extension automatically scans files when you save them. Supported file types:
- Python (`.py`)
- JavaScript (`.js`)
- TypeScript (`.ts`)
- Java (`.java`)
- Go (`.go`)
- Ruby (`.rb`)

## Context Menu Integration

Right-click on:
- **Files**: Scan individual files for APIs
- **Folders**: Scan entire directories
- **Editor**: Generate specs from current file

## Output Structure

Generated artifacts are saved to your project:
```
api-output/
├── openapi.json       # OpenAPI 3.0 specification
├── openapi.yaml       # YAML version
├── tests/             # Generated test suites
├── mock_server/       # Mock server implementation
└── analysis.json      # AI-powered insights
```

## Requirements

- VS Code 1.74.0 or higher
- API Orchestrator account (free tier available)
- Active internet connection for AI features

## Installation

### From VS Code Marketplace
1. Open VS Code
2. Go to Extensions (Cmd+Shift+X)
3. Search for "API Orchestrator"
4. Click Install

### From VSIX
1. Download the `.vsix` file
2. Run: `code --install-extension api-orchestrator-1.0.0.vsix`

## Development

To contribute or run locally:

```bash
git clone https://github.com/JonSnow1807/api-orchestrator
cd api-orchestrator/vscode-extension
npm install
npm run compile
```

Press F5 in VS Code to launch a development instance.

## Support

- 📧 Email: support@api-orchestrator.com
- 💬 Discord: [Join our community](https://discord.gg/api-orchestrator)
- 🐛 Issues: [GitHub Issues](https://github.com/JonSnow1807/api-orchestrator/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Transform your code into APIs in seconds!** 🚀
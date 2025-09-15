#!/bin/bash

echo "🚀 Publishing API Orchestrator to PyPI and VS Code Marketplace"
echo "============================================================="

# 1. Package and Publish VS Code Extension
echo ""
echo "📦 Building VS Code Extension..."
cd vscode-extension

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    npm install
fi

# Compile TypeScript
npm run compile

# Package the extension
npx vsce package

echo "✅ VS Code extension packaged: api-orchestrator-1.0.0.vsix"
echo ""
echo "To publish to VS Code Marketplace:"
echo "1. Create publisher at https://marketplace.visualstudio.com/manage"
echo "2. Get Personal Access Token from Azure DevOps"
echo "3. Run: npx vsce publish"
echo ""

# 2. Publish CLI to PyPI
echo "📦 Publishing CLI to PyPI..."
cd ../cli

# Create README for PyPI
cat > README.md << 'EOF'
# API Orchestrator CLI

The most powerful API testing CLI tool. Better than Newman, with AI capabilities.

## Installation

```bash
pip install api-orchestrator-cli
```

## Quick Start

```bash
# Run a collection
api-orchestrator run collection.json

# Test with environment
api-orchestrator test --env production

# Lint OpenAPI spec
api-orchestrator lint openapi.yaml

# Generate mock server
api-orchestrator mock openapi.yaml --port 3000
```

## Features

- ✅ Newman-compatible commands
- ✅ Data-driven testing
- ✅ Parallel execution
- ✅ CI/CD integration
- ✅ Multiple reporters
- ✅ AI-powered testing

## Documentation

Full docs at: https://github.com/JonSnow1807/api-orchestrator

## License

MIT
EOF

# Build distribution packages
echo "Building distribution packages..."
python setup.py sdist bdist_wheel

echo ""
echo "✅ CLI packages built in dist/"
echo ""
echo "To publish to PyPI:"
echo "1. Create account at https://pypi.org"
echo "2. Get API token from https://pypi.org/manage/account/token/"
echo "3. Install twine: pip install twine"
echo "4. Upload to PyPI:"
echo "   For test: twine upload --repository testpypi dist/*"
echo "   For prod: twine upload dist/*"
echo ""

# 3. Quick publish commands (when ready)
cat > PUBLISH_COMMANDS.md << 'EOF'
# Publishing Commands

## VS Code Extension

```bash
cd vscode-extension
npx vsce publish
```

## PyPI Package

```bash
cd cli
# Test PyPI first
twine upload --repository testpypi dist/*

# Then production
twine upload dist/*
```

## Verify Installation

```bash
# Install from PyPI
pip install api-orchestrator-cli

# Test it works
api-orchestrator --version
```

## VS Code Extension Install

After publishing, users can:
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search "API Orchestrator"
4. Click Install

Or via command line:
```bash
code --install-extension api-orchestrator.api-orchestrator
```
EOF

echo "============================================================="
echo "✅ READY FOR PUBLISHING!"
echo ""
echo "📝 See PUBLISH_COMMANDS.md for detailed instructions"
echo ""
echo "⚠️  IMPORTANT BEFORE YC:"
echo "1. Publish CLI to PyPI (5 minutes)"
echo "2. Publish VS Code extension (5 minutes)"
echo "3. Test both work: pip install api-orchestrator-cli"
echo "4. Add to pitch: 'Available on PyPI and VS Code Marketplace'"
echo ""
echo "This makes you look MORE professional and production-ready!"
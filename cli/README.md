# 🚀 API Orchestrator CLI

> The ultimate API testing CLI - Newman killer with AI-powered features

[![PyPI version](https://badge.fury.io/py/api-orchestrator-cli.svg)](https://badge.fury.io/py/api-orchestrator-cli)
[![Python Support](https://img.shields.io/pypi/pyversions/api-orchestrator-cli.svg)](https://pypi.org/project/api-orchestrator-cli/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/JonSnow1807/api-orchestrator/blob/main/LICENSE)

## 🌟 Features

### **Newman Parity + AI Intelligence**
- ✅ **100% Newman Compatible** - Drop-in replacement for existing pipelines
- 🤖 **AI-Powered Analysis** - Security scanning and performance optimization
- 🚀 **Enterprise Ready** - SSO, RBAC, audit logging
- 🎯 **Multi-Protocol** - REST, GraphQL, WebSocket, gRPC, SOAP
- 📊 **Advanced Reporting** - HTML, JUnit, Allure, SARIF formats
- 🔄 **CI/CD Integration** - GitHub Actions, GitLab CI, Jenkins templates

## 📦 Installation

```bash
# Install via pip
pip install api-orchestrator-cli

# Verify installation
api-orchestrator --version
```

## 🚀 Quick Start

```bash
# Basic collection run (Newman compatible)
api-orchestrator run collection.json

# With environment and reporting
api-orchestrator run \
  --collection tests/api-tests.json \
  --environment envs/staging.json \
  --reporters cli,junit,html \
  --output-dir results/
```

## 🏢 CI/CD Integration

### **GitHub Actions**
```bash
api-orchestrator init ci github
```

### **GitLab CI**
```bash
api-orchestrator init ci gitlab
```

### **Jenkins**
```bash
api-orchestrator init ci jenkins
```

## 🆘 Support

- **Documentation**: [docs.streamapi.dev](https://docs.streamapi.dev)
- **Issues**: [GitHub Issues](https://github.com/JonSnow1807/api-orchestrator/issues)
- **Email**: support@streamapi.dev

## 📄 License

Apache 2.0 - see [LICENSE](LICENSE) file for details.
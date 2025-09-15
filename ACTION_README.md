# API Orchestrator GitHub Action

Run comprehensive API tests in your CI/CD pipeline using API Orchestrator - the AI-powered Postman alternative.

## Features

- **Multi-Protocol Support**: Test REST, GraphQL, WebSocket, gRPC, and SOAP APIs
- **AI-Powered Testing**: Natural language test generation and intelligent assertions
- **Performance Testing**: Built-in load testing and response time validation
- **Security Scanning**: Automatic detection of exposed secrets and vulnerabilities
- **Compliance Checks**: GDPR, HIPAA, SOC2, and PCI-DSS validation
- **Rich Reporting**: JSON, JUnit XML, HTML, and CLI output formats
- **Data-Driven Testing**: CSV and JSON data file support
- **Parallel Execution**: Run multiple test suites concurrently

## Usage

### Basic Example

```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run API Tests
        uses: ChinmayShrivastava/api-orchestrator@v1
        with:
          collection: './tests/api-collection.json'
          environment: 'production'
```

### Advanced Example

```yaml
name: Comprehensive API Testing
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 */6 * * *'  # Run every 6 hours

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run API Test Suite
        uses: ChinmayShrivastava/api-orchestrator@v1
        with:
          collection: './tests/postman_collection.json'
          environment: 'staging'
          reporters: 'cli,json,junit'
          bail: 'false'
          timeout: '60000'
          iterations: '3'
          api-key: ${{ secrets.API_ORCHESTRATOR_KEY }}
          
      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            test-results.json
            junit-report.xml
            
      - name: Publish Test Report
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: API Test Results
          path: 'junit-report.xml'
          reporter: java-junit
```

### Testing Specific Folders

```yaml
- name: Test Authentication Endpoints
  uses: ChinmayShrivastava/api-orchestrator@v1
  with:
    collection: './tests/collection.json'
    folder: 'Authentication'
    environment: 'production'
```

### Performance Regression Testing

```yaml
- name: Performance Regression Check
  uses: ChinmayShrivastava/api-orchestrator@v1
  with:
    collection: './tests/performance.json'
    environment: 'production'
    reporters: 'json'
    fail-on-error: 'true'
    
- name: Check Performance Regression
  run: |
    CURRENT_AVG=$(jq '.avg_response_time' test-results.json)
    BASELINE_AVG=$(cat baseline.json | jq '.avg_response_time')
    
    if (( $(echo "$CURRENT_AVG > $BASELINE_AVG * 1.1" | bc -l) )); then
      echo "Performance regression detected!"
      exit 1
    fi
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `collection` | Path to collection file (JSON/YAML) | No | `./api-tests.json` |
| `environment` | Environment file or name | No | `production` |
| `api-key` | API Orchestrator API key for cloud features | No | - |
| `reporters` | Test reporters (json, junit, html, cli) | No | `cli,json` |
| `bail` | Stop on first test failure | No | `false` |
| `timeout` | Request timeout in ms | No | `30000` |
| `delay` | Delay between requests in ms | No | `0` |
| `iterations` | Number of iterations to run | No | `1` |
| `folder` | Run specific folder from collection | No | - |
| `working-directory` | Working directory for tests | No | `./` |
| `fail-on-error` | Fail the action if tests fail | No | `true` |

## Outputs

| Output | Description |
|--------|-------------|
| `total` | Total number of tests |
| `passed` | Number of passed tests |
| `failed` | Number of failed tests |
| `duration` | Total duration in ms |
| `report-path` | Path to generated report |

## Supported Collection Formats

- **Postman Collections** (v2.1)
- **OpenAPI/Swagger** (3.0, 3.1)
- **API Orchestrator Native** (.apo)
- **Insomnia** (v4)
- **Thunder Client** (via import)

## Environment Variables

```yaml
env:
  API_BASE_URL: ${{ secrets.API_BASE_URL }}
  API_KEY: ${{ secrets.API_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Examples

### Load Testing

```yaml
- name: Load Test API
  uses: ChinmayShrivastava/api-orchestrator@v1
  with:
    collection: './tests/load-test.json'
    iterations: '100'
    timeout: '120000'
    reporters: 'json,html'
```

### Multi-Environment Testing

```yaml
strategy:
  matrix:
    environment: [development, staging, production]
    
steps:
  - name: Test ${{ matrix.environment }}
    uses: ChinmayShrivastava/api-orchestrator@v1
    with:
      collection: './tests/api.json'
      environment: ${{ matrix.environment }}
```

### Security Scanning

```yaml
- name: Security Scan
  uses: ChinmayShrivastava/api-orchestrator@v1
  with:
    collection: './tests/security.json'
    api-key: ${{ secrets.API_ORCHESTRATOR_KEY }}
    
- name: Check for Security Issues
  run: |
    if grep -q "SECURITY_ISSUE" test-results.json; then
      echo "Security vulnerabilities detected!"
      exit 1
    fi
```

## Comparison with Newman

| Feature | API Orchestrator | Newman |
|---------|------------------|--------|
| REST API Testing | ✅ | ✅ |
| GraphQL Support | ✅ | ❌ |
| WebSocket Testing | ✅ | ❌ |
| gRPC Support | ✅ | ❌ |
| AI-Powered Tests | ✅ | ❌ |
| Security Scanning | ✅ | ❌ |
| Compliance Checks | ✅ | ❌ |
| Visual Workflow Editor | ✅ | ❌ |
| Natural Language Tests | ✅ | ❌ |
| Price | Free (Open Source) | Free |

## Migration from Newman

Switching from Newman is easy:

```yaml
# Before (Newman)
- name: Run Newman
  run: |
    npm install -g newman
    newman run collection.json -e environment.json --reporters cli,json

# After (API Orchestrator)
- name: Run API Orchestrator
  uses: ChinmayShrivastava/api-orchestrator@v1
  with:
    collection: './collection.json'
    environment: './environment.json'
    reporters: 'cli,json'
```

## Support

- **Documentation**: [https://api-orchestrator.dev/docs](https://api-orchestrator.dev/docs)
- **Issues**: [GitHub Issues](https://github.com/ChinmayShrivastava/api-orchestrator/issues)
- **Discord**: [Join our community](https://discord.gg/api-orchestrator)

## License

MIT License - see [LICENSE](LICENSE) for details

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

---

**API Orchestrator** - The AI-Powered API Testing Platform
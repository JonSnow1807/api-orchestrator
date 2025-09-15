# CI/CD Integration Guide

Complete guide for integrating API Orchestrator into your CI/CD pipelines.

## Table of Contents

1. [GitHub Actions](#github-actions)
2. [GitLab CI](#gitlab-ci)
3. [Jenkins](#jenkins)
4. [CircleCI](#circleci)
5. [Azure DevOps](#azure-devops)
6. [Bitbucket Pipelines](#bitbucket-pipelines)
7. [Travis CI](#travis-ci)
8. [Docker Integration](#docker-integration)
9. [CLI Usage](#cli-usage)
10. [Best Practices](#best-practices)

## GitHub Actions

### Quick Start

```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ChinmayShrivastava/api-orchestrator@v1
        with:
          collection: './tests/api-tests.json'
          environment: 'production'
```

### Matrix Testing

```yaml
name: Multi-Environment Tests
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, staging, prod]
        region: [us-east-1, eu-west-1, ap-south-1]
    steps:
      - uses: actions/checkout@v3
      - uses: ChinmayShrivastava/api-orchestrator@v1
        with:
          collection: './tests/api-tests.json'
          environment: '${{ matrix.environment }}-${{ matrix.region }}'
```

### Scheduled Testing

```yaml
name: Hourly Health Check
on:
  schedule:
    - cron: '0 * * * *'  # Every hour

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ChinmayShrivastava/api-orchestrator@v1
        with:
          collection: './tests/health-checks.json'
          fail-on-error: 'true'
```

## GitLab CI

### Basic Configuration

```yaml
# .gitlab-ci.yml
stages:
  - test
  - deploy

api-tests:
  stage: test
  image: chinmayshrivastava/api-orchestrator:latest
  script:
    - api-orchestrator test ./tests/collection.json --environment production
  artifacts:
    reports:
      junit: test-results.xml
    paths:
      - test-results.json
      - test-report.html
```

### Parallel Testing

```yaml
api-tests:
  stage: test
  parallel:
    matrix:
      - ENVIRONMENT: [dev, staging, prod]
        REGION: [us, eu, asia]
  script:
    - api-orchestrator test ./tests/collection.json --environment ${ENVIRONMENT}-${REGION}
```

## Jenkins

### Pipeline Script

```groovy
pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('API Tests') {
            steps {
                sh '''
                    docker run --rm \
                        -v ${WORKSPACE}:/workspace \
                        chinmayshrivastava/api-orchestrator:latest \
                        test /workspace/tests/collection.json \
                        --environment production \
                        --reporters json,junit
                '''
            }
        }
        
        stage('Publish Results') {
            steps {
                junit 'test-results.xml'
                publishHTML([
                    reportDir: '.',
                    reportFiles: 'test-report.html',
                    reportName: 'API Test Report'
                ])
            }
        }
    }
    
    post {
        failure {
            emailext (
                subject: "API Tests Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "API tests failed. Check the report at ${env.BUILD_URL}",
                to: 'team@example.com'
            )
        }
    }
}
```

### Declarative Pipeline

```groovy
@Library('api-orchestrator') _

pipeline {
    agent any
    
    environment {
        API_KEY = credentials('api-orchestrator-key')
    }
    
    stages {
        stage('Test') {
            steps {
                apiOrchestratorTest(
                    collection: 'tests/api.json',
                    environment: 'staging',
                    reporters: ['json', 'junit', 'html']
                )
            }
        }
    }
}
```

## CircleCI

### Configuration

```yaml
# .circleci/config.yml
version: 2.1

orbs:
  api-orchestrator: chinmayshrivastava/api-orchestrator@1.0.0

jobs:
  api-test:
    docker:
      - image: cimg/base:stable
    steps:
      - checkout
      - api-orchestrator/test:
          collection: './tests/collection.json'
          environment: 'production'
      - store_test_results:
          path: test-results
      - store_artifacts:
          path: test-report.html

workflows:
  test-and-deploy:
    jobs:
      - api-test
      - deploy:
          requires:
            - api-test
          filters:
            branches:
              only: main
```

## Azure DevOps

### Pipeline YAML

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Test
    jobs:
      - job: APITests
        steps:
          - checkout: self
          
          - task: Docker@2
            inputs:
              command: 'run'
              arguments: |
                --rm
                -v $(Build.SourcesDirectory):/workspace
                chinmayshrivastava/api-orchestrator:latest
                test /workspace/tests/collection.json
                --reporters junit,html
          
          - task: PublishTestResults@2
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: '**/test-results.xml'
              
          - task: PublishHtmlReport@1
            inputs:
              reportDir: '$(Build.SourcesDirectory)'
              tabName: 'API Tests'
```

## Bitbucket Pipelines

### Configuration

```yaml
# bitbucket-pipelines.yml
image: chinmayshrivastava/api-orchestrator:latest

pipelines:
  default:
    - step:
        name: API Tests
        script:
          - api-orchestrator test ./tests/collection.json --environment production
        artifacts:
          - test-results.json
          - test-report.html
          
  branches:
    main:
      - step:
          name: Production Tests
          script:
            - api-orchestrator test ./tests/production.json
          after-script:
            - if [ $BITBUCKET_EXIT_CODE -ne 0 ]; then
                curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
                  -H 'Content-Type: application/json'
                  -d '{"text":"API tests failed in production!"}';
              fi
```

## Travis CI

### Configuration

```yaml
# .travis.yml
language: minimal
services:
  - docker

script:
  - docker run --rm -v $TRAVIS_BUILD_DIR:/workspace chinmayshrivastava/api-orchestrator:latest test /workspace/tests/collection.json

after_success:
  - bash <(curl -s https://codecov.io/bash) -f test-coverage.json

notifications:
  slack:
    secure: YOUR_ENCRYPTED_SLACK_TOKEN
    on_success: change
    on_failure: always
```

## Docker Integration

### Dockerfile for Testing

```dockerfile
FROM chinmayshrivastava/api-orchestrator:latest

WORKDIR /tests

COPY tests/ /tests/
COPY environments/ /environments/

ENTRYPOINT ["api-orchestrator", "test"]
CMD ["collection.json", "--environment", "production"]
```

### Docker Compose

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/test
    depends_on:
      - db
      
  db:
    image: postgres:14
    environment:
      - POSTGRES_PASSWORD=pass
      - POSTGRES_USER=user
      - POSTGRES_DB=test
      
  tests:
    image: chinmayshrivastava/api-orchestrator:latest
    depends_on:
      - api
    volumes:
      - ./tests:/tests
    command: test /tests/collection.json --environment docker
    environment:
      - API_BASE_URL=http://api:8000
```

## CLI Usage

### Installation

```bash
# Via pip
pip install api-orchestrator

# Via npm
npm install -g @api-orchestrator/cli

# Via Docker
docker pull chinmayshrivastava/api-orchestrator:latest
```

### Basic Commands

```bash
# Run tests
api-orchestrator test collection.json --environment production

# Run with specific reporters
api-orchestrator test collection.json --reporters json,junit,html

# Run specific folder
api-orchestrator test collection.json --folder "User Management"

# Run with data file
api-orchestrator test collection.json --data users.csv

# Parallel execution
api-orchestrator batch collection1.json collection2.json --parallel

# Performance regression
api-orchestrator regression collection.json --compare baseline.json --threshold 10

# Monitor endpoints
api-orchestrator monitor https://api.example.com/health --watch --interval 60

# Generate SDK
api-orchestrator codegen openapi.yaml --language python --output ./sdk
```

### Environment Variables

```bash
export API_ORCHESTRATOR_URL=https://api-orchestrator.dev
export API_ORCHESTRATOR_KEY=your-api-key
export API_ORCHESTRATOR_ENVIRONMENT=production
```

## Best Practices

### 1. Test Organization

```
tests/
├── smoke/           # Quick health checks
├── integration/     # API integration tests
├── performance/     # Load and stress tests
├── security/        # Security scans
└── regression/      # Regression test suites
```

### 2. Environment Management

```json
// environments/base.json
{
  "name": "base",
  "values": [
    {
      "key": "api_version",
      "value": "v1",
      "type": "default"
    }
  ]
}

// environments/production.json
{
  "name": "production",
  "extends": "base",
  "values": [
    {
      "key": "base_url",
      "value": "https://api.production.com",
      "type": "default"
    },
    {
      "key": "api_key",
      "value": "{{vault:production/api_key}}",
      "type": "secret"
    }
  ]
}
```

### 3. Failure Handling

```yaml
# Retry failed tests
- name: Run Tests with Retry
  uses: ChinmayShrivastava/api-orchestrator@v1
  with:
    collection: './tests/api-tests.json'
    max-retries: 3
    retry-delay: 5000
```

### 4. Performance Baselines

```bash
# Create baseline
api-orchestrator test perf.json --export-json baseline.json

# Check regression
api-orchestrator regression perf.json --compare baseline.json --threshold 10
```

### 5. Security Scanning

```yaml
# Regular security scans
- name: Security Scan
  uses: ChinmayShrivastava/api-orchestrator@v1
  with:
    collection: './tests/security-scan.json'
    api-key: ${{ secrets.API_ORCHESTRATOR_KEY }}
  continue-on-error: false
```

### 6. Notifications

```javascript
// webhook-handler.js
const results = require('./test-results.json');

if (results.failed > 0) {
  // Send to Slack
  await fetch(process.env.SLACK_WEBHOOK, {
    method: 'POST',
    body: JSON.stringify({
      text: `API Tests Failed: ${results.failed}/${results.total}`,
      attachments: [{
        color: 'danger',
        fields: results.failures.map(f => ({
          title: f.test,
          value: f.error,
          short: false
        }))
      }]
    })
  });
}
```

### 7. Custom Reporters

```python
# custom_reporter.py
import json
from api_orchestrator import Reporter

class CustomReporter(Reporter):
    def generate(self, results):
        # Custom report generation
        summary = {
            'timestamp': results['timestamp'],
            'pass_rate': results['passed'] / results['total'] * 100,
            'critical_failures': [
                t for t in results['tests'] 
                if t['status'] == 'failed' and t['critical']
            ]
        }
        
        with open('custom-report.json', 'w') as f:
            json.dump(summary, f, indent=2)
```

## Migration Guides

### From Newman

```bash
# Newman command
newman run collection.json -e environment.json --reporters cli,json

# API Orchestrator equivalent
api-orchestrator test collection.json --environment environment.json --reporters cli,json
```

### From Postman Cloud

1. Export collections from Postman
2. Import into API Orchestrator
3. Update CI/CD pipelines
4. Migrate environment variables
5. Update team permissions

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   ```bash
   export API_ORCHESTRATOR_KEY=your-key
   api-orchestrator test collection.json
   ```

2. **Network Issues**
   ```bash
   api-orchestrator test collection.json --proxy http://proxy:8080
   ```

3. **Certificate Errors**
   ```bash
   api-orchestrator test collection.json --insecure
   ```

4. **Timeout Issues**
   ```bash
   api-orchestrator test collection.json --timeout 60000
   ```

## Support

- Documentation: https://api-orchestrator.dev/docs
- GitHub: https://github.com/ChinmayShrivastava/api-orchestrator
- Discord: https://discord.gg/api-orchestrator
- Email: support@api-orchestrator.dev
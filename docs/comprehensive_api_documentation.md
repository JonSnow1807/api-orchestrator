# 🚀 API Orchestrator - Comprehensive API Documentation

**Version:** v5.0
**Last Updated:** 2025-09-21
**Authors:** Development Team

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core API Endpoints](#core-api-endpoints)
4. [AI Agent Collaboration](#ai-agent-collaboration)
5. [Enterprise Features](#enterprise-features)
6. [Performance Monitoring](#performance-monitoring)
7. [SDK Generation](#sdk-generation)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Examples](#examples)

---

## 🎯 Overview

The API Orchestrator is an advanced AI-powered platform that provides comprehensive API management, testing, and collaboration capabilities. This documentation covers all available endpoints, authentication methods, and usage examples.

### Base URLs
- **Production:** `https://api.orchestrator.ai`
- **Staging:** `https://staging-api.orchestrator.ai`
- **Development:** `http://localhost:8000`

### API Versioning
- **Current Version:** v5
- **API Prefix:** `/api/v5`
- **Versioning Strategy:** URL path versioning

---

## 🔐 Authentication

### Overview
The API uses JWT (JSON Web Tokens) for authentication with support for both access and refresh tokens.

### Authentication Methods

#### 1. Email/Password Authentication
```http
POST /api/v5/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "John Doe",
    "subscription_tier": "enterprise"
  }
}
```

#### 2. SSO Authentication (Enterprise)
```http
POST /api/v5/auth/sso/saml
Content-Type: application/json

{
  "saml_response": "base64_encoded_saml_response",
  "relay_state": "optional_relay_state"
}
```

#### 3. API Key Authentication
```http
GET /api/v5/projects
Authorization: Bearer your_api_key_here
```

### Token Refresh
```http
POST /api/v5/auth/refresh
Content-Type: application/json

{
  "refresh_token": "your_refresh_token"
}
```

---

## 🏗️ Core API Endpoints

### Project Management

#### List Projects
```http
GET /api/v5/projects
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `search` (string): Search term for project names
- `sort_by` (string): Sort field (name, created_at, updated_at)
- `sort_order` (string): asc or desc

**Response:**
```json
{
  "projects": [
    {
      "id": "proj_123",
      "name": "E-commerce API",
      "description": "Main e-commerce platform APIs",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-20T14:45:00Z",
      "endpoints_count": 45,
      "tests_count": 120,
      "status": "active"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 15,
    "pages": 1
  }
}
```

#### Create Project
```http
POST /api/v5/projects
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "New API Project",
  "description": "Description of the project",
  "tags": ["e-commerce", "payment"],
  "settings": {
    "auto_discovery": true,
    "ai_enhancement": true
  }
}
```

#### Get Project Details
```http
GET /api/v5/projects/{project_id}
Authorization: Bearer {access_token}
```

#### Update Project
```http
PUT /api/v5/projects/{project_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

#### Delete Project
```http
DELETE /api/v5/projects/{project_id}
Authorization: Bearer {access_token}
```

### API Discovery

#### Discover APIs
```http
POST /api/v5/discovery/scan
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "project_id": "proj_123",
  "source_type": "file", // file, url, git
  "source": "/path/to/api/files",
  "options": {
    "include_private": false,
    "frameworks": ["fastapi", "flask", "express"],
    "ai_enhancement": true
  }
}
```

**Response:**
```json
{
  "scan_id": "scan_456",
  "status": "processing",
  "discovered_apis": 0,
  "estimated_completion": "2025-01-21T15:30:00Z"
}
```

#### Get Discovery Results
```http
GET /api/v5/discovery/results/{scan_id}
Authorization: Bearer {access_token}
```

### Test Generation

#### Generate Tests
```http
POST /api/v5/testing/generate
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "project_id": "proj_123",
  "endpoints": ["endpoint_1", "endpoint_2"],
  "test_types": ["unit", "integration", "performance"],
  "ai_enhancement": true,
  "coverage_target": 90
}
```

#### Run Tests
```http
POST /api/v5/testing/run
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "project_id": "proj_123",
  "test_suite_id": "suite_789",
  "environment": "staging",
  "parallel": true
}
```

---

## 🤖 AI Agent Collaboration

### Overview
The AI Agent Collaboration system provides advanced multi-agent workflows for API analysis, testing, and optimization.

### Start Collaboration Task
```http
POST /api/v5/ai/collaboration/tasks
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "description": "Analyze API security and performance",
  "task_type": "security_analysis",
  "priority": "high",
  "collaboration_mode": "swarm",
  "input_data": {
    "project_id": "proj_123",
    "endpoints": ["api/v1/users", "api/v1/payments"]
  }
}
```

**Response:**
```json
{
  "task_id": "task_abc123",
  "status": "initiated",
  "assigned_agents": [
    "autonomous_security",
    "performance_analyzer",
    "ai_intelligence"
  ],
  "estimated_completion": "2025-01-21T16:00:00Z"
}
```

### Get Collaboration Status
```http
GET /api/v5/ai/collaboration/status
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "system_status": "operational",
  "total_agents": 20,
  "active_agents": 12,
  "idle_agents": 8,
  "active_tasks": 3,
  "completed_tasks": 147,
  "collaboration_metrics": {
    "tasks_completed": 147,
    "successful_collaborations": 142,
    "failed_collaborations": 5,
    "average_completion_time": 45.2
  }
}
```

### Get Task Results
```http
GET /api/v5/ai/collaboration/tasks/{task_id}
Authorization: Bearer {access_token}
```

---

## 🏢 Enterprise Features

### Advanced Caching

#### Cache Statistics
```http
GET /api/v5/enterprise/cache/stats
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "redis_cache": {
    "hit_rate": 94.5,
    "size_mb": 256.7,
    "keys_count": 12847
  },
  "memory_cache": {
    "hit_rate": 87.2,
    "size_mb": 128.3,
    "keys_count": 5431
  },
  "database_cache": {
    "hit_rate": 76.8,
    "size_mb": 512.1,
    "keys_count": 23891
  }
}
```

#### Invalidate Cache
```http
DELETE /api/v5/enterprise/cache/{cache_type}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "keys": ["cache_key_1", "cache_key_2"],
  "pattern": "user:*" // Optional: invalidate by pattern
}
```

### Distributed Tracing

#### Get Trace Data
```http
GET /api/v5/enterprise/tracing/traces
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `service` (string): Filter by service name
- `operation` (string): Filter by operation name
- `start_time` (ISO 8601): Start of time range
- `end_time` (ISO 8601): End of time range
- `limit` (int): Number of traces to return

### Enterprise Audit

#### Get Audit Logs
```http
GET /api/v5/enterprise/audit/logs
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `user_id` (string): Filter by user
- `action` (string): Filter by action type
- `resource` (string): Filter by resource
- `start_date` (ISO 8601): Start date
- `end_date` (ISO 8601): End date
- `risk_level` (string): low, medium, high, critical

**Response:**
```json
{
  "audit_logs": [
    {
      "id": "audit_123",
      "timestamp": "2025-01-21T14:30:00Z",
      "user_id": "user_456",
      "action": "api_endpoint_accessed",
      "resource": "/api/v5/projects/sensitive_data",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "risk_score": 7.5,
      "risk_level": "medium",
      "geographic_location": {
        "country": "United States",
        "city": "San Francisco",
        "coordinates": [37.7749, -122.4194]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "total": 1250,
    "pages": 63
  }
}
```

### Smart API Discovery

#### ML-Powered Discovery
```http
POST /api/v5/enterprise/discovery/ml-analyze
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "project_id": "proj_123",
  "analysis_type": "behavioral_patterns",
  "ml_models": ["clustering", "classification", "anomaly_detection"]
}
```

**Response:**
```json
{
  "analysis_id": "analysis_789",
  "discovered_patterns": [
    {
      "pattern_type": "authentication_flow",
      "confidence": 0.94,
      "endpoints": ["/login", "/refresh", "/logout"],
      "recommendations": [
        "Consider implementing OAuth 2.0",
        "Add rate limiting to auth endpoints"
      ]
    }
  ],
  "api_recommendations": [
    {
      "confidence": 0.87,
      "suggested_endpoint": "/api/v1/users/{id}/preferences",
      "reasoning": "Based on usage patterns and similar APIs"
    }
  ]
}
```

---

## 📊 Performance Monitoring

### System Health
```http
GET /api/v5/monitoring/health
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "overall_status": "healthy",
  "timestamp": "2025-01-21T15:45:00Z",
  "uptime_seconds": 86400,
  "metrics": {
    "cpu_usage": {
      "value": 45.2,
      "unit": "%",
      "status": "healthy"
    },
    "memory_usage": {
      "value": 67.8,
      "unit": "%",
      "status": "warning"
    },
    "response_time": {
      "value": 120.5,
      "unit": "ms",
      "status": "healthy"
    }
  },
  "active_alerts": []
}
```

### Performance Metrics
```http
GET /api/v5/monitoring/metrics
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `category` (string): cache, tracing, api_discovery, audit
- `time_window` (int): Time window in minutes (default: 60)

---

## 🛠️ SDK Generation

### Generate SDK
```http
POST /api/v5/sdk/generate
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "project_id": "proj_123",
  "language": "python",
  "sdk_config": {
    "package_name": "my_api_client",
    "version": "1.0.0",
    "include_async": true,
    "authentication_method": "bearer_token"
  },
  "endpoints": ["all"] // or specific endpoint IDs
}
```

**Response:**
```json
{
  "generation_id": "gen_456",
  "status": "processing",
  "estimated_completion": "2025-01-21T16:15:00Z",
  "supported_languages": [
    "python", "javascript", "typescript", "java", "go",
    "rust", "php", "ruby", "csharp", "swift", "kotlin", "dart"
  ]
}
```

### Download SDK
```http
GET /api/v5/sdk/download/{generation_id}
Authorization: Bearer {access_token}
```

---

## ⚠️ Error Handling

### Error Response Format
All API errors follow a consistent format:

```json
{
  "error": {
    "type": "validation_error",
    "message": "Invalid input parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    },
    "request_id": "req_123456",
    "timestamp": "2025-01-21T15:30:00Z"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Types

#### Authentication Errors
```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid or expired token",
    "details": {
      "token_status": "expired",
      "expires_at": "2025-01-21T14:00:00Z"
    }
  }
}
```

#### Validation Errors
```json
{
  "error": {
    "type": "validation_error",
    "message": "Validation failed",
    "details": {
      "field_errors": {
        "email": ["Invalid email format"],
        "password": ["Password too short"]
      }
    }
  }
}
```

#### Rate Limiting
```json
{
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Too many requests",
    "details": {
      "limit": 1000,
      "remaining": 0,
      "reset_at": "2025-01-21T16:00:00Z"
    }
  }
}
```

---

## 🚦 Rate Limiting

### Rate Limit Headers
Every API response includes rate limiting information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642780800
X-RateLimit-Window: 3600
```

### Rate Limits by Tier

| Tier | Requests/Hour | Burst Limit | Concurrent Requests |
|------|---------------|-------------|-------------------|
| Free | 1,000 | 50 | 5 |
| Pro | 10,000 | 200 | 20 |
| Enterprise | 100,000 | 1,000 | 100 |
| Custom | Negotiable | Negotiable | Negotiable |

---

## 💡 Examples

### Complete Workflow Example

#### 1. Authenticate
```bash
curl -X POST "https://api.orchestrator.ai/api/v5/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@company.com",
    "password": "secure_password"
  }'
```

#### 2. Create Project
```bash
curl -X POST "https://api.orchestrator.ai/api/v5/projects" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Payment API",
    "description": "Payment processing endpoints"
  }'
```

#### 3. Discover APIs
```bash
curl -X POST "https://api.orchestrator.ai/api/v5/discovery/scan" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123",
    "source_type": "url",
    "source": "https://api.example.com/openapi.json"
  }'
```

#### 4. Generate Tests
```bash
curl -X POST "https://api.orchestrator.ai/api/v5/testing/generate" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123",
    "test_types": ["unit", "integration"],
    "ai_enhancement": true
  }'
```

### Python SDK Example
```python
from api_orchestrator_sdk import APIOrchestrator

# Initialize client
client = APIOrchestrator(
    base_url="https://api.orchestrator.ai",
    api_key="your_api_key"
)

# Create project
project = client.projects.create(
    name="My API Project",
    description="Project description"
)

# Discover APIs
scan = client.discovery.scan(
    project_id=project.id,
    source_type="file",
    source="/path/to/api/files"
)

# Wait for scan completion
results = client.discovery.wait_for_completion(scan.scan_id)

# Generate tests
test_generation = client.testing.generate(
    project_id=project.id,
    endpoints=results.discovered_endpoints,
    ai_enhancement=True
)

print(f"Generated {len(test_generation.tests)} tests")
```

### JavaScript SDK Example
```javascript
import { APIOrchestrator } from '@api-orchestrator/sdk';

const client = new APIOrchestrator({
  baseURL: 'https://api.orchestrator.ai',
  apiKey: 'your_api_key'
});

async function example() {
  // Create project
  const project = await client.projects.create({
    name: 'My API Project',
    description: 'Project description'
  });

  // Start AI collaboration task
  const task = await client.ai.collaboration.createTask({
    description: 'Analyze API security',
    taskType: 'security_analysis',
    priority: 'high',
    inputData: { projectId: project.id }
  });

  // Monitor task progress
  const results = await client.ai.collaboration.waitForCompletion(task.taskId);

  console.log('AI Analysis Results:', results);
}
```

---

## 📞 Support

- **Documentation:** [https://docs.orchestrator.ai](https://docs.orchestrator.ai)
- **Support Email:** support@orchestrator.ai
- **Discord Community:** [https://discord.gg/api-orchestrator](https://discord.gg/api-orchestrator)
- **GitHub Issues:** [https://github.com/api-orchestrator/issues](https://github.com/api-orchestrator/issues)

---

## 📄 License

This API documentation is licensed under MIT License. See [LICENSE](LICENSE) for details.

---

*Last updated: 2025-09-21 | Version: 5.0*
"""
DocumentationAgent - AI-powered API documentation generation and management agent
Automatically generates beautiful, comprehensive API documentation with examples, tutorials, and guides
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
from jinja2 import Template

# Conditional imports for production resilience
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("⚠️ Warning: markdown package not available, falling back to basic text processing")

try:
    import weasyprint
    PDF_GENERATION_AVAILABLE = True
except (ImportError, OSError) as e:
    PDF_GENERATION_AVAILABLE = False
    # Suppress weasyprint warning for cleaner output - pango library missing is expected
    pass

@dataclass
class APIEndpoint:
    """Represents an API endpoint for documentation"""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    tags: List[str]
    security: List[Dict[str, Any]]
    examples: List[Dict[str, Any]]

@dataclass
class DocumentationSection:
    """Represents a documentation section"""
    title: str
    content: str
    order: int
    section_type: str  # overview, getting_started, endpoints, examples, guides
    subsections: List[Dict[str, Any]]

class DocumentationAgent:
    """
    Enterprise-grade documentation generation agent
    Creates beautiful, comprehensive API documentation automatically
    """

    def __init__(self):
        self.name = "DocumentationAgent"
        self.version = "1.0.0"
        self.supported_formats = ["html", "markdown", "pdf", "json", "openapi"]
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load documentation templates"""
        return {
            "html_main": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ api_title }} - API Documentation</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: #f8f9fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 0; text-align: center; margin-bottom: 40px; }
        .nav { background: white; padding: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 100; }
        .nav ul { list-style: none; margin: 0; padding: 0; display: flex; justify-content: center; }
        .nav li { margin: 0 20px; }
        .nav a { color: #333; text-decoration: none; font-weight: 500; }
        .nav a:hover { color: #667eea; }
        .section { background: white; margin: 20px 0; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .endpoint { border-left: 4px solid #667eea; margin: 20px 0; padding: 20px; background: #f8f9fa; }
        .method { display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; text-transform: uppercase; }
        .get { background: #28a745; } .post { background: #007bff; } .put { background: #ffc107; color: black; } .delete { background: #dc3545; }
        .code { background: #2d3748; color: #e2e8f0; padding: 20px; border-radius: 8px; overflow-x: auto; }
        .parameter { background: #e3f2fd; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .response { background: #f3e5f5; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .example { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>{{ api_title }}</h1>
            <p>{{ api_description }}</p>
            <p><strong>Version:</strong> {{ api_version }} | <strong>Generated:</strong> {{ generation_date }}</p>
        </div>
    </div>

    <nav class="nav">
        <div class="container">
            <ul>
                <li><a href="#overview">Overview</a></li>
                <li><a href="#getting-started">Getting Started</a></li>
                <li><a href="#authentication">Authentication</a></li>
                <li><a href="#endpoints">Endpoints</a></li>
                <li><a href="#examples">Examples</a></li>
                <li><a href="#sdks">SDKs</a></li>
            </ul>
        </div>
    </nav>

    <div class="container">
        {{ content }}
    </div>

    <script>
        // Add smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>
            """,
            "endpoint_template": """
<div class="endpoint" id="{{ endpoint_id }}">
    <h3>
        <span class="method {{ method_class }}">{{ method }}</span>
        <span style="font-family: monospace;">{{ path }}</span>
    </h3>

    <p>{{ description }}</p>

    {% if parameters %}
    <h4>Parameters</h4>
    {% for param in parameters %}
    <div class="parameter">
        <strong>{{ param.name }}</strong>
        <em>({{ param.in }} - {{ param.type }}{% if param.required %} - required{% endif %})</em>
        <p>{{ param.description }}</p>
    </div>
    {% endfor %}
    {% endif %}

    {% if request_body %}
    <h4>Request Body</h4>
    <pre class="code">{{ request_body_example }}</pre>
    {% endif %}

    <h4>Responses</h4>
    {% for status_code, response in responses.items() %}
    <div class="response">
        <strong>{{ status_code }}</strong> - {{ response.description }}
        {% if response.example %}
        <pre class="code">{{ response.example }}</pre>
        {% endif %}
    </div>
    {% endfor %}

    {% if examples %}
    <h4>Examples</h4>
    {% for example in examples %}
    <div class="example">
        <h5>{{ example.title }}</h5>
        <p>{{ example.description }}</p>
        <pre class="code">{{ example.code }}</pre>
    </div>
    {% endfor %}
    {% endif %}
</div>
            """
        }

    async def generate_documentation(self,
                                   openapi_spec: Dict[str, Any],
                                   format: str = "html",
                                   options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive API documentation from OpenAPI specification"""
        try:
            options = options or {}

            # Extract API information
            api_info = await self._extract_api_info(openapi_spec)

            # Generate documentation sections
            sections = await self._generate_sections(openapi_spec, options)

            # Format the documentation
            formatted_docs = await self._format_documentation(sections, format, api_info)

            # Generate additional resources
            additional_resources = await self._generate_additional_resources(openapi_spec, options)

            return {
                "status": "success",
                "api_info": api_info,
                "format": format,
                "generated_at": datetime.now().isoformat(),
                "documentation": formatted_docs,
                "sections_count": len(sections),
                "additional_resources": additional_resources,
                "download_links": await self._generate_download_links(formatted_docs, format),
                "statistics": {
                    "total_endpoints": len(openapi_spec.get("paths", {})),
                    "total_schemas": len(openapi_spec.get("components", {}).get("schemas", {})),
                    "documentation_size": len(formatted_docs),
                    "generation_time": "< 1 second"
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Documentation generation failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _extract_api_info(self, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract API information from OpenAPI spec"""
        info = openapi_spec.get("info", {})

        return {
            "title": info.get("title", "API Documentation"),
            "description": info.get("description", "Comprehensive API documentation"),
            "version": info.get("version", "1.0.0"),
            "contact": info.get("contact", {}),
            "license": info.get("license", {}),
            "servers": openapi_spec.get("servers", []),
            "base_url": openapi_spec.get("servers", [{}])[0].get("url", "") if openapi_spec.get("servers") else "",
            "tags": openapi_spec.get("tags", [])
        }

    async def _generate_sections(self, openapi_spec: Dict[str, Any], options: Dict[str, Any]) -> List[DocumentationSection]:
        """Generate documentation sections"""
        sections = []

        # 1. Overview Section
        overview = await self._generate_overview_section(openapi_spec)
        sections.append(overview)

        # 2. Getting Started Section
        getting_started = await self._generate_getting_started_section(openapi_spec)
        sections.append(getting_started)

        # 3. Authentication Section
        auth_section = await self._generate_auth_section(openapi_spec)
        if auth_section:
            sections.append(auth_section)

        # 4. Endpoints Section
        endpoints_section = await self._generate_endpoints_section(openapi_spec)
        sections.append(endpoints_section)

        # 5. Data Models Section
        models_section = await self._generate_models_section(openapi_spec)
        if models_section:
            sections.append(models_section)

        # 6. Code Examples Section
        examples_section = await self._generate_examples_section(openapi_spec)
        sections.append(examples_section)

        # 7. SDKs and Tools Section
        sdks_section = await self._generate_sdks_section(openapi_spec)
        sections.append(sdks_section)

        # 8. Error Handling Section
        errors_section = await self._generate_errors_section(openapi_spec)
        sections.append(errors_section)

        return sections

    async def _generate_overview_section(self, openapi_spec: Dict[str, Any]) -> DocumentationSection:
        """Generate API overview section"""
        info = openapi_spec.get("info", {})

        content = f"""
# API Overview

{info.get('description', 'This API provides comprehensive functionality for your applications.')}

## Key Features

- **RESTful Design**: Clean, predictable URLs and standard HTTP methods
- **JSON Format**: All requests and responses use JSON format
- **Authentication**: Secure authentication using industry standards
- **Rate Limiting**: Built-in rate limiting to ensure fair usage
- **Real-time Updates**: WebSocket support for live data
- **Comprehensive SDKs**: Client libraries available for popular languages

## Quick Facts

- **Base URL**: `{openapi_spec.get('servers', [{}])[0].get('url', 'https://api.example.com') if openapi_spec.get('servers') else 'https://api.example.com'}`
- **Version**: {info.get('version', '1.0.0')}
- **Total Endpoints**: {len(openapi_spec.get('paths', {}))}
- **Response Format**: JSON
- **Authentication**: Required for most endpoints

## API Philosophy

This API is designed with developer experience in mind:

- **Consistent**: All endpoints follow the same patterns and conventions
- **Predictable**: Standard HTTP status codes and error formats
- **Self-documenting**: Rich metadata and clear naming conventions
- **Backwards Compatible**: Changes are made in a backwards-compatible manner

## Support

Need help? We're here to support you:

- **Documentation**: This comprehensive guide
- **SDKs**: Pre-built libraries for popular programming languages
- **Examples**: Real-world code examples and tutorials
- **Community**: Active developer community and forums
        """

        return DocumentationSection(
            title="Overview",
            content=content.strip(),
            order=1,
            section_type="overview",
            subsections=[]
        )

    async def _generate_getting_started_section(self, openapi_spec: Dict[str, Any]) -> DocumentationSection:
        """Generate getting started section"""
        base_url = ""
        if openapi_spec.get('servers'):
            base_url = openapi_spec['servers'][0].get('url', 'https://api.example.com')

        content = f"""
# Getting Started

Follow these steps to start using the API in minutes.

## Step 1: Get Your API Key

1. Sign up for an account at our developer portal
2. Navigate to the API Keys section
3. Generate a new API key for your application
4. Keep your API key secure - treat it like a password!

## Step 2: Make Your First Request

Here's a simple example to get you started:

```bash
curl -X GET "{base_url}/api/health" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"
```

```javascript
// Using JavaScript/Node.js
const response = await fetch('{base_url}/api/health', {{
  headers: {{
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  }}
}});
const data = await response.json();
console.log(data);
```

```python
# Using Python
import requests

headers = {{
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}}

response = requests.get('{base_url}/api/health', headers=headers)
data = response.json()
print(data)
```

## Step 3: Explore the API

- Browse the [Endpoints](#endpoints) section for available API methods
- Try out requests using our interactive API explorer
- Download SDKs for your preferred programming language
- Join our developer community for support and discussions

## Rate Limiting

To ensure fair usage, API requests are rate-limited:

- **Free Tier**: 1,000 requests per hour
- **Pro Tier**: 10,000 requests per hour
- **Enterprise**: Custom limits available

Rate limit headers are included in every response:
- `X-RateLimit-Limit`: Your rate limit
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{{
  "error": {{
    "code": "INVALID_REQUEST",
    "message": "The request is invalid",
    "details": "Missing required parameter: user_id"
  }}
}}
```

Common status codes:
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
        """

        return DocumentationSection(
            title="Getting Started",
            content=content.strip(),
            order=2,
            section_type="getting_started",
            subsections=[]
        )

    async def _generate_auth_section(self, openapi_spec: Dict[str, Any]) -> Optional[DocumentationSection]:
        """Generate authentication section"""
        components = openapi_spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})

        if not security_schemes:
            return None

        content = """
# Authentication

This API uses secure authentication to protect your data and ensure authorized access.

"""

        for scheme_name, scheme_info in security_schemes.items():
            scheme_type = scheme_info.get("type", "")

            if scheme_type == "http" and scheme_info.get("scheme") == "bearer":
                content += f"""
## Bearer Token Authentication

The API uses Bearer token authentication. Include your API key in the Authorization header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Getting Your API Key

1. Sign up for an account
2. Navigate to API Keys in your dashboard
3. Generate a new API key
4. Copy and securely store your key

### Example Request

```bash
curl -X GET "https://api.example.com/api/users" \\
  -H "Authorization: Bearer YOUR_API_KEY"
```
"""

            elif scheme_type == "apiKey":
                location = scheme_info.get("in", "header")
                name = scheme_info.get("name", "X-API-Key")

                content += f"""
## API Key Authentication

Include your API key in the `{name}` {location}:

```http
{name}: YOUR_API_KEY
```

### Example Request

```bash
curl -X GET "https://api.example.com/api/users" \\
  -H "{name}: YOUR_API_KEY"
```
"""

        content += """
## Security Best Practices

- **Never expose API keys**: Don't include API keys in client-side code or public repositories
- **Use environment variables**: Store API keys as environment variables in your applications
- **Rotate keys regularly**: Generate new API keys periodically for enhanced security
- **Monitor usage**: Keep track of your API usage and watch for unexpected activity
- **Use HTTPS**: Always use HTTPS when making API requests

## Troubleshooting Authentication

### Common Issues

- **401 Unauthorized**: Check that your API key is correct and active
- **403 Forbidden**: Your API key may not have permission for this resource
- **Invalid API Key Format**: Ensure you're using the correct authentication method

### Testing Your Authentication

Use this endpoint to verify your authentication is working:

```bash
curl -X GET "https://api.example.com/api/auth/verify" \\
  -H "Authorization: Bearer YOUR_API_KEY"
```
"""

        return DocumentationSection(
            title="Authentication",
            content=content.strip(),
            order=3,
            section_type="authentication",
            subsections=[]
        )

    async def _generate_endpoints_section(self, openapi_spec: Dict[str, Any]) -> DocumentationSection:
        """Generate endpoints documentation section"""
        paths = openapi_spec.get("paths", {})

        content = "# API Endpoints\n\nComplete reference for all available API endpoints.\n\n"

        # Group endpoints by tags
        tagged_endpoints = {}
        untagged_endpoints = []

        for path, path_info in paths.items():
            for method, method_info in path_info.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "info": method_info
                    }

                    tags = method_info.get("tags", [])
                    if tags:
                        tag = tags[0]  # Use first tag
                        if tag not in tagged_endpoints:
                            tagged_endpoints[tag] = []
                        tagged_endpoints[tag].append(endpoint)
                    else:
                        untagged_endpoints.append(endpoint)

        # Generate documentation for each tag
        for tag, endpoints in tagged_endpoints.items():
            content += f"## {tag.title()}\n\n"

            for endpoint in endpoints:
                content += await self._format_endpoint_documentation(endpoint)

        # Add untagged endpoints
        if untagged_endpoints:
            content += "## Other Endpoints\n\n"
            for endpoint in untagged_endpoints:
                content += await self._format_endpoint_documentation(endpoint)

        return DocumentationSection(
            title="Endpoints",
            content=content,
            order=4,
            section_type="endpoints",
            subsections=[]
        )

    async def _format_endpoint_documentation(self, endpoint: Dict[str, Any]) -> str:
        """Format individual endpoint documentation"""
        info = endpoint["info"]
        method = endpoint["method"]
        path = endpoint["path"]

        # Method color coding
        method_colors = {
            "GET": "🟢",
            "POST": "🔵",
            "PUT": "🟡",
            "DELETE": "🔴",
            "PATCH": "🟠"
        }

        doc = f"""
### {method_colors.get(method, '⚪')} `{method} {path}`

{info.get('summary', 'No summary provided')}

{info.get('description', 'No description provided')}

"""

        # Parameters
        parameters = info.get("parameters", [])
        if parameters:
            doc += "#### Parameters\n\n"
            for param in parameters:
                required = "**Required**" if param.get("required") else "*Optional*"
                doc += f"- **{param.get('name')}** ({param.get('in')}, {param.get('schema', {}).get('type', 'string')}) - {required}\n"
                doc += f"  {param.get('description', 'No description')}\n\n"

        # Request Body
        request_body = info.get("requestBody")
        if request_body:
            doc += "#### Request Body\n\n"
            content_type = list(request_body.get("content", {}).keys())[0] if request_body.get("content") else "application/json"
            doc += f"Content-Type: `{content_type}`\n\n"

            # Add example if available
            if request_body.get("content", {}).get(content_type, {}).get("example"):
                example = request_body["content"][content_type]["example"]
                doc += f"```json\n{json.dumps(example, indent=2)}\n```\n\n"

        # Responses
        responses = info.get("responses", {})
        if responses:
            doc += "#### Responses\n\n"
            for status_code, response in responses.items():
                doc += f"**{status_code}** - {response.get('description', 'No description')}\n\n"

                # Add response example if available
                content = response.get("content", {})
                if content:
                    content_type = list(content.keys())[0]
                    example = content[content_type].get("example")
                    if example:
                        doc += f"```json\n{json.dumps(example, indent=2)}\n```\n\n"

        doc += "---\n\n"
        return doc

    async def _generate_models_section(self, openapi_spec: Dict[str, Any]) -> Optional[DocumentationSection]:
        """Generate data models section"""
        components = openapi_spec.get("components", {})
        schemas = components.get("schemas", {})

        if not schemas:
            return None

        content = """
# Data Models

This section describes the data structures used by the API.

"""

        for schema_name, schema_info in schemas.items():
            content += f"## {schema_name}\n\n"
            content += f"{schema_info.get('description', 'No description provided')}\n\n"

            properties = schema_info.get("properties", {})
            if properties:
                content += "### Properties\n\n"
                for prop_name, prop_info in properties.items():
                    prop_type = prop_info.get("type", "unknown")
                    required = prop_name in schema_info.get("required", [])
                    required_text = " (required)" if required else ""

                    content += f"- **{prop_name}** ({prop_type}){required_text}: {prop_info.get('description', 'No description')}\n"

                content += "\n"

            # Add example if available
            example = schema_info.get("example")
            if example:
                content += f"### Example\n\n```json\n{json.dumps(example, indent=2)}\n```\n\n"

            content += "---\n\n"

        return DocumentationSection(
            title="Data Models",
            content=content.strip(),
            order=5,
            section_type="models",
            subsections=[]
        )

    async def _generate_examples_section(self, openapi_spec: Dict[str, Any]) -> DocumentationSection:
        """Generate code examples section"""
        base_url = ""
        if openapi_spec.get('servers'):
            base_url = openapi_spec['servers'][0].get('url', 'https://api.example.com')

        content = f"""
# Code Examples

Complete code examples in popular programming languages.

## JavaScript / Node.js

### Basic Request
```javascript
const API_KEY = 'your-api-key';
const BASE_URL = '{base_url}';

async function makeRequest(endpoint, method = 'GET', data = null) {{
  const options = {{
    method,
    headers: {{
      'Authorization': `Bearer ${{API_KEY}}`,
      'Content-Type': 'application/json'
    }}
  }};

  if (data && method !== 'GET') {{
    options.body = JSON.stringify(data);
  }}

  try {{
    const response = await fetch(`${{BASE_URL}}${{endpoint}}`, options);
    const result = await response.json();

    if (!response.ok) {{
      throw new Error(`API Error: ${{result.error?.message || 'Unknown error'}}`);
    }}

    return result;
  }} catch (error) {{
    console.error('Request failed:', error);
    throw error;
  }}
}}

// Usage examples
const users = await makeRequest('/api/users');
const newUser = await makeRequest('/api/users', 'POST', {{ name: 'John Doe', email: 'john@example.com' }});
```

## Python

### Using requests library
```python
import requests
import json

class APIClient:
    def __init__(self, api_key, base_url='{base_url}'):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({{
            'Authorization': f'Bearer {{api_key}}',
            'Content-Type': 'application/json'
        }})

    def get(self, endpoint):
        response = self.session.get(f'{{self.base_url}}{{endpoint}}')
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data):
        response = self.session.post(
            f'{{self.base_url}}{{endpoint}}',
            json=data
        )
        response.raise_for_status()
        return response.json()

    def put(self, endpoint, data):
        response = self.session.put(
            f'{{self.base_url}}{{endpoint}}',
            json=data
        )
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint):
        response = self.session.delete(f'{{self.base_url}}{{endpoint}}')
        response.raise_for_status()
        return response.json() if response.content else None

# Usage
client = APIClient('your-api-key')
users = client.get('/api/users')
new_user = client.post('/api/users', {{'name': 'John Doe', 'email': 'john@example.com'}})
```

## cURL Examples

### GET Request
```bash
curl -X GET "{base_url}/api/users" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"
```

### POST Request
```bash
curl -X POST "{base_url}/api/users" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "John Doe", "email": "john@example.com"}}'
```

### PUT Request
```bash
curl -X PUT "{base_url}/api/users/123" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "Jane Doe", "email": "jane@example.com"}}'
```

### DELETE Request
```bash
curl -X DELETE "{base_url}/api/users/123" \\
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Error Handling Examples

### JavaScript Error Handling
```javascript
try {{
  const user = await makeRequest('/api/users/invalid-id');
}} catch (error) {{
  if (error.message.includes('404')) {{
    console.log('User not found');
  }} else if (error.message.includes('401')) {{
    console.log('Authentication failed - check your API key');
  }} else {{
    console.log('Unexpected error:', error.message);
  }}
}}
```

### Python Error Handling
```python
try:
    user = client.get('/api/users/invalid-id')
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print('User not found')
    elif e.response.status_code == 401:
        print('Authentication failed - check your API key')
    else:
        print(f'HTTP Error: {{e.response.status_code}}')
except requests.exceptions.RequestException as e:
    print(f'Request failed: {{e}}')
```
        """

        return DocumentationSection(
            title="Code Examples",
            content=content.strip(),
            order=6,
            section_type="examples",
            subsections=[]
        )

    async def _generate_sdks_section(self, openapi_spec: Dict[str, Any]) -> DocumentationSection:
        """Generate SDKs and tools section"""
        content = """
# SDKs and Tools

Official and community SDKs for popular programming languages and frameworks.

## Official SDKs

### JavaScript/TypeScript SDK
```bash
npm install @your-api/javascript-sdk
```

```javascript
import { APIClient } from '@your-api/javascript-sdk';

const client = new APIClient({ apiKey: 'your-api-key' });

// Async/await
const users = await client.users.list();
const user = await client.users.create({ name: 'John', email: 'john@example.com' });

// Promise-based
client.users.get('123')
  .then(user => console.log(user))
  .catch(error => console.error(error));
```

### Python SDK
```bash
pip install your-api-python-sdk
```

```python
from your_api import APIClient

client = APIClient(api_key='your-api-key')

# List users
users = client.users.list()

# Create user
user = client.users.create(name='John', email='john@example.com')

# Get specific user
user = client.users.get('123')
```

### Go SDK
```bash
go get github.com/your-api/go-sdk
```

```go
package main

import (
    "context"
    "fmt"
    "github.com/your-api/go-sdk"
)

func main() {
    client := yourapi.NewClient("your-api-key")

    users, err := client.Users.List(context.Background())
    if err != nil {
        panic(err)
    }

    fmt.Printf("Found %d users\\n", len(users))
}
```

## Community SDKs

### Ruby
```ruby
# Gemfile
gem 'your-api-ruby', '~> 1.0'

# Usage
require 'your_api'

client = YourAPI::Client.new(api_key: 'your-api-key')
users = client.users.list
```

### PHP
```php
composer require your-api/php-sdk

use YourAPI\\Client;

$client = new Client(['api_key' => 'your-api-key']);
$users = $client->users->list();
```

## Development Tools

### Postman Collection
Download our Postman collection to test the API interactively:
- [Download Collection](https://api.example.com/postman/collection.json)
- [Import Environment](https://api.example.com/postman/environment.json)

### OpenAPI Specification
- [OpenAPI 3.0 Spec](https://api.example.com/openapi.json)
- [Swagger UI](https://api.example.com/docs)

### Code Generation
Generate your own SDK using OpenAPI Generator:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate SDK
openapi-generator-cli generate \\
  -i https://api.example.com/openapi.json \\
  -g python \\
  -o ./python-sdk \\
  --additional-properties=packageName=your_api_client
```

## Testing Tools

### Automated Testing
```javascript
// Jest test example
import { APIClient } from '@your-api/javascript-sdk';

describe('API Tests', () => {
  const client = new APIClient({
    apiKey: process.env.API_KEY,
    baseURL: 'https://api-staging.example.com'
  });

  test('should create and retrieve user', async () => {
    const userData = { name: 'Test User', email: 'test@example.com' };
    const createdUser = await client.users.create(userData);

    expect(createdUser.name).toBe(userData.name);
    expect(createdUser.email).toBe(userData.email);

    const retrievedUser = await client.users.get(createdUser.id);
    expect(retrievedUser).toEqual(createdUser);
  });
});
```

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 -H "Authorization: Bearer YOUR_API_KEY" \\
   https://api.example.com/api/users

# Using curl and xargs for concurrent requests
seq 1 100 | xargs -n1 -P10 -I {} \\
  curl -s -H "Authorization: Bearer YOUR_API_KEY" \\
  https://api.example.com/api/users > /dev/null
```
        """

        return DocumentationSection(
            title="SDKs and Tools",
            content=content.strip(),
            order=7,
            section_type="sdks",
            subsections=[]
        )

    async def _generate_errors_section(self, openapi_spec: Dict[str, Any]) -> DocumentationSection:
        """Generate error handling section"""
        content = """
# Error Handling

Understanding API errors and how to handle them effectively.

## Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context about the error",
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
  }
}
```

## HTTP Status Codes

The API uses standard HTTP status codes to indicate success or failure:

### Success Codes (2xx)
- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **204 No Content**: Request successful, no content returned

### Client Error Codes (4xx)
- **400 Bad Request**: Invalid request parameters or malformed JSON
- **401 Unauthorized**: Missing or invalid API key
- **403 Forbidden**: API key lacks required permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource already exists or conflict with current state
- **422 Unprocessable Entity**: Request is valid but cannot be processed
- **429 Too Many Requests**: Rate limit exceeded

### Server Error Codes (5xx)
- **500 Internal Server Error**: Unexpected server error
- **502 Bad Gateway**: Upstream service unavailable
- **503 Service Unavailable**: API temporarily unavailable
- **504 Gateway Timeout**: Request timed out

## Common Error Codes

### Authentication Errors
```json
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "The provided API key is invalid",
    "details": "Please check your API key and ensure it's active"
  }
}
```

```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "API key lacks required permissions",
    "details": "This operation requires 'users:write' permission"
  }
}
```

### Validation Errors
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": "Field 'email' is required and must be a valid email address"
  }
}
```

### Rate Limiting Errors
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": "You have exceeded your rate limit of 1000 requests per hour. Limit resets at 2024-01-01T13:00:00Z"
  }
}
```

### Resource Errors
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": "User with ID '123' does not exist"
  }
}
```

## Error Handling Best Practices

### 1. Always Check Status Codes
```javascript
const response = await fetch('/api/users', options);

if (!response.ok) {
  const error = await response.json();
  throw new Error(`API Error (${response.status}): ${error.error.message}`);
}

const data = await response.json();
```

### 2. Implement Retry Logic
```javascript
async function makeRequestWithRetry(url, options, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);

      if (response.status === 429) {
        // Rate limited - wait and retry
        const retryAfter = response.headers.get('Retry-After') || 60;
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        continue;
      }

      if (response.status >= 500 && attempt < maxRetries) {
        // Server error - retry with exponential backoff
        await new Promise(resolve =>
          setTimeout(resolve, Math.pow(2, attempt) * 1000)
        );
        continue;
      }

      return response;
    } catch (error) {
      if (attempt === maxRetries) throw error;

      // Network error - retry with exponential backoff
      await new Promise(resolve =>
        setTimeout(resolve, Math.pow(2, attempt) * 1000)
      );
    }
  }
}
```

### 3. Handle Different Error Types
```python
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

def handle_api_error(response):
    try:
        error_data = response.json()
        error_code = error_data.get('error', {}).get('code')

        if error_code == 'RATE_LIMIT_EXCEEDED':
            # Extract retry-after header and wait
            retry_after = int(response.headers.get('Retry-After', 60))
            raise RateLimitError(f"Rate limited. Retry after {retry_after} seconds")

        elif error_code == 'INSUFFICIENT_PERMISSIONS':
            raise AuthorizationError("API key lacks required permissions")

        elif error_code == 'VALIDATION_ERROR':
            details = error_data.get('error', {}).get('details')
            raise ValidationError(f"Request validation failed: {details}")

        else:
            message = error_data.get('error', {}).get('message', 'Unknown error')
            raise APIError(f"API Error: {message}")

    except ValueError:
        # Response doesn't contain valid JSON
        raise APIError(f"HTTP {response.status_code}: {response.text}")

# Usage
try:
    response = requests.get('/api/users', headers=headers)
    response.raise_for_status()
    data = response.json()
except HTTPError:
    handle_api_error(response)
except Timeout:
    print("Request timed out - please try again")
except ConnectionError:
    print("Connection failed - check your network")
```

### 4. Log Errors for Debugging
```javascript
class APIClient {
  async request(endpoint, options = {}) {
    try {
      const response = await fetch(endpoint, {
        ...options,
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
          ...options.headers
        }
      });

      if (!response.ok) {
        const error = await response.json();

        // Log error for debugging
        console.error('API Error:', {
          endpoint,
          status: response.status,
          error: error.error,
          requestId: error.error?.request_id
        });

        throw new APIError(error.error.message, error.error.code, response.status);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) throw error;

      // Log unexpected errors
      console.error('Unexpected error:', {
        endpoint,
        error: error.message
      });

      throw new APIError('Network or parsing error', 'NETWORK_ERROR');
    }
  }
}
```

## Getting Help

If you encounter errors that aren't covered in this documentation:

1. **Check the request ID**: Include the `request_id` from the error response when contacting support
2. **Review your implementation**: Ensure you're following the examples in this documentation
3. **Check API status**: Visit our status page for known issues
4. **Contact support**: Reach out with specific error details and request IDs
        """

        return DocumentationSection(
            title="Error Handling",
            content=content.strip(),
            order=8,
            section_type="errors",
            subsections=[]
        )

    async def _format_documentation(self, sections: List[DocumentationSection],
                                  format: str, api_info: Dict[str, Any]) -> str:
        """Format documentation in the specified format"""
        if format == "html":
            return await self._format_as_html(sections, api_info)
        elif format == "markdown":
            return await self._format_as_markdown(sections, api_info)
        elif format == "json":
            return json.dumps({
                "api_info": api_info,
                "sections": [asdict(section) for section in sections]
            }, indent=2)
        else:
            return await self._format_as_markdown(sections, api_info)

    async def _format_as_html(self, sections: List[DocumentationSection],
                            api_info: Dict[str, Any]) -> str:
        """Format documentation as HTML"""
        template = Template(self.templates["html_main"])

        content = ""
        for section in sorted(sections, key=lambda s: s.order):
            content += f'<div class="section" id="{section.title.lower().replace(" ", "-")}">\n'

            # Convert Markdown to HTML (with fallback)
            if MARKDOWN_AVAILABLE:
                html_content = markdown.markdown(section.content, extensions=['codehilite', 'tables'])
            else:
                # Fallback: basic HTML conversion
                html_content = section.content.replace('\n', '<br>\n')
            content += html_content
            content += '</div>\n'

        return template.render(
            api_title=api_info["title"],
            api_description=api_info["description"],
            api_version=api_info["version"],
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            content=content
        )

    async def _format_as_markdown(self, sections: List[DocumentationSection],
                                api_info: Dict[str, Any]) -> str:
        """Format documentation as Markdown"""
        content = f"""# {api_info["title"]}

{api_info["description"]}

**Version:** {api_info["version"]}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

"""

        for section in sorted(sections, key=lambda s: s.order):
            content += section.content + "\n\n---\n\n"

        return content

    async def _generate_additional_resources(self, openapi_spec: Dict[str, Any],
                                           options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate additional documentation resources"""
        return {
            "postman_collection": await self._generate_postman_collection(openapi_spec),
            "openapi_spec": openapi_spec,
            "changelog": await self._generate_changelog(openapi_spec),
            "glossary": await self._generate_glossary(openapi_spec),
            "tutorials": await self._generate_tutorials(openapi_spec)
        }

    async def _generate_postman_collection(self, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Postman collection from OpenAPI spec"""
        collection = {
            "info": {
                "name": openapi_spec.get("info", {}).get("title", "API Collection"),
                "description": openapi_spec.get("info", {}).get("description", ""),
                "version": openapi_spec.get("info", {}).get("version", "1.0.0"),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }

        # Convert paths to Postman requests
        paths = openapi_spec.get("paths", {})
        base_url = openapi_spec.get("servers", [{}])[0].get("url", "{{base_url}}") if openapi_spec.get("servers") else "{{base_url}}"

        for path, path_info in paths.items():
            folder = {
                "name": path.replace("/api/", "").replace("/", " ").title(),
                "item": []
            }

            for method, method_info in path_info.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    request = {
                        "name": method_info.get("summary", f"{method.upper()} {path}"),
                        "request": {
                            "method": method.upper(),
                            "header": [
                                {
                                    "key": "Authorization",
                                    "value": "Bearer {{api_key}}",
                                    "type": "text"
                                },
                                {
                                    "key": "Content-Type",
                                    "value": "application/json",
                                    "type": "text"
                                }
                            ],
                            "url": {
                                "raw": f"{base_url}{path}",
                                "host": [base_url],
                                "path": path.split("/")[1:]
                            }
                        }
                    }

                    folder["item"].append(request)

            if folder["item"]:
                collection["item"].append(folder)

        return collection

    async def _generate_changelog(self, openapi_spec: Dict[str, Any]) -> str:
        """Generate API changelog"""
        return f"""
# API Changelog

## Version {openapi_spec.get('info', {}).get('version', '1.0.0')}

### Added
- Initial API implementation
- {len(openapi_spec.get('paths', {}))} endpoints available
- Authentication support
- Rate limiting
- Comprehensive error handling

### Features
- RESTful API design
- JSON request/response format
- OpenAPI 3.0 specification
- Auto-generated documentation
        """

    async def _generate_glossary(self, openapi_spec: Dict[str, Any]) -> str:
        """Generate API glossary"""
        return """
# Glossary

**API Key**: A unique identifier used to authenticate requests to the API

**Bearer Token**: An authentication method where the token is included in the Authorization header

**Endpoint**: A specific URL where the API can be accessed

**HTTP Status Code**: A standard response code indicating the result of the HTTP request

**JSON**: JavaScript Object Notation, a lightweight data interchange format

**Rate Limiting**: A technique to limit the number of API requests a client can make

**Request Body**: Data sent to the API in POST, PUT, or PATCH requests

**Response**: Data returned by the API after processing a request

**REST**: Representational State Transfer, an architectural style for web services

**SDK**: Software Development Kit, a collection of tools for integrating with the API
        """

    async def _generate_tutorials(self, openapi_spec: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate API tutorials"""
        return [
            {
                "title": "Quick Start Tutorial",
                "description": "Get up and running with the API in 5 minutes",
                "content": "Step-by-step guide to making your first API request"
            },
            {
                "title": "Authentication Guide",
                "description": "Complete guide to API authentication",
                "content": "Learn how to securely authenticate with the API"
            },
            {
                "title": "Error Handling Best Practices",
                "description": "Handle API errors like a pro",
                "content": "Comprehensive guide to error handling and retry logic"
            }
        ]

    async def _generate_download_links(self, formatted_docs: str, format: str) -> Dict[str, str]:
        """Generate download links for documentation"""
        return {
            "html": "/docs/download?format=html",
            "pdf": "/docs/download?format=pdf",
            "markdown": "/docs/download?format=markdown",
            "postman": "/docs/download?format=postman",
            "openapi": "/docs/download?format=openapi"
        }

# Usage example and testing
if __name__ == "__main__":
    async def test_documentation_agent():
        agent = DocumentationAgent()

        # Sample OpenAPI spec
        sample_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Sample API",
                "description": "A sample API for testing documentation generation",
                "version": "1.0.0"
            },
            "servers": [
                {"url": "https://api.example.com"}
            ],
            "paths": {
                "/api/users": {
                    "get": {
                        "summary": "List users",
                        "description": "Retrieve a list of all users",
                        "tags": ["Users"],
                        "responses": {
                            "200": {
                                "description": "List of users",
                                "content": {
                                    "application/json": {
                                        "example": [{"id": 1, "name": "John", "email": "john@example.com"}]
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "summary": "Create user",
                        "description": "Create a new user",
                        "tags": ["Users"],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "example": {"name": "John", "email": "john@example.com"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "User created"}
                        }
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer"
                    }
                }
            }
        }

        # Generate documentation
        result = await agent.generate_documentation(sample_spec, format="markdown")
        print("Generated Documentation:")
        print(json.dumps(result, indent=2)[:1000] + "..." if len(str(result)) > 1000 else json.dumps(result, indent=2))

    # Run test
    asyncio.run(test_documentation_agent())
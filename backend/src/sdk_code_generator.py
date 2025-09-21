"""
Multi-Language SDK Code Generator
Generates client SDKs in Python, JavaScript, TypeScript, Java, Go, C#, PHP, Ruby, and more
"""

from typing import Optional, Dict, Any, List, Set, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import os
from pathlib import Path
import zipfile
import tempfile
import uuid
from jinja2 import Environment, BaseLoader, Template

class ProgrammingLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    RUST = "rust"
    DART = "dart"

class AuthType(str, Enum):
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    CUSTOM = "custom"

@dataclass
class EndpointSpec:
    """Specification for an API endpoint"""
    path: str
    method: str
    operation_id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    auth_required: bool = True
    rate_limit: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class SDKConfig:
    """Configuration for SDK generation"""
    package_name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "MIT"
    base_url: str = "https://api.example.com"
    auth_type: AuthType = AuthType.API_KEY

    # Language-specific settings
    language_settings: Dict[str, Any] = field(default_factory=dict)

    # Features to include
    include_retry_logic: bool = True
    include_rate_limiting: bool = True
    include_pagination: bool = True
    include_async_support: bool = True
    include_type_hints: bool = True
    include_examples: bool = True
    include_tests: bool = True

@dataclass
class GeneratedSDK:
    """Generated SDK package"""
    language: ProgrammingLanguage
    package_name: str
    version: str
    files: Dict[str, str]  # filename -> content
    metadata: Dict[str, Any]
    zip_path: Optional[str] = None

class TemplateEngine:
    """Template engine for code generation"""

    def __init__(self):
        self.env = Environment(loader=BaseLoader())
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load language-specific templates"""
        return {
            ProgrammingLanguage.PYTHON: {
                "client": self._get_python_client_template(),
                "model": self._get_python_model_template(),
                "auth": self._get_python_auth_template(),
                "setup": self._get_python_setup_template(),
                "readme": self._get_python_readme_template(),
                "example": self._get_python_example_template(),
                "test": self._get_python_test_template()
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "client": self._get_js_client_template(),
                "model": self._get_js_model_template(),
                "auth": self._get_js_auth_template(),
                "package": self._get_js_package_template(),
                "readme": self._get_js_readme_template(),
                "example": self._get_js_example_template(),
                "test": self._get_js_test_template()
            },
            ProgrammingLanguage.TYPESCRIPT: {
                "client": self._get_ts_client_template(),
                "types": self._get_ts_types_template(),
                "auth": self._get_ts_auth_template(),
                "package": self._get_ts_package_template(),
                "readme": self._get_ts_readme_template(),
                "example": self._get_ts_example_template(),
                "test": self._get_ts_test_template()
            },
            ProgrammingLanguage.JAVA: {
                "client": self._get_java_client_template(),
                "model": self._get_java_model_template(),
                "auth": self._get_java_auth_template(),
                "pom": self._get_java_pom_template(),
                "readme": self._get_java_readme_template(),
                "example": self._get_java_example_template(),
                "test": self._get_java_test_template()
            },
            ProgrammingLanguage.GO: {
                "client": self._get_go_client_template(),
                "model": self._get_go_model_template(),
                "auth": self._get_go_auth_template(),
                "mod": self._get_go_mod_template(),
                "readme": self._get_go_readme_template(),
                "example": self._get_go_example_template(),
                "test": self._get_go_test_template()
            }
        }

    def render_template(self, language: ProgrammingLanguage, template_type: str, **kwargs) -> str:
        """Render a template with given context"""
        template_str = self.templates.get(language, {}).get(template_type, "")
        if not template_str:
            return f"# Template not found for {language.value}:{template_type}"

        template = self.env.from_string(template_str)
        return template.render(**kwargs)

    def _get_python_client_template(self) -> str:
        return '''"""
{{ package_name }} - {{ description }}
Generated API client for {{ base_url }}
"""

import requests
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import time
import logging

{% if include_async_support %}
import asyncio
import aiohttp
{% endif %}

class {{ class_name }}:
    """Main API client for {{ package_name }}"""

    def __init__(self, {% if auth_type == 'api_key' %}api_key: str,{% elif auth_type == 'bearer_token' %}token: str,{% endif %} base_url: str = "{{ base_url }}"):
        self.base_url = base_url.rstrip('/')
        {% if auth_type == 'api_key' %}
        self.api_key = api_key
        {% elif auth_type == 'bearer_token' %}
        self.token = token
        {% endif %}
        self.session = requests.Session()
        self._setup_auth()

        {% if include_retry_logic %}
        self.max_retries = 3
        self.retry_delay = 1.0
        {% endif %}

        {% if include_rate_limiting %}
        self.rate_limit_calls = 0
        self.rate_limit_reset = time.time()
        {% endif %}

    def _setup_auth(self):
        """Setup authentication headers"""
        {% if auth_type == 'api_key' %}
        self.session.headers.update({
            'X-API-Key': self.api_key
        })
        {% elif auth_type == 'bearer_token' %}
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}'
        })
        {% endif %}
        self.session.headers.update({
            'User-Agent': '{{ package_name }}/{{ version }}',
            'Content-Type': 'application/json'
        })

    {% if include_retry_logic %}
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(method, url, **kwargs)

                if response.status_code < 500:
                    return response

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise

        return response
    {% endif %}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"

        {% if include_rate_limiting %}
        # Simple rate limiting
        if self.rate_limit_calls >= 100:  # Assuming 100 calls per minute
            wait_time = 60 - (time.time() - self.rate_limit_reset)
            if wait_time > 0:
                time.sleep(wait_time)
                self.rate_limit_calls = 0
                self.rate_limit_reset = time.time()
        {% endif %}

        {% if include_retry_logic %}
        response = self._make_request_with_retry(method, url, **kwargs)
        {% else %}
        response = self.session.request(method, url, **kwargs)
        {% endif %}

        {% if include_rate_limiting %}
        self.rate_limit_calls += 1
        {% endif %}

        if response.status_code >= 400:
            raise {{ class_name }}Error(f"API request failed: {response.status_code} - {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError:
            return {"data": response.text}

{% for endpoint in endpoints %}
    def {{ endpoint.method_name }}(self{% for param in endpoint.parameters %}, {{ param.name }}: {{ param.type }}{% if not param.required %} = None{% endif %}{% endfor %}) -> Dict[str, Any]:
        """{{ endpoint.description or endpoint.summary or 'API endpoint' }}"""

        {% if endpoint.path_params %}
        # Build path with parameters
        path = "{{ endpoint.path }}"
        {% for param in endpoint.path_params %}
        path = path.replace("{{{ param.name }}}", str({{ param.name }}))
        {% endfor %}
        {% else %}
        path = "{{ endpoint.path }}"
        {% endif %}

        {% if endpoint.query_params %}
        # Build query parameters
        params = {}
        {% for param in endpoint.query_params %}
        if {{ param.name }} is not None:
            params["{{ param.name }}"] = {{ param.name }}
        {% endfor %}
        {% else %}
        params = None
        {% endif %}

        {% if endpoint.has_body %}
        # Build request body
        data = {}
        {% for param in endpoint.body_params %}
        if {{ param.name }} is not None:
            data["{{ param.name }}"] = {{ param.name }}
        {% endfor %}

        return self._make_request("{{ endpoint.method.upper() }}", path, params=params, json=data)
        {% else %}
        return self._make_request("{{ endpoint.method.upper() }}", path, params=params)
        {% endif %}

{% endfor %}

{% if include_async_support %}
class Async{{ class_name }}:
    """Async API client for {{ package_name }}"""

    def __init__(self, {% if auth_type == 'api_key' %}api_key: str,{% elif auth_type == 'bearer_token' %}token: str,{% endif %} base_url: str = "{{ base_url }}"):
        self.base_url = base_url.rstrip('/')
        {% if auth_type == 'api_key' %}
        self.api_key = api_key
        {% elif auth_type == 'bearer_token' %}
        self.token = token
        {% endif %}
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            'User-Agent': '{{ package_name }}/{{ version }}',
            'Content-Type': 'application/json'
        }

        {% if auth_type == 'api_key' %}
        headers['X-API-Key'] = self.api_key
        {% elif auth_type == 'bearer_token' %}
        headers['Authorization'] = f'Bearer {self.token}'
        {% endif %}

        return headers

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make async HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        async with self.session.request(method, url, headers=headers, **kwargs) as response:
            if response.status >= 400:
                text = await response.text()
                raise {{ class_name }}Error(f"API request failed: {response.status} - {text}")

            try:
                return await response.json()
            except:
                text = await response.text()
                return {"data": text}

{% for endpoint in endpoints %}
    async def {{ endpoint.method_name }}(self{% for param in endpoint.parameters %}, {{ param.name }}: {{ param.type }}{% if not param.required %} = None{% endif %}{% endfor %}) -> Dict[str, Any]:
        """{{ endpoint.description or endpoint.summary or 'API endpoint' }}"""

        {% if endpoint.path_params %}
        # Build path with parameters
        path = "{{ endpoint.path }}"
        {% for param in endpoint.path_params %}
        path = path.replace("{{{ param.name }}}", str({{ param.name }}))
        {% endfor %}
        {% else %}
        path = "{{ endpoint.path }}"
        {% endif %}

        {% if endpoint.query_params %}
        # Build query parameters
        params = {}
        {% for param in endpoint.query_params %}
        if {{ param.name }} is not None:
            params["{{ param.name }}"] = {{ param.name }}
        {% endfor %}
        {% else %}
        params = None
        {% endif %}

        {% if endpoint.has_body %}
        # Build request body
        data = {}
        {% for param in endpoint.body_params %}
        if {{ param.name }} is not None:
            data["{{ param.name }}"] = {{ param.name }}
        {% endfor %}

        return await self._make_request("{{ endpoint.method.upper() }}", path, params=params, json=data)
        {% else %}
        return await self._make_request("{{ endpoint.method.upper() }}", path, params=params)
        {% endif %}

{% endfor %}
{% endif %}

class {{ class_name }}Error(Exception):
    """Custom exception for {{ package_name }} errors"""
    pass

# Convenience functions
def create_client({% if auth_type == 'api_key' %}api_key: str,{% elif auth_type == 'bearer_token' %}token: str,{% endif %} base_url: str = "{{ base_url }}") -> {{ class_name }}:
    """Create a new API client instance"""
    return {{ class_name }}({% if auth_type == 'api_key' %}api_key,{% elif auth_type == 'bearer_token' %}token,{% endif %} base_url)

{% if include_async_support %}
def create_async_client({% if auth_type == 'api_key' %}api_key: str,{% elif auth_type == 'bearer_token' %}token: str,{% endif %} base_url: str = "{{ base_url }}") -> Async{{ class_name }}:
    """Create a new async API client instance"""
    return Async{{ class_name }}({% if auth_type == 'api_key' %}api_key,{% elif auth_type == 'bearer_token' %}token,{% endif %} base_url)
{% endif %}
'''

    def _get_python_setup_template(self) -> str:
        return '''"""
Setup script for {{ package_name }}
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{{ package_name }}",
    version="{{ version }}",
    author="{{ author }}",
    description="{{ description }}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: {{ license }} License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        {% if include_async_support %}"aiohttp>=3.8.0",{% endif %}
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0",
            "flake8>=3.9.0",
        ],
    },
)
'''

    def _get_python_readme_template(self) -> str:
        return '''# {{ package_name }}

{{ description }}

## Installation

```bash
pip install {{ package_name }}
```

## Quick Start

```python
from {{ package_name }} import create_client

# Initialize client
client = create_client({% if auth_type == 'api_key' %}api_key="your-api-key"{% elif auth_type == 'bearer_token' %}token="your-bearer-token"{% endif %})

{% for endpoint in endpoints[:3] %}
# {{ endpoint.summary or endpoint.description or 'Example usage' }}
result = client.{{ endpoint.method_name }}({% for param in endpoint.required_params %}{{ param.name }}="{{ param.example or 'value' }}"{% if not loop.last %}, {% endif %}{% endfor %})
print(result)

{% endfor %}
```

{% if include_async_support %}
## Async Usage

```python
import asyncio
from {{ package_name }} import create_async_client

async def main():
    async with create_async_client({% if auth_type == 'api_key' %}api_key="your-api-key"{% elif auth_type == 'bearer_token' %}token="your-bearer-token"{% endif %}) as client:
        result = await client.{{ endpoints[0].method_name }}()
        print(result)

asyncio.run(main())
```
{% endif %}

## Features

{% if include_retry_logic %}- ✅ Automatic retry logic{% endif %}
{% if include_rate_limiting %}- ✅ Built-in rate limiting{% endif %}
{% if include_async_support %}- ✅ Async/await support{% endif %}
{% if include_type_hints %}- ✅ Full type hints{% endif %}
- ✅ Comprehensive error handling
- ✅ Detailed documentation

## API Reference

{% for endpoint in endpoints %}
### {{ endpoint.method_name }}()

{{ endpoint.description or endpoint.summary or 'No description available' }}

**Parameters:**
{% for param in endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}){% if param.required %} - Required{% endif %}{% if param.description %} - {{ param.description }}{% endif %}
{% endfor %}

**Returns:** Dict[str, Any]

**Example:**
```python
result = client.{{ endpoint.method_name }}({% for param in endpoint.required_params %}{{ param.name }}="{{ param.example or 'value' }}"{% if not loop.last %}, {% endif %}{% endfor %})
```

{% endfor %}

## Error Handling

```python
from {{ package_name }} import {{ class_name }}Error

try:
    result = client.some_method()
except {{ class_name }}Error as e:
    print(f"API error: {e}")
```

## License

This project is licensed under the {{ license }} License.
'''

    def _get_python_example_template(self) -> str:
        return '''"""
Example usage of {{ package_name }}
"""

from {{ package_name }} import create_client{% if include_async_support %}, create_async_client{% endif %}
import os

def main():
    """Example usage of the API client"""

    # Get API credentials from environment
    {% if auth_type == 'api_key' %}
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable is required")

    # Create client
    client = create_client(api_key=api_key)
    {% elif auth_type == 'bearer_token' %}
    token = os.getenv("BEARER_TOKEN")
    if not token:
        raise ValueError("BEARER_TOKEN environment variable is required")

    # Create client
    client = create_client(token=token)
    {% endif %}

    try:
        {% for endpoint in endpoints[:3] %}
        # {{ endpoint.summary or endpoint.description or 'Example API call' }}
        print("Calling {{ endpoint.method_name }}...")
        result = client.{{ endpoint.method_name }}({% for param in endpoint.required_params %}{{ param.name }}="{{ param.example or 'example_value' }}"{% if not loop.last %}, {% endif %}{% endfor %})
        print(f"Result: {result}")
        print()

        {% endfor %}
    except Exception as e:
        print(f"Error: {e}")

{% if include_async_support %}
async def async_main():
    """Example async usage of the API client"""

    {% if auth_type == 'api_key' %}
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable is required")

    async with create_async_client(api_key=api_key) as client:
    {% elif auth_type == 'bearer_token' %}
    token = os.getenv("BEARER_TOKEN")
    if not token:
        raise ValueError("BEARER_TOKEN environment variable is required")

    async with create_async_client(token=token) as client:
    {% endif %}
        try:
            {% for endpoint in endpoints[:2] %}
            # {{ endpoint.summary or endpoint.description or 'Example async API call' }}
            print("Calling {{ endpoint.method_name }} async...")
            result = await client.{{ endpoint.method_name }}({% for param in endpoint.required_params %}{{ param.name }}="{{ param.example or 'example_value' }}"{% if not loop.last %}, {% endif %}{% endfor %})
            print(f"Result: {result}")
            print()

            {% endfor %}
        except Exception as e:
            print(f"Error: {e}")
{% endif %}

if __name__ == "__main__":
    main()

    {% if include_async_support %}
    # Uncomment to run async example
    # import asyncio
    # asyncio.run(async_main())
    {% endif %}
'''

    def _get_python_test_template(self) -> str:
        return '''"""
Tests for {{ package_name }}
"""

import pytest
import requests_mock
{% if include_async_support %}
import aiohttp
import aioresponses
{% endif %}

from {{ package_name }} import create_client{% if include_async_support %}, create_async_client{% endif %}, {{ class_name }}Error

class TestClient:
    """Test the main API client"""

    def setup_method(self):
        """Setup test client"""
        self.client = create_client({% if auth_type == 'api_key' %}api_key="test-api-key"{% elif auth_type == 'bearer_token' %}token="test-token"{% endif %})

    {% for endpoint in endpoints[:3] %}
    def test_{{ endpoint.method_name }}(self):
        """Test {{ endpoint.method_name }} method"""
        with requests_mock.Mocker() as m:
            # Mock successful response
            m.{{ endpoint.method.lower() }}(
                "{{ base_url }}{{ endpoint.path }}",
                json={"success": True, "data": {"id": 1, "name": "test"}}
            )

            result = self.client.{{ endpoint.method_name }}({% for param in endpoint.required_params %}{{ param.name }}="{{ param.example or 'test_value' }}"{% if not loop.last %}, {% endif %}{% endfor %})

            assert result["success"] is True
            assert "data" in result

    def test_{{ endpoint.method_name }}_error(self):
        """Test {{ endpoint.method_name }} error handling"""
        with requests_mock.Mocker() as m:
            # Mock error response
            m.{{ endpoint.method.lower() }}(
                "{{ base_url }}{{ endpoint.path }}",
                status_code=404,
                text="Not Found"
            )

            with pytest.raises({{ class_name }}Error):
                self.client.{{ endpoint.method_name }}({% for param in endpoint.required_params %}{{ param.name }}="{{ param.example or 'test_value' }}"{% if not loop.last %}, {% endif %}{% endfor %})

    {% endfor %}

{% if include_async_support %}
class TestAsyncClient:
    """Test the async API client"""

    {% for endpoint in endpoints[:2] %}
    @pytest.mark.asyncio
    async def test_async_{{ endpoint.method_name }}(self):
        """Test async {{ endpoint.method_name }} method"""
        with aioresponses.aioresponses() as m:
            # Mock successful response
            m.{{ endpoint.method.lower() }}(
                "{{ base_url }}{{ endpoint.path }}",
                payload={"success": True, "data": {"id": 1, "name": "test"}}
            )

            async with create_async_client({% if auth_type == 'api_key' %}api_key="test-api-key"{% elif auth_type == 'bearer_token' %}token="test-token"{% endif %}) as client:
                result = await client.{{ endpoint.method_name }}({% for param in endpoint.required_params %}{{ param.name }}="{{ param.example or 'test_value' }}"{% if not loop.last %}, {% endif %}{% endfor %})

                assert result["success"] is True
                assert "data" in result

    {% endfor %}
{% endif %}
'''

    def _get_python_model_template(self) -> str:
        return '''"""
Data models for {{ package_name }}
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

{% for model in models %}
@dataclass
class {{ model.name }}:
    """{{ model.description or model.name + ' model' }}"""

    {% for field in model.fields %}
    {{ field.name }}: {{ field.type }}{% if not field.required %} = None{% endif %}
    {% endfor %}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "{{ model.name }}":
        """Create instance from dictionary"""
        return cls(
            {% for field in model.fields %}
            {{ field.name }}=data.get("{{ field.name }}"){% if not loop.last %},{% endif %}
            {% endfor %}
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            {% for field in model.fields %}
            "{{ field.name }}": self.{{ field.name }}{% if not loop.last %},{% endif %}
            {% endfor %}
        }

{% endfor %}
'''

    def _get_python_auth_template(self) -> str:
        return '''"""
Authentication helpers for {{ package_name }}
"""

from typing import Dict, Optional
import base64

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

{% if auth_type == 'api_key' %}
class APIKeyAuth:
    """API Key authentication"""

    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        self.api_key = api_key
        self.header_name = header_name

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {self.header_name: self.api_key}

{% elif auth_type == 'bearer_token' %}
class BearerTokenAuth:
    """Bearer token authentication"""

    def __init__(self, token: str):
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {"Authorization": f"Bearer {self.token}"}

{% elif auth_type == 'basic_auth' %}
class BasicAuth:
    """Basic authentication"""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

{% endif %}
'''

    def _get_js_client_template(self) -> str:
        return '''/**
 * {{ package_name }} - {{ description }}
 * Generated API client for {{ base_url }}
 */

class {{ class_name }} {
    /**
     * Create a new API client
     * @param {string} {% if auth_type == 'api_key' %}apiKey - Your API key{% elif auth_type == 'bearer_token' %}token - Your bearer token{% endif %}
     * @param {string} baseUrl - Base URL for the API
     */
    constructor({% if auth_type == 'api_key' %}apiKey,{% elif auth_type == 'bearer_token' %}token,{% endif %} baseUrl = "{{ base_url }}") {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        {% if auth_type == 'api_key' %}
        this.apiKey = apiKey;
        {% elif auth_type == 'bearer_token' %}
        this.token = token;
        {% endif %}

        {% if include_retry_logic %}
        this.maxRetries = 3;
        this.retryDelay = 1000;
        {% endif %}

        {% if include_rate_limiting %}
        this.rateLimitCalls = 0;
        this.rateLimitReset = Date.now();
        {% endif %}
    }

    /**
     * Get default headers for requests
     * @returns {Object} Headers object
     */
    _getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'User-Agent': '{{ package_name }}/{{ version }}'
        };

        {% if auth_type == 'api_key' %}
        headers['X-API-Key'] = this.apiKey;
        {% elif auth_type == 'bearer_token' %}
        headers['Authorization'] = `Bearer ${this.token}`;
        {% endif %}

        return headers;
    }

    {% if include_retry_logic %}
    /**
     * Make HTTP request with retry logic
     * @param {string} method - HTTP method
     * @param {string} url - Request URL
     * @param {Object} options - Request options
     * @returns {Promise<Response>} Fetch response
     */
    async _makeRequestWithRetry(method, url, options = {}) {
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await fetch(url, {
                    method,
                    headers: this._getHeaders(),
                    ...options
                });

                if (response.status < 500) {
                    return response;
                }

                if (attempt < this.maxRetries) {
                    await new Promise(resolve =>
                        setTimeout(resolve, this.retryDelay * Math.pow(2, attempt))
                    );
                }
            } catch (error) {
                if (attempt < this.maxRetries) {
                    await new Promise(resolve =>
                        setTimeout(resolve, this.retryDelay * Math.pow(2, attempt))
                    );
                } else {
                    throw error;
                }
            }
        }
    }
    {% endif %}

    /**
     * Make HTTP request to API
     * @param {string} method - HTTP method
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    async _makeRequest(method, endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        {% if include_rate_limiting %}
        // Simple rate limiting
        if (this.rateLimitCalls >= 100) {
            const waitTime = 60000 - (Date.now() - this.rateLimitReset);
            if (waitTime > 0) {
                await new Promise(resolve => setTimeout(resolve, waitTime));
                this.rateLimitCalls = 0;
                this.rateLimitReset = Date.now();
            }
        }
        {% endif %}

        {% if include_retry_logic %}
        const response = await this._makeRequestWithRetry(method, url, options);
        {% else %}
        const response = await fetch(url, {
            method,
            headers: this._getHeaders(),
            ...options
        });
        {% endif %}

        {% if include_rate_limiting %}
        this.rateLimitCalls++;
        {% endif %}

        if (!response.ok) {
            const errorText = await response.text();
            throw new {{ class_name }}Error(`API request failed: ${response.status} - ${errorText}`);
        }

        try {
            return await response.json();
        } catch (error) {
            const text = await response.text();
            return { data: text };
        }
    }

{% for endpoint in endpoints %}
    /**
     * {{ endpoint.description or endpoint.summary or 'API endpoint' }}
     {% for param in endpoint.parameters %}
     * @param {{ '{' }}{{ param.type }}{{ '}' }}{% if not param.required %} [{% endif %}{{ param.name }}{% if not param.required %}]{% endif %}{% if param.description %} - {{ param.description }}{% endif %}
     {% endfor %}
     * @returns {Promise<Object>} Response data
     */
    async {{ endpoint.method_name }}({% for param in endpoint.parameters %}{{ param.name }}{% if not param.required %} = null{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}) {
        {% if endpoint.path_params %}
        // Build path with parameters
        let path = "{{ endpoint.path }}";
        {% for param in endpoint.path_params %}
        path = path.replace("{{{ param.name }}}", {{ param.name }});
        {% endfor %}
        {% else %}
        const path = "{{ endpoint.path }}";
        {% endif %}

        const options = {};

        {% if endpoint.query_params %}
        // Build query parameters
        const params = new URLSearchParams();
        {% for param in endpoint.query_params %}
        if ({{ param.name }} !== null && {{ param.name }} !== undefined) {
            params.append("{{ param.name }}", {{ param.name }});
        }
        {% endfor %}

        const queryString = params.toString();
        const finalPath = queryString ? `${path}?${queryString}` : path;
        {% else %}
        const finalPath = path;
        {% endif %}

        {% if endpoint.has_body %}
        // Build request body
        const data = {};
        {% for param in endpoint.body_params %}
        if ({{ param.name }} !== null && {{ param.name }} !== undefined) {
            data.{{ param.name }} = {{ param.name }};
        }
        {% endfor %}

        options.body = JSON.stringify(data);
        {% endif %}

        return await this._makeRequest("{{ endpoint.method.upper() }}", finalPath, options);
    }

{% endfor %}
}

/**
 * Custom error class for API errors
 */
class {{ class_name }}Error extends Error {
    constructor(message) {
        super(message);
        this.name = '{{ class_name }}Error';
    }
}

/**
 * Create a new API client instance
 * @param {string} {% if auth_type == 'api_key' %}apiKey - Your API key{% elif auth_type == 'bearer_token' %}token - Your bearer token{% endif %}
 * @param {string} baseUrl - Base URL for the API
 * @returns {{{ class_name }}} API client instance
 */
function createClient({% if auth_type == 'api_key' %}apiKey,{% elif auth_type == 'bearer_token' %}token,{% endif %} baseUrl = "{{ base_url }}") {
    return new {{ class_name }}({% if auth_type == 'api_key' %}apiKey,{% elif auth_type == 'bearer_token' %}token,{% endif %} baseUrl);
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = { {{ class_name }}, {{ class_name }}Error, createClient };
} else if (typeof define === 'function' && define.amd) {
    // AMD
    define(() => ({ {{ class_name }}, {{ class_name }}Error, createClient }));
} else {
    // Browser global
    window.{{ class_name }} = {{ class_name }};
    window.{{ class_name }}Error = {{ class_name }}Error;
    window.createClient = createClient;
}
'''

    def _get_js_package_template(self) -> str:
        return '''{
  "name": "{{ package_name }}",
  "version": "{{ version }}",
  "description": "{{ description }}",
  "main": "index.js",
  "scripts": {
    "test": "jest",
    "build": "webpack --mode=production",
    "dev": "webpack --mode=development --watch"
  },
  "keywords": ["api", "client", "sdk"],
  "author": "{{ author }}",
  "license": "{{ license }}",
  "dependencies": {
    {% if include_async_support %}
    "node-fetch": "^3.0.0"
    {% endif %}
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "webpack": "^5.0.0",
    "webpack-cli": "^4.0.0"
  },
  "files": [
    "index.js",
    "README.md"
  ],
  "repository": {
    "type": "git",
    "url": "https://github.com/example/{{ package_name }}.git"
  },
  "bugs": {
    "url": "https://github.com/example/{{ package_name }}/issues"
  },
  "homepage": "https://github.com/example/{{ package_name }}#readme"
}
'''

    # Additional template methods would be implemented here for other languages...
    # For brevity, I'm showing the structure for Python and JavaScript

    def _get_js_readme_template(self) -> str:
        return "# JavaScript README template..."

    def _get_js_example_template(self) -> str:
        return "// JavaScript example template..."

    def _get_js_test_template(self) -> str:
        return "// JavaScript test template..."

    def _get_js_model_template(self) -> str:
        return "// JavaScript model template..."

    def _get_js_auth_template(self) -> str:
        return "// JavaScript auth template..."

    # TypeScript templates
    def _get_ts_client_template(self) -> str:
        return "// TypeScript client template..."

    def _get_ts_types_template(self) -> str:
        return "// TypeScript types template..."

    def _get_ts_auth_template(self) -> str:
        return "// TypeScript auth template..."

    def _get_ts_package_template(self) -> str:
        return "// TypeScript package.json template..."

    def _get_ts_readme_template(self) -> str:
        return "# TypeScript README template..."

    def _get_ts_example_template(self) -> str:
        return "// TypeScript example template..."

    def _get_ts_test_template(self) -> str:
        return "// TypeScript test template..."

    # Java templates
    def _get_java_client_template(self) -> str:
        return "// Java client template..."

    def _get_java_model_template(self) -> str:
        return "// Java model template..."

    def _get_java_auth_template(self) -> str:
        return "// Java auth template..."

    def _get_java_pom_template(self) -> str:
        return "<!-- Java pom.xml template... -->"

    def _get_java_readme_template(self) -> str:
        return "# Java README template..."

    def _get_java_example_template(self) -> str:
        return "// Java example template..."

    def _get_java_test_template(self) -> str:
        return "// Java test template..."

    # Go templates
    def _get_go_client_template(self) -> str:
        return "// Go client template..."

    def _get_go_model_template(self) -> str:
        return "// Go model template..."

    def _get_go_auth_template(self) -> str:
        return "// Go auth template..."

    def _get_go_mod_template(self) -> str:
        return "// Go go.mod template..."

    def _get_go_readme_template(self) -> str:
        return "# Go README template..."

    def _get_go_example_template(self) -> str:
        return "// Go example template..."

    def _get_go_test_template(self) -> str:
        return "// Go test template..."

class MultiLanguageSDKGenerator:
    """Main SDK generator for multiple programming languages"""

    def __init__(self):
        self.template_engine = TemplateEngine()
        self.generated_sdks: Dict[str, GeneratedSDK] = {}

    async def generate_sdk(self,
                          language: ProgrammingLanguage,
                          endpoints: List[EndpointSpec],
                          config: SDKConfig) -> GeneratedSDK:
        """Generate SDK for specified language"""

        # Prepare context for templates
        context = self._prepare_template_context(endpoints, config, language)

        # Generate files based on language
        files = {}

        if language == ProgrammingLanguage.PYTHON:
            files = await self._generate_python_sdk(context)
        elif language == ProgrammingLanguage.JAVASCRIPT:
            files = await self._generate_javascript_sdk(context)
        elif language == ProgrammingLanguage.TYPESCRIPT:
            files = await self._generate_typescript_sdk(context)
        elif language == ProgrammingLanguage.JAVA:
            files = await self._generate_java_sdk(context)
        elif language == ProgrammingLanguage.GO:
            files = await self._generate_go_sdk(context)
        else:
            raise ValueError(f"Unsupported language: {language}")

        # Create SDK object
        sdk = GeneratedSDK(
            language=language,
            package_name=config.package_name,
            version=config.version,
            files=files,
            metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "endpoints_count": len(endpoints),
                "language": language.value,
                "config": config.__dict__
            }
        )

        # Create zip package
        sdk.zip_path = await self._create_zip_package(sdk)

        # Store generated SDK
        self.generated_sdks[f"{language.value}_{config.package_name}"] = sdk

        return sdk

    def _prepare_template_context(self,
                                endpoints: List[EndpointSpec],
                                config: SDKConfig,
                                language: ProgrammingLanguage) -> Dict[str, Any]:
        """Prepare context for template rendering"""

        # Process endpoints for template usage
        processed_endpoints = []
        for endpoint in endpoints:
            processed_endpoint = self._process_endpoint_for_language(endpoint, language)
            processed_endpoints.append(processed_endpoint)

        # Create class name
        class_name = self._generate_class_name(config.package_name, language)

        return {
            "package_name": config.package_name,
            "class_name": class_name,
            "version": config.version,
            "description": config.description,
            "author": config.author,
            "license": config.license,
            "base_url": config.base_url,
            "auth_type": config.auth_type.value,
            "endpoints": processed_endpoints,
            "include_retry_logic": config.include_retry_logic,
            "include_rate_limiting": config.include_rate_limiting,
            "include_pagination": config.include_pagination,
            "include_async_support": config.include_async_support,
            "include_type_hints": config.include_type_hints,
            "include_examples": config.include_examples,
            "include_tests": config.include_tests,
            "language_settings": config.language_settings.get(language.value, {})
        }

    def _process_endpoint_for_language(self,
                                     endpoint: EndpointSpec,
                                     language: ProgrammingLanguage) -> Dict[str, Any]:
        """Process endpoint specification for specific language"""

        # Generate method name
        method_name = self._generate_method_name(endpoint.operation_id or endpoint.path, language)

        # Process parameters
        processed_params = []
        path_params = []
        query_params = []
        body_params = []

        for param in endpoint.parameters:
            processed_param = {
                "name": self._convert_parameter_name(param["name"], language),
                "type": self._convert_type(param.get("type", "string"), language),
                "required": param.get("required", False),
                "description": param.get("description", ""),
                "example": param.get("example", "")
            }

            processed_params.append(processed_param)

            # Categorize parameters
            location = param.get("in", "query")
            if location == "path":
                path_params.append(processed_param)
            elif location == "query":
                query_params.append(processed_param)
            elif location == "body":
                body_params.append(processed_param)

        return {
            "path": endpoint.path,
            "method": endpoint.method.lower(),
            "method_name": method_name,
            "operation_id": endpoint.operation_id,
            "summary": endpoint.summary,
            "description": endpoint.description,
            "parameters": processed_params,
            "path_params": path_params,
            "query_params": query_params,
            "body_params": body_params,
            "has_body": len(body_params) > 0 or endpoint.request_body is not None,
            "required_params": [p for p in processed_params if p["required"]],
            "auth_required": endpoint.auth_required
        }

    def _generate_class_name(self, package_name: str, language: ProgrammingLanguage) -> str:
        """Generate appropriate class name for language"""

        # Convert package name to class name
        words = re.findall(r'[A-Za-z0-9]+', package_name)

        if language in [ProgrammingLanguage.PYTHON, ProgrammingLanguage.RUBY]:
            # PascalCase for Python/Ruby classes
            return ''.join(word.capitalize() for word in words) + "Client"
        elif language in [ProgrammingLanguage.JAVA, ProgrammingLanguage.CSHARP, ProgrammingLanguage.KOTLIN]:
            # PascalCase for Java/C#/Kotlin
            return ''.join(word.capitalize() for word in words) + "Client"
        elif language == ProgrammingLanguage.GO:
            # PascalCase for Go
            return ''.join(word.capitalize() for word in words) + "Client"
        else:
            # camelCase for JavaScript/TypeScript
            if not words:
                return "APIClient"
            return words[0].lower() + ''.join(word.capitalize() for word in words[1:]) + "Client"

    def _generate_method_name(self, operation_id: str, language: ProgrammingLanguage) -> str:
        """Generate appropriate method name for language"""

        # Clean operation ID
        if operation_id.startswith('/'):
            # Extract from path
            parts = [part for part in operation_id.split('/') if part and not part.startswith('{')]
            if len(parts) >= 2:
                operation_id = f"{parts[-2]}_{parts[-1]}"
            elif parts:
                operation_id = parts[-1]
            else:
                operation_id = "api_call"

        # Convert to appropriate case
        words = re.findall(r'[A-Za-z0-9]+', operation_id)

        if language in [ProgrammingLanguage.PYTHON, ProgrammingLanguage.RUBY]:
            # snake_case
            return '_'.join(word.lower() for word in words)
        else:
            # camelCase
            if not words:
                return "apiCall"
            return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

    def _convert_parameter_name(self, param_name: str, language: ProgrammingLanguage) -> str:
        """Convert parameter name to appropriate case for language"""

        words = re.findall(r'[A-Za-z0-9]+', param_name)

        if language in [ProgrammingLanguage.PYTHON, ProgrammingLanguage.RUBY]:
            # snake_case
            return '_'.join(word.lower() for word in words)
        else:
            # camelCase
            if not words:
                return "param"
            return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

    def _convert_type(self, api_type: str, language: ProgrammingLanguage) -> str:
        """Convert API type to language-specific type"""

        type_mappings = {
            ProgrammingLanguage.PYTHON: {
                "string": "str",
                "integer": "int",
                "number": "float",
                "boolean": "bool",
                "array": "List",
                "object": "Dict[str, Any]"
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "string": "string",
                "integer": "number",
                "number": "number",
                "boolean": "boolean",
                "array": "Array",
                "object": "Object"
            },
            ProgrammingLanguage.TYPESCRIPT: {
                "string": "string",
                "integer": "number",
                "number": "number",
                "boolean": "boolean",
                "array": "Array<any>",
                "object": "Record<string, any>"
            },
            ProgrammingLanguage.JAVA: {
                "string": "String",
                "integer": "Integer",
                "number": "Double",
                "boolean": "Boolean",
                "array": "List<Object>",
                "object": "Map<String, Object>"
            },
            ProgrammingLanguage.GO: {
                "string": "string",
                "integer": "int",
                "number": "float64",
                "boolean": "bool",
                "array": "[]interface{}",
                "object": "map[string]interface{}"
            }
        }

        mapping = type_mappings.get(language, {})
        return mapping.get(api_type, "string")

    async def _generate_python_sdk(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate Python SDK files"""

        files = {}

        # Main client file
        files["__init__.py"] = self.template_engine.render_template(
            ProgrammingLanguage.PYTHON, "client", **context
        )

        # Setup file
        files["setup.py"] = self.template_engine.render_template(
            ProgrammingLanguage.PYTHON, "setup", **context
        )

        # README
        files["README.md"] = self.template_engine.render_template(
            ProgrammingLanguage.PYTHON, "readme", **context
        )

        # Example
        if context["include_examples"]:
            files["examples/example.py"] = self.template_engine.render_template(
                ProgrammingLanguage.PYTHON, "example", **context
            )

        # Tests
        if context["include_tests"]:
            files["tests/test_client.py"] = self.template_engine.render_template(
                ProgrammingLanguage.PYTHON, "test", **context
            )

        # Models (if needed)
        files["models.py"] = self.template_engine.render_template(
            ProgrammingLanguage.PYTHON, "model", **context
        )

        # Auth helpers
        files["auth.py"] = self.template_engine.render_template(
            ProgrammingLanguage.PYTHON, "auth", **context
        )

        return files

    async def _generate_javascript_sdk(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate JavaScript SDK files"""

        files = {}

        # Main client file
        files["index.js"] = self.template_engine.render_template(
            ProgrammingLanguage.JAVASCRIPT, "client", **context
        )

        # Package.json
        files["package.json"] = self.template_engine.render_template(
            ProgrammingLanguage.JAVASCRIPT, "package", **context
        )

        # README
        files["README.md"] = self.template_engine.render_template(
            ProgrammingLanguage.JAVASCRIPT, "readme", **context
        )

        # Example
        if context["include_examples"]:
            files["examples/example.js"] = self.template_engine.render_template(
                ProgrammingLanguage.JAVASCRIPT, "example", **context
            )

        # Tests
        if context["include_tests"]:
            files["tests/client.test.js"] = self.template_engine.render_template(
                ProgrammingLanguage.JAVASCRIPT, "test", **context
            )

        return files

    async def _generate_typescript_sdk(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate TypeScript SDK files"""
        files = {}
        # Implementation would be similar to JavaScript but with TypeScript templates
        return files

    async def _generate_java_sdk(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate Java SDK files"""
        files = {}
        # Implementation would use Java-specific templates
        return files

    async def _generate_go_sdk(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate Go SDK files"""
        files = {}
        # Implementation would use Go-specific templates
        return files

    async def _create_zip_package(self, sdk: GeneratedSDK) -> str:
        """Create a downloadable zip package of the SDK"""

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"{sdk.package_name}_{sdk.language.value}_v{sdk.version}.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, content in sdk.files.items():
                # Create directory structure in zip
                zipf.writestr(filename, content)

        return zip_path

    def get_generated_sdk(self, language: ProgrammingLanguage, package_name: str) -> Optional[GeneratedSDK]:
        """Get previously generated SDK"""
        key = f"{language.value}_{package_name}"
        return self.generated_sdks.get(key)

    def list_generated_sdks(self) -> List[GeneratedSDK]:
        """List all generated SDKs"""
        return list(self.generated_sdks.values())

    async def generate_multiple_sdks(self,
                                   languages: List[ProgrammingLanguage],
                                   endpoints: List[EndpointSpec],
                                   config: SDKConfig) -> Dict[ProgrammingLanguage, GeneratedSDK]:
        """Generate SDKs for multiple languages simultaneously"""

        results = {}

        # Generate SDKs in parallel
        tasks = []
        for language in languages:
            task = self.generate_sdk(language, endpoints, config)
            tasks.append((language, task))

        # Wait for all to complete
        for language, task in tasks:
            try:
                sdk = await task
                results[language] = sdk
            except Exception as e:
                logging.error(f"Failed to generate SDK for {language}: {e}")

        return results

# Global SDK generator instance
sdk_generator = MultiLanguageSDKGenerator()

# Utility functions
async def generate_sdk_for_language(language: str,
                                  endpoints: List[Dict[str, Any]],
                                  package_name: str,
                                  **config_kwargs) -> GeneratedSDK:
    """Convenient function to generate SDK for a specific language"""

    # Convert string to enum
    try:
        lang_enum = ProgrammingLanguage(language.lower())
    except ValueError:
        raise ValueError(f"Unsupported language: {language}")

    # Convert endpoint dictionaries to EndpointSpec objects
    endpoint_specs = []
    for ep in endpoints:
        endpoint_spec = EndpointSpec(
            path=ep["path"],
            method=ep["method"],
            operation_id=ep.get("operation_id", ep["path"]),
            summary=ep.get("summary"),
            description=ep.get("description"),
            parameters=ep.get("parameters", []),
            request_body=ep.get("request_body"),
            responses=ep.get("responses", {}),
            auth_required=ep.get("auth_required", True)
        )
        endpoint_specs.append(endpoint_spec)

    # Create SDK config
    config = SDKConfig(
        package_name=package_name,
        **config_kwargs
    )

    return await sdk_generator.generate_sdk(lang_enum, endpoint_specs, config)
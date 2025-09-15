"""
Public API Documentation Generator
Generate beautiful, interactive API documentation pages
"""

import json
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime
from jinja2 import Template
from markdown import markdown
import re
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Session, relationship
from pydantic import BaseModel, Field

from src.database import Base, get_db

class PublicDocumentation(Base):
    """Database model for public API documentation"""
    __tablename__ = "public_docs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Documentation details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), default="1.0.0")
    base_url = Column(String(500))
    
    # OpenAPI spec
    openapi_spec = Column(JSON)
    
    # Customization
    theme = Column(String(50), default="default")  # default, dark, minimal, corporate
    logo_url = Column(String(500))
    favicon_url = Column(String(500))
    custom_css = Column(Text)
    custom_js = Column(Text)
    
    # Authentication docs
    auth_description = Column(Text)
    auth_examples = Column(JSON)
    
    # Additional sections
    getting_started = Column(Text)  # Markdown
    tutorials = Column(JSON)  # List of tutorial objects
    code_examples = Column(JSON)  # Language-specific examples
    sdks = Column(JSON)  # SDK download links

    # Public hosting
    subdomain = Column(String(255), unique=True)  # docs.streamapi.dev/subdomain
    custom_domain = Column(String(255))  # custom.com
    is_public = Column(Boolean, default=False)
    analytics_id = Column(String(100))  # Google Analytics ID

    # SEO optimization
    meta_title = Column(String(255))
    meta_description = Column(String(500))
    meta_keywords = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Access control
    is_public_orig = Column(Boolean, default=True)
    requires_auth = Column(Boolean, default=False)

class DocumentationGenerator:
    """Generates public API documentation"""

    def __init__(self):
        self.template = self._get_html_template()

    def generate_html_docs(self, docs: PublicDocumentation) -> str:
        """Generate HTML documentation"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{docs.title or 'API Documentation'}</title>
    <meta name="description" content="{docs.description or 'API Documentation'}">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .endpoints {{ margin-top: 40px; }}
        .endpoint {{ background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 8px; }}
        .method {{ display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }}
        .get {{ background: #28a745; }}
        .post {{ background: #007bff; }}
        .put {{ background: #ffc107; color: #000; }}
        .delete {{ background: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{docs.title or 'API Documentation'}</h1>
            <p>{docs.description or 'API Documentation'}</p>
            <p>Version: {docs.version or '1.0.0'}</p>
        </div>

        {self._generate_getting_started_section(docs)}
        {self._generate_auth_section(docs)}
        {self._generate_endpoints_section(docs)}
    </div>
</body>
</html>
        """

    def _generate_getting_started_section(self, docs: PublicDocumentation) -> str:
        """Generate getting started section"""
        if not docs.getting_started:
            return ""

        return f"""
        <div class="section">
            <h2>Getting Started</h2>
            <div>{markdown(docs.getting_started) if docs.getting_started else ''}</div>
        </div>
        """

    def _generate_auth_section(self, docs: PublicDocumentation) -> str:
        """Generate authentication section"""
        if not docs.auth_description:
            return ""

        return f"""
        <div class="section">
            <h2>Authentication</h2>
            <p>{docs.auth_description}</p>
        </div>
        """

    def _generate_endpoints_section(self, docs: PublicDocumentation) -> str:
        """Generate endpoints section from OpenAPI spec"""
        if not docs.openapi_spec or 'paths' not in docs.openapi_spec:
            return ""

        endpoints_html = "<div class='endpoints'><h2>API Endpoints</h2>"

        for path, methods in docs.openapi_spec['paths'].items():
            for method, spec in methods.items():
                endpoints_html += f"""
                <div class="endpoint">
                    <div>
                        <span class="method {method.lower()}">{method.upper()}</span>
                        <strong>{path}</strong>
                    </div>
                    <p>{spec.get('summary', 'No description available')}</p>
                </div>
                """

        endpoints_html += "</div>"
        return endpoints_html

    def generate_sitemap(self, docs: PublicDocumentation) -> str:
        """Generate sitemap.xml"""
        base_url = f"https://docs.streamapi.dev/{docs.subdomain}"
        if docs.custom_domain:
            base_url = f"https://{docs.custom_domain}"

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}</loc>
        <lastmod>{docs.updated_at.isoformat()}</lastmod>
        <priority>1.0</priority>
    </url>
</urlset>"""

    def generate_robots_txt(self, docs: PublicDocumentation) -> str:
        """Generate robots.txt"""
        base_url = f"https://docs.streamapi.dev/{docs.subdomain}"
        if docs.custom_domain:
            base_url = f"https://{docs.custom_domain}"

        return f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml"""

    def _get_html_template(self) -> str:
        """Get HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <meta name="description" content="{{ description }}">
</head>
<body>
    {{ content }}
</body>
</html>
        """
    allowed_domains = Column(JSON, default=[])  # Domain whitelist
    
    # SEO
    meta_description = Column(Text)
    meta_keywords = Column(JSON)
    og_image = Column(String(500))
    
    # Analytics
    analytics_id = Column(String(100))  # Google Analytics, etc.
    
    # Publishing
    slug = Column(String(100), unique=True, index=True)
    custom_domain = Column(String(255))
    published_at = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", backref="public_docs")

class DocGenerator:
    """Generate beautiful API documentation"""
    
    def __init__(self):
        self.themes = self._load_themes()
    
    def _load_themes(self) -> Dict[str, str]:
        """Load documentation themes"""
        return {
            "default": self._get_default_theme(),
            "dark": self._get_dark_theme(),
            "minimal": self._get_minimal_theme(),
            "corporate": self._get_corporate_theme()
        }
    
    def generate_docs(self, doc_config: PublicDocumentation) -> str:
        """Generate HTML documentation from OpenAPI spec"""
        
        # Parse OpenAPI spec
        spec = doc_config.openapi_spec
        if isinstance(spec, str):
            spec = json.loads(spec)
        
        # Get theme
        theme = self.themes.get(doc_config.theme, self.themes["default"])
        
        # Generate HTML
        template = Template(theme)
        
        html = template.render(
            title=doc_config.title or spec.get("info", {}).get("title", "API Documentation"),
            description=doc_config.description or spec.get("info", {}).get("description", ""),
            version=doc_config.version or spec.get("info", {}).get("version", "1.0.0"),
            base_url=doc_config.base_url or spec.get("servers", [{}])[0].get("url", ""),
            logo_url=doc_config.logo_url,
            favicon_url=doc_config.favicon_url,
            custom_css=doc_config.custom_css,
            custom_js=doc_config.custom_js,
            endpoints=self._parse_endpoints(spec),
            models=self._parse_models(spec),
            auth_info=self._parse_auth(spec, doc_config),
            getting_started=markdown(doc_config.getting_started) if doc_config.getting_started else "",
            tutorials=doc_config.tutorials or [],
            code_examples=doc_config.code_examples or {},
            sdks=doc_config.sdks or [],
            meta_description=doc_config.meta_description,
            meta_keywords=doc_config.meta_keywords,
            og_image=doc_config.og_image,
            analytics_id=doc_config.analytics_id
        )
        
        return html
    
    def _parse_endpoints(self, spec: Dict) -> List[Dict]:
        """Parse endpoints from OpenAPI spec"""
        endpoints = []
        paths = spec.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "operationId": details.get("operationId", ""),
                        "tags": details.get("tags", []),
                        "parameters": self._parse_parameters(details.get("parameters", [])),
                        "requestBody": self._parse_request_body(details.get("requestBody", {})),
                        "responses": self._parse_responses(details.get("responses", {})),
                        "security": details.get("security", []),
                        "deprecated": details.get("deprecated", False)
                    }
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_parameters(self, parameters: List) -> List[Dict]:
        """Parse parameters from OpenAPI spec"""
        parsed = []
        for param in parameters:
            parsed.append({
                "name": param.get("name"),
                "in": param.get("in"),
                "description": param.get("description", ""),
                "required": param.get("required", False),
                "schema": param.get("schema", {}),
                "example": param.get("example")
            })
        return parsed
    
    def _parse_request_body(self, request_body: Dict) -> Dict:
        """Parse request body from OpenAPI spec"""
        if not request_body:
            return {}
        
        content = request_body.get("content", {})
        parsed = {
            "description": request_body.get("description", ""),
            "required": request_body.get("required", False),
            "content": {}
        }
        
        for content_type, schema_info in content.items():
            parsed["content"][content_type] = {
                "schema": schema_info.get("schema", {}),
                "example": schema_info.get("example"),
                "examples": schema_info.get("examples", {})
            }
        
        return parsed
    
    def _parse_responses(self, responses: Dict) -> Dict:
        """Parse responses from OpenAPI spec"""
        parsed = {}
        for status_code, response in responses.items():
            parsed[status_code] = {
                "description": response.get("description", ""),
                "content": {}
            }
            
            content = response.get("content", {})
            for content_type, schema_info in content.items():
                parsed[status_code]["content"][content_type] = {
                    "schema": schema_info.get("schema", {}),
                    "example": schema_info.get("example"),
                    "examples": schema_info.get("examples", {})
                }
        
        return parsed
    
    def _parse_models(self, spec: Dict) -> Dict:
        """Parse data models from OpenAPI spec"""
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        return schemas
    
    def _parse_auth(self, spec: Dict, doc_config: PublicDocumentation) -> Dict:
        """Parse authentication information"""
        components = spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        
        return {
            "schemes": security_schemes,
            "description": doc_config.auth_description,
            "examples": doc_config.auth_examples or {}
        }
    
    def _get_default_theme(self) -> str:
        """Get default documentation theme"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - API Documentation</title>
    <meta name="description" content="{{ meta_description or description }}">
    {% if meta_keywords %}
    <meta name="keywords" content="{{ meta_keywords|join(', ') }}">
    {% endif %}
    {% if og_image %}
    <meta property="og:image" content="{{ og_image }}">
    {% endif %}
    {% if favicon_url %}
    <link rel="icon" href="{{ favicon_url }}">
    {% endif %}
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Prism for syntax highlighting -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
    
    {% if custom_css %}
    <style>{{ custom_css }}</style>
    {% endif %}
    
    {% if analytics_id %}
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={{ analytics_id }}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', '{{ analytics_id }}');
    </script>
    {% endif %}
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="container mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-4">
                {% if logo_url %}
                <img src="{{ logo_url }}" alt="{{ title }}" class="h-8">
                {% endif %}
                <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
                <span class="text-sm text-gray-500">v{{ version }}</span>
            </div>
            <div class="flex items-center space-x-4">
                <span class="text-sm text-gray-600">Base URL: <code class="bg-gray-100 px-2 py-1 rounded">{{ base_url }}</code></span>
            </div>
        </div>
    </header>
    
    <!-- Main Content -->
    <div class="container mx-auto px-4 py-8">
        <div class="grid grid-cols-12 gap-8">
            <!-- Sidebar -->
            <aside class="col-span-3">
                <nav class="sticky top-8 space-y-2">
                    <a href="#introduction" class="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded">Introduction</a>
                    {% if getting_started %}
                    <a href="#getting-started" class="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded">Getting Started</a>
                    {% endif %}
                    <a href="#authentication" class="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded">Authentication</a>
                    <a href="#endpoints" class="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded">Endpoints</a>
                    {% for tag in endpoints|map(attribute='tags')|flatten|unique %}
                    <a href="#tag-{{ tag|lower|replace(' ', '-') }}" class="block px-4 py-2 pl-8 text-sm text-gray-600 hover:text-blue-600">{{ tag }}</a>
                    {% endfor %}
                    <a href="#models" class="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded">Models</a>
                    {% if sdks %}
                    <a href="#sdks" class="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded">SDKs</a>
                    {% endif %}
                </nav>
            </aside>
            
            <!-- Content -->
            <main class="col-span-9">
                <!-- Introduction -->
                <section id="introduction" class="mb-12">
                    <h2 class="text-3xl font-bold mb-4">Introduction</h2>
                    <div class="prose max-w-none">{{ description }}</div>
                </section>
                
                {% if getting_started %}
                <!-- Getting Started -->
                <section id="getting-started" class="mb-12">
                    <h2 class="text-3xl font-bold mb-4">Getting Started</h2>
                    <div class="prose max-w-none">{{ getting_started|safe }}</div>
                </section>
                {% endif %}
                
                <!-- Authentication -->
                <section id="authentication" class="mb-12">
                    <h2 class="text-3xl font-bold mb-4">Authentication</h2>
                    {% if auth_info.description %}
                    <div class="prose max-w-none mb-6">{{ auth_info.description }}</div>
                    {% endif %}
                    
                    {% for scheme_name, scheme in auth_info.schemes.items() %}
                    <div class="bg-white p-6 rounded-lg shadow mb-4">
                        <h3 class="text-xl font-semibold mb-2">{{ scheme_name }}</h3>
                        <p class="text-gray-600 mb-4">Type: <code class="bg-gray-100 px-2 py-1 rounded">{{ scheme.type }}</code></p>
                        {% if scheme.description %}
                        <p class="text-gray-700">{{ scheme.description }}</p>
                        {% endif %}
                    </div>
                    {% endfor %}
                </section>
                
                <!-- Endpoints -->
                <section id="endpoints" class="mb-12">
                    <h2 class="text-3xl font-bold mb-6">Endpoints</h2>
                    
                    {% for endpoint in endpoints %}
                    <div class="bg-white rounded-lg shadow mb-6 overflow-hidden">
                        <div class="px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center space-x-4">
                                    <span class="px-3 py-1 bg-white bg-opacity-20 rounded text-sm font-semibold">
                                        {{ endpoint.method }}
                                    </span>
                                    <code class="text-lg">{{ endpoint.path }}</code>
                                </div>
                                {% if endpoint.deprecated %}
                                <span class="px-3 py-1 bg-red-500 rounded text-sm">Deprecated</span>
                                {% endif %}
                            </div>
                            {% if endpoint.summary %}
                            <p class="mt-2 text-blue-100">{{ endpoint.summary }}</p>
                            {% endif %}
                        </div>
                        
                        <div class="p-6">
                            {% if endpoint.description %}
                            <div class="mb-6">
                                <h4 class="font-semibold mb-2">Description</h4>
                                <p class="text-gray-700">{{ endpoint.description }}</p>
                            </div>
                            {% endif %}
                            
                            {% if endpoint.parameters %}
                            <div class="mb-6">
                                <h4 class="font-semibold mb-2">Parameters</h4>
                                <table class="w-full">
                                    <thead>
                                        <tr class="border-b">
                                            <th class="text-left py-2">Name</th>
                                            <th class="text-left py-2">Type</th>
                                            <th class="text-left py-2">In</th>
                                            <th class="text-left py-2">Required</th>
                                            <th class="text-left py-2">Description</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for param in endpoint.parameters %}
                                        <tr class="border-b">
                                            <td class="py-2"><code>{{ param.name }}</code></td>
                                            <td class="py-2">{{ param.schema.type|default('string') }}</td>
                                            <td class="py-2">{{ param.in }}</td>
                                            <td class="py-2">
                                                {% if param.required %}
                                                <span class="text-red-500">Yes</span>
                                                {% else %}
                                                <span class="text-gray-400">No</span>
                                                {% endif %}
                                            </td>
                                            <td class="py-2 text-sm text-gray-600">{{ param.description }}</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                            {% endif %}
                            
                            {% if endpoint.requestBody.content %}
                            <div class="mb-6">
                                <h4 class="font-semibold mb-2">Request Body</h4>
                                {% for content_type, content in endpoint.requestBody.content.items() %}
                                <div class="mb-4">
                                    <p class="text-sm text-gray-600 mb-2">Content-Type: <code>{{ content_type }}</code></p>
                                    {% if content.example %}
                                    <pre><code class="language-json">{{ content.example|tojson(2) }}</code></pre>
                                    {% endif %}
                                </div>
                                {% endfor %}
                            </div>
                            {% endif %}
                            
                            <!-- Responses -->
                            <div class="mb-6">
                                <h4 class="font-semibold mb-2">Responses</h4>
                                {% for status_code, response in endpoint.responses.items() %}
                                <div class="mb-4 pl-4 border-l-4 border-gray-200">
                                    <div class="flex items-center space-x-2 mb-2">
                                        <span class="px-2 py-1 bg-{{ 'green' if status_code|int < 300 else 'yellow' if status_code|int < 400 else 'red' }}-100 text-{{ 'green' if status_code|int < 300 else 'yellow' if status_code|int < 400 else 'red' }}-800 rounded text-sm font-semibold">
                                            {{ status_code }}
                                        </span>
                                        <span class="text-gray-600">{{ response.description }}</span>
                                    </div>
                                    {% for content_type, content in response.content.items() %}
                                    {% if content.example %}
                                    <pre><code class="language-json">{{ content.example|tojson(2) }}</code></pre>
                                    {% endif %}
                                    {% endfor %}
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </section>
                
                <!-- Models -->
                <section id="models" class="mb-12">
                    <h2 class="text-3xl font-bold mb-6">Models</h2>
                    {% for model_name, model in models.items() %}
                    <div class="bg-white rounded-lg shadow mb-6 p-6">
                        <h3 class="text-xl font-semibold mb-4">{{ model_name }}</h3>
                        {% if model.description %}
                        <p class="text-gray-600 mb-4">{{ model.description }}</p>
                        {% endif %}
                        <pre><code class="language-json">{{ model|tojson(2) }}</code></pre>
                    </div>
                    {% endfor %}
                </section>
                
                {% if sdks %}
                <!-- SDKs -->
                <section id="sdks" class="mb-12">
                    <h2 class="text-3xl font-bold mb-6">SDKs & Libraries</h2>
                    <div class="grid grid-cols-3 gap-4">
                        {% for sdk in sdks %}
                        <a href="{{ sdk.url }}" class="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
                            <h3 class="font-semibold mb-2">{{ sdk.language }}</h3>
                            <p class="text-sm text-gray-600">{{ sdk.description }}</p>
                        </a>
                        {% endfor %}
                    </div>
                </section>
                {% endif %}
            </main>
        </div>
    </div>
    
    {% if custom_js %}
    <script>{{ custom_js }}</script>
    {% endif %}
    
    <script>
        // Initialize Prism
        Prism.highlightAll();
        
        // Smooth scrolling
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
        '''
    
    def _get_dark_theme(self) -> str:
        """Get dark theme (similar structure with dark colors)"""
        # Dark theme implementation
        return self._get_default_theme()  # Placeholder
    
    def _get_minimal_theme(self) -> str:
        """Get minimal theme"""
        return self._get_default_theme()  # Placeholder
    
    def _get_corporate_theme(self) -> str:
        """Get corporate theme"""
        return self._get_default_theme()  # Placeholder
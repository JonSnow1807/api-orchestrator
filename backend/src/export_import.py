"""
Export/Import module for API Orchestrator
Handles exporting artifacts in various formats and importing existing specs
"""

import json
import yaml
import zipfile
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import HTTPException, status


class ExportManager:
    """Manages export of artifacts in various formats"""

    SUPPORTED_FORMATS = ["json", "yaml", "postman", "markdown", "zip"]

    @staticmethod
    def export_openapi_spec(spec: Dict, format: str = "json") -> Any:
        """Export OpenAPI specification in requested format"""
        if format not in ExportManager.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}. Supported: {ExportManager.SUPPORTED_FORMATS}",
            )

        if format == "json":
            return json.dumps(spec, indent=2)

        elif format == "yaml":
            return yaml.dump(spec, default_flow_style=False, sort_keys=False)

        elif format == "postman":
            return ExportManager._convert_to_postman(spec)

        elif format == "markdown":
            return ExportManager._convert_to_markdown(spec)

        elif format == "zip":
            return ExportManager._create_zip_bundle(spec)

    @staticmethod
    def _convert_to_postman(openapi_spec: Dict) -> str:
        """Convert OpenAPI spec to Postman collection"""
        collection = {
            "info": {
                "name": openapi_spec.get("info", {}).get("title", "API Collection"),
                "description": openapi_spec.get("info", {}).get("description", ""),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        }

        # Get base URL from servers
        base_url = ""
        if "servers" in openapi_spec:
            base_url = openapi_spec["servers"][0].get("url", "")

        # Convert paths to Postman items
        paths = openapi_spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    item = {
                        "name": details.get("summary", f"{method.upper()} {path}"),
                        "request": {
                            "method": method.upper(),
                            "header": [],
                            "url": {
                                "raw": f"{base_url}{path}",
                                "host": [
                                    base_url.replace("http://", "").replace(
                                        "https://", ""
                                    )
                                ],
                                "path": path.strip("/").split("/"),
                            },
                            "description": details.get("description", ""),
                        },
                    }

                    # Add parameters
                    if "parameters" in details:
                        item["request"]["url"]["query"] = []
                        for param in details["parameters"]:
                            if param.get("in") == "query":
                                item["request"]["url"]["query"].append(
                                    {
                                        "key": param["name"],
                                        "value": "",
                                        "description": param.get("description", ""),
                                    }
                                )
                            elif param.get("in") == "header":
                                item["request"]["header"].append(
                                    {
                                        "key": param["name"],
                                        "value": "",
                                        "description": param.get("description", ""),
                                    }
                                )

                    # Add request body for POST/PUT/PATCH
                    if method in ["post", "put", "patch"] and "requestBody" in details:
                        content = details["requestBody"].get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            example = ExportManager._generate_example_from_schema(
                                schema
                            )
                            item["request"]["body"] = {
                                "mode": "raw",
                                "raw": json.dumps(example, indent=2),
                                "options": {"raw": {"language": "json"}},
                            }

                    collection["item"].append(item)

        return json.dumps(collection, indent=2)

    @staticmethod
    def _generate_example_from_schema(schema: Dict) -> Dict:
        """Generate example data from JSON schema"""
        if schema.get("type") == "object":
            example = {}
            properties = schema.get("properties", {})
            for key, prop in properties.items():
                example[key] = ExportManager._generate_example_from_schema(prop)
            return example
        elif schema.get("type") == "array":
            items = schema.get("items", {})
            return [ExportManager._generate_example_from_schema(items)]
        elif schema.get("type") == "string":
            return schema.get("example", "string")
        elif schema.get("type") == "number":
            return schema.get("example", 0)
        elif schema.get("type") == "boolean":
            return schema.get("example", True)
        else:
            return None

    @staticmethod
    def _convert_to_markdown(openapi_spec: Dict) -> str:
        """Convert OpenAPI spec to Markdown documentation"""
        md = []

        # Title and description
        info = openapi_spec.get("info", {})
        md.append(f"# {info.get('title', 'API Documentation')}\n")
        md.append(f"{info.get('description', '')}\n")
        md.append(f"**Version:** {info.get('version', '1.0.0')}\n")

        # Servers
        if "servers" in openapi_spec:
            md.append("\n## Servers\n")
            for server in openapi_spec["servers"]:
                md.append(
                    f"- {server.get('url', '')} - {server.get('description', '')}\n"
                )

        # Endpoints
        md.append("\n## Endpoints\n")
        paths = openapi_spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    md.append(f"\n### {method.upper()} `{path}`\n")

                    # Summary and description
                    if "summary" in details:
                        md.append(f"**{details['summary']}**\n")
                    if "description" in details:
                        md.append(f"\n{details['description']}\n")

                    # Parameters
                    if "parameters" in details:
                        md.append("\n#### Parameters\n")
                        md.append("| Name | In | Type | Required | Description |\n")
                        md.append("|------|-----|------|----------|-------------|\n")
                        for param in details["parameters"]:
                            md.append(
                                f"| {param.get('name', '')} | {param.get('in', '')} | "
                                f"{param.get('schema', {}).get('type', '')} | "
                                f"{'Yes' if param.get('required', False) else 'No'} | "
                                f"{param.get('description', '')} |\n"
                            )

                    # Request body
                    if "requestBody" in details:
                        md.append("\n#### Request Body\n")
                        content = details["requestBody"].get("content", {})
                        if "application/json" in content:
                            schema = content["application/json"].get("schema", {})
                            md.append("```json\n")
                            md.append(
                                json.dumps(
                                    ExportManager._generate_example_from_schema(schema),
                                    indent=2,
                                )
                            )
                            md.append("\n```\n")

                    # Responses
                    if "responses" in details:
                        md.append("\n#### Responses\n")
                        for code, response in details["responses"].items():
                            md.append(
                                f"- **{code}**: {response.get('description', '')}\n"
                            )

        # Schemas
        if "components" in openapi_spec and "schemas" in openapi_spec["components"]:
            md.append("\n## Schemas\n")
            for schema_name, schema in openapi_spec["components"]["schemas"].items():
                md.append(f"\n### {schema_name}\n")
                md.append("```json\n")
                md.append(json.dumps(schema, indent=2))
                md.append("\n```\n")

        return "".join(md)

    @staticmethod
    def _create_zip_bundle(
        spec: Dict, tests: Optional[List] = None, mock_server: Optional[Dict] = None
    ) -> bytes:
        """Create a ZIP bundle with all artifacts"""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add OpenAPI spec in multiple formats
            zip_file.writestr("openapi.json", json.dumps(spec, indent=2))
            zip_file.writestr("openapi.yaml", yaml.dump(spec, default_flow_style=False))
            zip_file.writestr(
                "documentation.md", ExportManager._convert_to_markdown(spec)
            )
            zip_file.writestr(
                "postman_collection.json", ExportManager._convert_to_postman(spec)
            )

            # Add tests if provided
            if tests:
                for i, test in enumerate(tests):
                    if isinstance(test, dict) and "code" in test:
                        framework = test.get("framework", "test")
                        ext = "py" if framework in ["pytest", "unittest"] else "js"
                        zip_file.writestr(f"tests/{framework}_{i}.{ext}", test["code"])

            # Add mock server if provided
            if mock_server:
                zip_file.writestr("mock_server/server.py", mock_server.get("code", ""))
                zip_file.writestr(
                    "mock_server/README.md", mock_server.get("readme", "")
                )
                zip_file.writestr(
                    "mock_server/requirements.txt", mock_server.get("requirements", "")
                )

            # Add README
            readme_content = f"""# API Orchestrator Export

Generated on: {datetime.now().isoformat()}

## Contents

- `openapi.json` - OpenAPI 3.0 specification (JSON format)
- `openapi.yaml` - OpenAPI 3.0 specification (YAML format)  
- `documentation.md` - Human-readable API documentation
- `postman_collection.json` - Postman collection for API testing
- `tests/` - Generated test suites
- `mock_server/` - Mock server implementation

## Usage

### Import into Postman
1. Open Postman
2. Click Import > Choose Files
3. Select `postman_collection.json`

### Use Mock Server
1. Navigate to `mock_server/`
2. Install requirements: `pip install -r requirements.txt`
3. Run: `python server.py`

### Run Tests
Navigate to `tests/` and run tests with appropriate framework.
"""
            zip_file.writestr("README.md", readme_content)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    @staticmethod
    def export_tests(tests: List[Dict], format: str = "zip") -> Any:
        """Export test suites"""
        if format == "json":
            return json.dumps(tests, indent=2)

        elif format == "zip":
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for test in tests:
                    framework = test.get("framework", "test")
                    name = test.get("name", f"test_{framework}")
                    code = test.get("code", "")

                    # Determine file extension
                    if framework in ["pytest", "unittest"]:
                        ext = "py"
                    elif framework in ["jest", "mocha"]:
                        ext = "js"
                    else:
                        ext = "txt"

                    zip_file.writestr(f"{name}.{ext}", code)

            zip_buffer.seek(0)
            return zip_buffer.getvalue()

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format for tests: {format}",
            )


class ImportManager:
    """Manages import of existing specifications and artifacts"""

    @staticmethod
    def import_openapi_spec(content: bytes, content_type: str) -> Dict:
        """Import OpenAPI specification from various formats"""
        try:
            if content_type == "application/json":
                return json.loads(content)

            elif content_type in ["application/yaml", "text/yaml"]:
                return yaml.safe_load(content)

            elif content_type == "application/zip":
                # Extract OpenAPI spec from ZIP
                with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                    # Look for OpenAPI spec files
                    for name in zip_file.namelist():
                        if name.endswith("openapi.json"):
                            with zip_file.open(name) as f:
                                return json.load(f)
                        elif name.endswith("openapi.yaml") or name.endswith(
                            "openapi.yml"
                        ):
                            with zip_file.open(name) as f:
                                return yaml.safe_load(f)

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No OpenAPI specification found in ZIP file",
                )

            else:
                # Try to parse as JSON first, then YAML
                try:
                    return json.loads(content)
                except Exception:
                    try:
                        return yaml.safe_load(content)
                    except Exception:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Unable to parse content as JSON or YAML",
                        )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to import specification: {str(e)}",
            )

    @staticmethod
    def validate_openapi_spec(spec: Dict) -> bool:
        """Validate that the imported content is a valid OpenAPI spec"""
        # Basic validation
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in spec:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid OpenAPI specification: missing '{field}' field",
                )

        # Check OpenAPI version
        version = spec.get("openapi", "")
        if not version.startswith("3."):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OpenAPI version: {version}. Only 3.x is supported",
            )

        return True

    @staticmethod
    def import_postman_collection(content: bytes) -> Dict:
        """Convert Postman collection to OpenAPI spec"""
        try:
            collection = json.loads(content)

            # Basic structure
            openapi_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": collection.get("info", {}).get("name", "Imported API"),
                    "description": collection.get("info", {}).get("description", ""),
                    "version": "1.0.0",
                },
                "paths": {},
            }

            # Convert Postman items to OpenAPI paths
            items = collection.get("item", [])
            for item in items:
                if "request" in item:
                    request = item["request"]
                    method = request.get("method", "GET").lower()
                    url = request.get("url", {})

                    # Extract path
                    path = "/" + "/".join(url.get("path", []))
                    if not path in openapi_spec["paths"]:
                        openapi_spec["paths"][path] = {}

                    # Create operation
                    operation = {
                        "summary": item.get("name", ""),
                        "description": request.get("description", ""),
                        "responses": {"200": {"description": "Successful response"}},
                    }

                    # Add parameters
                    if "query" in url:
                        operation["parameters"] = []
                        for param in url["query"]:
                            operation["parameters"].append(
                                {
                                    "name": param.get("key", ""),
                                    "in": "query",
                                    "description": param.get("description", ""),
                                    "schema": {"type": "string"},
                                }
                            )

                    # Add request body
                    if "body" in request and method in ["post", "put", "patch"]:
                        body = request["body"]
                        if body.get("mode") == "raw":
                            operation["requestBody"] = {
                                "content": {
                                    "application/json": {"schema": {"type": "object"}}
                                }
                            }

                    openapi_spec["paths"][path][method] = operation

            return openapi_spec

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to import Postman collection: {str(e)}",
            )

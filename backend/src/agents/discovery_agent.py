import ast
import re
from typing import List, Optional
from pathlib import Path

from src.core.orchestrator import APIEndpoint, AgentMessage


class DiscoveryAgent:
    """Agent responsible for discovering API endpoints in codebases"""

    def __init__(self):
        self.supported_frameworks = {
            "fastapi": self._parse_fastapi,
            "flask": self._parse_flask,
            "express": self._parse_express,
            "django": self._parse_django,
        }
        self.discovered_apis = []

    async def scan(self, source_path: str) -> List[APIEndpoint]:
        """Scan a directory or file for API endpoints"""
        self.discovered_apis = []
        path = Path(source_path)

        if path.is_file():
            await self._scan_file(path)
        elif path.is_dir():
            await self._scan_directory(path)
        else:
            raise ValueError(f"Path {source_path} not found")

        return self.discovered_apis

    async def _scan_directory(self, directory: Path):
        """Recursively scan directory for API definitions"""
        # Python files
        for py_file in directory.rglob("*.py"):
            if "venv" not in str(py_file) and "__pycache__" not in str(py_file):
                await self._scan_file(py_file)

        # JavaScript files
        for js_file in directory.rglob("*.js"):
            if "node_modules" not in str(js_file):
                await self._scan_file(js_file)

        # TypeScript files
        for ts_file in directory.rglob("*.ts"):
            if "node_modules" not in str(ts_file):
                await self._scan_file(ts_file)

    async def _scan_file(self, file_path: Path):
        """Scan individual file for API endpoints"""
        print(f"📄 Scanning: {file_path}")
        file_content = file_path.read_text(encoding="utf-8", errors="ignore")

        # Detect framework
        framework = self._detect_framework(file_content, file_path.suffix)
        print(f"  Framework detected: {framework}")

        if framework and framework in self.supported_frameworks:
            parser = self.supported_frameworks[framework]
            apis = parser(file_content, str(file_path))
            self.discovered_apis.extend(apis)
            print(f"  Found {len(apis)} endpoints")
        else:
            print(f"  No supported framework detected")

    def _detect_framework(self, content: str, file_extension: str) -> Optional[str]:
        """Detect which framework is being used"""
        if file_extension == ".py":
            if "from fastapi" in content or "import fastapi" in content:
                return "fastapi"
            elif "from flask" in content or "import flask" in content:
                return "flask"
            elif "from django" in content or "import django" in content:
                return "django"
        elif file_extension in [".js", ".ts"]:
            if "express" in content.lower() and "router" in content.lower():
                return "express"
        return None

    def _parse_fastapi(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Parse FastAPI endpoints"""
        endpoints = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # FIXED: Check for both FunctionDef AND AsyncFunctionDef
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Look for decorators
                    for decorator in node.decorator_list:
                        method = None
                        path = None

                        # Handle @app.get("/path") style decorators
                        if isinstance(decorator, ast.Call):
                            if hasattr(decorator.func, "attr"):
                                # This is app.method or router.method
                                method = decorator.func.attr

                                # Get the path argument - handle both Constant (Python 3.8+) and Str (older)
                                if decorator.args:
                                    if isinstance(decorator.args[0], ast.Constant):
                                        path = decorator.args[0].value
                                    elif hasattr(ast, "Str") and isinstance(
                                        decorator.args[0], ast.Str
                                    ):
                                        path = decorator.args[0].s

                        # Check if this is an HTTP method decorator
                        http_methods = [
                            "get",
                            "post",
                            "put",
                            "delete",
                            "patch",
                            "options",
                            "head",
                        ]
                        if method in http_methods and path is not None:
                            # Extract parameters from function signature
                            params = []
                            for arg in node.args.args:
                                if arg.arg not in ["self", "cls"]:
                                    params.append(
                                        {
                                            "name": arg.arg,
                                            "type": "string",
                                            "in": "query",
                                        }
                                    )

                            # Get docstring
                            docstring = ast.get_docstring(node)

                            endpoint = APIEndpoint(
                                path=path,
                                method=method.upper(),
                                handler_name=node.name,
                                parameters=params,
                                description=docstring,
                            )
                            endpoints.append(endpoint)
                            print(f"  ✓ Found: {method.upper()} {path} -> {node.name}")

        except SyntaxError as e:
            print(f"⚠️  Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")
            import traceback

            traceback.print_exc()

        return endpoints

    def _parse_flask(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Parse Flask endpoints with improved detection"""
        endpoints = []

        # Multiple patterns for Flask routes
        route_patterns = [
            (r'@app\.route\([\'"]([^\'"]+)[\'"](?:.*methods=\[([^\]]+)\])?\)', "route"),
            (
                r'@\w+\.route\([\'"]([^\'"]+)[\'"](?:.*methods=\[([^\]]+)\])?\)',
                "blueprint",
            ),
            (r'@app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', "method"),
        ]

        for pattern, pattern_type in route_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if pattern_type == "method":
                    method = match.group(1)
                    path = match.group(2)
                    methods_list = [method]
                else:
                    path = match.group(1)
                    methods = match.group(2) if match.group(2) else "'GET'"
                    methods = methods.replace("'", "").replace('"', "").replace(" ", "")
                    methods_list = methods.split(",")

                for method in methods_list:
                    endpoint = APIEndpoint(
                        path=path,
                        method=method.upper(),
                        handler_name=f"flask_handler_{path.replace('/', '_')}",
                        parameters=[],
                    )
                    endpoints.append(endpoint)
                    print(f"  ✓ Found Flask: {method.upper()} {path}")

        return endpoints

    def _parse_express(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Parse Express.js endpoints"""
        endpoints = []

        # Regex patterns for Express routes
        patterns = [
            r'app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
            r'router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                method = match.group(1)
                path = match.group(2)

                endpoint = APIEndpoint(
                    path=path,
                    method=method.upper(),
                    handler_name=f"express_handler_{path.replace('/', '_')}",
                    parameters=[],
                )
                endpoints.append(endpoint)
                print(f"  ✓ Found: {method.upper()} {path}")

        return endpoints

    def _parse_django(self, content: str, file_path: str) -> List[APIEndpoint]:
        """Parse Django URLs and views with improved detection"""
        endpoints = []

        # Check for Django REST Framework
        if "@api_view" in content:
            # Parse DRF function-based views
            api_view_pattern = r"@api_view\(\[([^\]]+)\]\)\s+def\s+(\w+)"
            matches = re.finditer(api_view_pattern, content)
            for match in matches:
                methods = (
                    match.group(1).replace("'", "").replace('"', "").replace(" ", "")
                )
                func_name = match.group(2)
                for method in methods.split(","):
                    endpoint = APIEndpoint(
                        path=f"/{func_name}/",
                        method=method.upper(),
                        handler_name=func_name,
                        parameters=[],
                    )
                    endpoints.append(endpoint)
                    print(f"  ✓ Found Django DRF: {method.upper()} /{func_name}/")

        # Look for url patterns
        patterns = [
            r'path\([\'"]([^\'"]+)[\'"]',
            r'url\(r?[\'"]\^?([^\'"\$]+)\$?[\'"]',
            r're_path\(r?[\'"]\^?([^\'"\$]+)\$?[\'"]',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                path = match.group(1)
                # Clean up regex patterns
                path = path.replace("(?P<", "{").replace(">[^/]+)", "}")
                path = path.replace("\\d+", "{id}")

                endpoint = APIEndpoint(
                    path=f"/{path}" if not path.startswith("/") else path,
                    method="GET",  # Default, will be refined with view analysis
                    handler_name=f"django_view_{path.replace('/', '_')}",
                    parameters=[],
                )
                endpoints.append(endpoint)
                print(f"  ✓ Found Django: GET {endpoint.path}")

        # Check for ViewSet or APIView classes
        class_pattern = r"class\s+(\w+)\(.*(?:ViewSet|APIView|View).*\):"
        class_matches = re.finditer(class_pattern, content)
        for class_match in class_matches:
            class_name = class_match.group(1)
            # Check for REST methods in the class
            rest_methods = [
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "list",
                "create",
                "retrieve",
                "update",
                "destroy",
            ]
            for method in rest_methods:
                if (
                    f"def {method}("
                    in content[class_match.start() : class_match.start() + 2000]
                ):
                    http_method = (
                        method.upper()
                        if method in ["get", "post", "put", "patch", "delete"]
                        else "GET"
                    )
                    endpoint = APIEndpoint(
                        path=f"/{class_name.lower()}/",
                        method=http_method,
                        handler_name=f"{class_name}.{method}",
                        parameters=[],
                    )
                    endpoints.append(endpoint)
                    print(
                        f"  ✓ Found Django Class: {http_method} /{class_name.lower()}/"
                    )

        return endpoints

    async def handle_message(self, message: AgentMessage):
        """Handle messages from other agents"""
        if message.action == "rescan":
            # Rescan requested path
            await self.scan(message.payload.get("path", "."))
        elif message.action == "get_endpoint_details":
            # Return details about specific endpoint
            message.payload.get("endpoint")
            # Implementation for getting specific endpoint details

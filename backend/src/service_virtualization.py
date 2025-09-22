"""
Service Virtualization / Advanced API Mocking
Mock entire API services without dependencies
Competitive with ReadyAPI's service virtualization
"""

import asyncio
import json
import re
import random
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from faker import Faker
from aiohttp import web

fake = Faker()


class MockBehavior(Enum):
    """Mock response behaviors"""

    STATIC = "static"  # Return static response
    DYNAMIC = "dynamic"  # Generate dynamic data
    STATEFUL = "stateful"  # Maintain state between calls
    CONDITIONAL = "conditional"  # Response based on conditions
    PROXY = "proxy"  # Proxy to real service
    CHAOS = "chaos"  # Chaos engineering mode
    RECORD = "record"  # Record real responses
    REPLAY = "replay"  # Replay recorded responses


@dataclass
class MockRule:
    """Rule for mock response generation"""

    path_pattern: str
    method: str
    behavior: MockBehavior
    response: Optional[Dict[str, Any]] = None
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    delay_ms: int = 0
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    state_key: Optional[str] = None
    proxy_url: Optional[str] = None
    chaos_config: Optional[Dict[str, Any]] = None

    def matches(self, method: str, path: str) -> bool:
        """Check if rule matches request"""
        if self.method != "*" and self.method.upper() != method.upper():
            return False

        pattern = self.path_pattern.replace("*", ".*").replace("{id}", r"[^/]+")
        return bool(re.match(f"^{pattern}$", path))


@dataclass
class VirtualService:
    """Virtual API service"""

    id: str
    name: str
    base_path: str
    port: int
    rules: List[MockRule] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    recordings: List[Dict[str, Any]] = field(default_factory=list)
    middleware: List[Callable] = field(default_factory=list)
    openapi_spec: Optional[Dict[str, Any]] = None
    is_running: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class ServiceVirtualizer:
    """Advanced service virtualization engine"""

    def __init__(self):
        self.services: Dict[str, VirtualService] = {}
        self.running_servers = {}
        self.state_store = {}
        self.recording_store = {}
        self.chaos_engine = ChaosEngine()

    async def create_virtual_service(
        self,
        name: str,
        openapi_spec: Optional[Dict[str, Any]] = None,
        port: Optional[int] = None,
    ) -> VirtualService:
        """Create a new virtual service"""

        service_id = str(uuid.uuid4())
        base_path = f"/mock/{name.lower().replace(' ', '-')}"

        if not port:
            port = self._find_available_port()

        service = VirtualService(
            id=service_id,
            name=name,
            base_path=base_path,
            port=port,
            openapi_spec=openapi_spec,
        )

        # Generate rules from OpenAPI spec if provided
        if openapi_spec:
            service.rules = self._generate_rules_from_spec(openapi_spec)

        self.services[service_id] = service
        return service

    def _generate_rules_from_spec(self, spec: Dict[str, Any]) -> List[MockRule]:
        """Generate mock rules from OpenAPI specification"""

        rules = []
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    rule = self._create_rule_from_operation(
                        path, method.upper(), operation, spec
                    )
                    rules.append(rule)

        return rules

    def _create_rule_from_operation(
        self, path: str, method: str, operation: Dict[str, Any], spec: Dict[str, Any]
    ) -> MockRule:
        """Create mock rule from OpenAPI operation"""

        # Get response schema
        responses = operation.get("responses", {})
        success_response = (
            responses.get("200") or responses.get("201") or responses.get("default", {})
        )

        # Generate mock data based on schema
        mock_data = None
        if "content" in success_response:
            content = success_response["content"]
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                mock_data = self._generate_mock_from_schema(schema, spec)

        # Determine behavior
        behavior = MockBehavior.DYNAMIC
        if method == "GET" and "{" in path:
            behavior = MockBehavior.STATEFUL  # For resource retrieval
        elif method in ["POST", "PUT"]:
            behavior = MockBehavior.STATEFUL  # For resource creation/update

        return MockRule(
            path_pattern=path.replace("{", "{").replace("}", "}"),
            method=method,
            behavior=behavior,
            response=mock_data,
            status_code=200 if method != "POST" else 201,
            headers={"Content-Type": "application/json"},
        )

    def _generate_mock_from_schema(
        self, schema: Dict[str, Any], spec: Dict[str, Any]
    ) -> Any:
        """Generate mock data from JSON schema"""

        if "$ref" in schema:
            # Resolve reference
            ref_path = schema["$ref"].split("/")
            resolved = spec
            for part in ref_path[1:]:  # Skip '#'
                resolved = resolved.get(part, {})
            schema = resolved

        schema_type = schema.get("type", "object")

        if schema_type == "object":
            result = {}
            properties = schema.get("properties", {})

            for prop_name, prop_schema in properties.items():
                result[prop_name] = self._generate_mock_from_schema(prop_schema, spec)

            return result

        elif schema_type == "array":
            items_schema = schema.get("items", {})
            # Generate 3-5 items
            return [
                self._generate_mock_from_schema(items_schema, spec)
                for _ in range(random.randint(3, 5))
            ]

        elif schema_type == "string":
            return self._generate_string_value(schema)

        elif schema_type == "integer":
            return random.randint(schema.get("minimum", 1), schema.get("maximum", 1000))

        elif schema_type == "number":
            return round(
                random.uniform(
                    schema.get("minimum", 0.0), schema.get("maximum", 1000.0)
                ),
                2,
            )

        elif schema_type == "boolean":
            return random.choice([True, False])

        else:
            return None

    def _generate_string_value(self, schema: Dict[str, Any]) -> str:
        """Generate string value based on schema"""

        # Check for enum
        if "enum" in schema:
            return random.choice(schema["enum"])

        # Check for format
        format_type = schema.get("format", "")

        if format_type == "date":
            return fake.date()
        elif format_type == "date-time":
            return fake.iso8601()
        elif format_type == "email":
            return fake.email()
        elif format_type == "uri" or format_type == "url":
            return fake.url()
        elif format_type == "uuid":
            return str(uuid.uuid4())
        elif format_type == "ipv4":
            return fake.ipv4()
        elif format_type == "ipv6":
            return fake.ipv6()

        # Check for pattern in property name
        if "example" in schema:
            return schema["example"]

        # Generate based on common patterns
        pattern = schema.get("pattern", "")
        if pattern:
            # Simple pattern matching
            if "phone" in pattern.lower():
                return fake.phone_number()
            elif "zip" in pattern.lower() or "postal" in pattern.lower():
                return fake.postcode()

        # Default string generation
        min_length = schema.get("minLength", 5)
        max_length = schema.get("maxLength", 20)
        return fake.text(max_nb_chars=random.randint(min_length, max_length))

    async def start_service(self, service_id: str):
        """Start a virtual service"""

        service = self.services.get(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        if service.is_running:
            return

        # Start mock server
        from aiohttp import web

        app = web.Application()

        # Add routes
        app.router.add_route("*", "/{path:.*}", self._create_handler(service))

        # Start server
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, "localhost", service.port)
        await site.start()

        self.running_servers[service_id] = runner
        service.is_running = True

        print(
            f"Virtual service '{service.name}' started at http://localhost:{service.port}{service.base_path}"
        )

    def _create_handler(self, service: VirtualService):
        """Create request handler for service"""

        async def handler(request):
            method = request.method
            path = request.path_qs

            # Remove base path
            if path.startswith(service.base_path):
                path = path[len(service.base_path) :]

            # Find matching rule
            for rule in service.rules:
                if rule.matches(method, path):
                    return await self._handle_with_rule(request, rule, service)

            # No matching rule - return 404
            return web.json_response({"error": "Not found", "path": path}, status=404)

        return handler

    async def _handle_with_rule(self, request, rule: MockRule, service: VirtualService):
        """Handle request with matching rule"""

        from aiohttp import web

        # Apply delay if configured
        if rule.delay_ms > 0:
            await asyncio.sleep(rule.delay_ms / 1000)

        # Handle based on behavior
        if rule.behavior == MockBehavior.STATIC:
            response_data = rule.response or {}

        elif rule.behavior == MockBehavior.DYNAMIC:
            response_data = self._generate_dynamic_response(rule, request)

        elif rule.behavior == MockBehavior.STATEFUL:
            response_data = await self._handle_stateful_response(rule, request, service)

        elif rule.behavior == MockBehavior.CONDITIONAL:
            response_data = self._evaluate_conditions(rule, request)

        elif rule.behavior == MockBehavior.PROXY:
            return await self._proxy_request(rule, request)

        elif rule.behavior == MockBehavior.CHAOS:
            return await self._chaos_response(rule, request)

        elif rule.behavior == MockBehavior.RECORD:
            return await self._record_and_forward(rule, request, service)

        elif rule.behavior == MockBehavior.REPLAY:
            response_data = self._replay_response(rule, request, service)

        else:
            response_data = {"message": "Mock response"}

        # Apply middleware
        for middleware in service.middleware:
            response_data = await middleware(request, response_data)

        return web.json_response(
            response_data, status=rule.status_code, headers=rule.headers
        )

    def _generate_dynamic_response(self, rule: MockRule, request) -> Dict[str, Any]:
        """Generate dynamic response data"""

        if rule.response:
            # Use template and fill with fake data
            return self._fill_template_with_fake_data(rule.response)

        # Generate based on common patterns
        path = request.path

        if "users" in path or "user" in path:
            return {
                "id": str(uuid.uuid4()),
                "name": fake.name(),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "address": {
                    "street": fake.street_address(),
                    "city": fake.city(),
                    "country": fake.country(),
                    "zip": fake.postcode(),
                },
                "created_at": fake.iso8601(),
            }
        elif "products" in path or "items" in path:
            return {
                "id": str(uuid.uuid4()),
                "name": fake.catch_phrase(),
                "description": fake.text(),
                "price": round(random.uniform(10, 1000), 2),
                "category": random.choice(["Electronics", "Clothing", "Food", "Books"]),
                "in_stock": random.choice([True, False]),
                "rating": round(random.uniform(1, 5), 1),
            }
        elif "orders" in path:
            return {
                "id": str(uuid.uuid4()),
                "customer_id": str(uuid.uuid4()),
                "items": [
                    {
                        "product_id": str(uuid.uuid4()),
                        "quantity": random.randint(1, 5),
                        "price": round(random.uniform(10, 100), 2),
                    }
                    for _ in range(random.randint(1, 5))
                ],
                "total": round(random.uniform(50, 500), 2),
                "status": random.choice(
                    ["pending", "processing", "shipped", "delivered"]
                ),
                "created_at": fake.iso8601(),
            }
        else:
            # Generic response
            return {
                "id": str(uuid.uuid4()),
                "data": fake.text(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _fill_template_with_fake_data(self, template: Any) -> Any:
        """Fill template with fake data"""

        if isinstance(template, dict):
            result = {}
            for key, value in template.items():
                if (
                    isinstance(value, str)
                    and value.startswith("{{")
                    and value.endswith("}}")
                ):
                    # Template variable
                    var_name = value[2:-2].strip()
                    result[key] = self._generate_fake_value(var_name)
                else:
                    result[key] = self._fill_template_with_fake_data(value)
            return result

        elif isinstance(template, list):
            return [self._fill_template_with_fake_data(item) for item in template]

        else:
            return template

    def _generate_fake_value(self, var_name: str) -> Any:
        """Generate fake value based on variable name"""

        var_lower = var_name.lower()

        if "id" in var_lower:
            return str(uuid.uuid4())
        elif "name" in var_lower:
            if "first" in var_lower:
                return fake.first_name()
            elif "last" in var_lower:
                return fake.last_name()
            else:
                return fake.name()
        elif "email" in var_lower:
            return fake.email()
        elif "phone" in var_lower:
            return fake.phone_number()
        elif "address" in var_lower:
            return fake.address()
        elif "city" in var_lower:
            return fake.city()
        elif "country" in var_lower:
            return fake.country()
        elif "date" in var_lower or "time" in var_lower:
            return fake.iso8601()
        elif "price" in var_lower or "amount" in var_lower:
            return round(random.uniform(10, 1000), 2)
        elif "quantity" in var_lower or "count" in var_lower:
            return random.randint(1, 100)
        elif "status" in var_lower:
            return random.choice(["active", "inactive", "pending"])
        elif "bool" in var_lower or "is_" in var_lower or "has_" in var_lower:
            return random.choice([True, False])
        else:
            return fake.word()

    async def _handle_stateful_response(
        self, rule: MockRule, request, service: VirtualService
    ) -> Dict[str, Any]:
        """Handle stateful mock response"""

        method = request.method
        path = request.path

        # Initialize state if needed
        if service.id not in self.state_store:
            self.state_store[service.id] = {}

        state = self.state_store[service.id]

        # Extract resource ID from path
        resource_id = self._extract_resource_id(path, rule.path_pattern)

        if method == "GET":
            if resource_id:
                # Get specific resource
                return state.get(resource_id, {"error": "Not found"})
            else:
                # List resources
                return {"items": list(state.values()), "total": len(state)}

        elif method == "POST":
            # Create new resource
            data = await request.json() if request.body_exists else {}
            new_id = str(uuid.uuid4())
            data["id"] = new_id
            data["created_at"] = datetime.utcnow().isoformat()
            state[new_id] = data
            return data

        elif method == "PUT" or method == "PATCH":
            # Update resource
            if resource_id and resource_id in state:
                data = await request.json() if request.body_exists else {}
                state[resource_id].update(data)
                state[resource_id]["updated_at"] = datetime.utcnow().isoformat()
                return state[resource_id]
            return {"error": "Not found"}

        elif method == "DELETE":
            # Delete resource
            if resource_id and resource_id in state:
                deleted = state.pop(resource_id)
                return {"message": "Deleted", "data": deleted}
            return {"error": "Not found"}

        return {"error": "Method not supported"}

    def _extract_resource_id(self, path: str, pattern: str) -> Optional[str]:
        """Extract resource ID from path"""

        # Convert pattern to regex
        regex_pattern = (
            pattern.replace("{id}", r"([^/]+)").replace("{", r"\{").replace("}", r"\}")
        )
        match = re.match(regex_pattern, path)

        if match and match.groups():
            return match.group(1)

        return None

    def _evaluate_conditions(self, rule: MockRule, request) -> Dict[str, Any]:
        """Evaluate conditional rules"""

        for condition in rule.conditions:
            if self._check_condition(condition, request):
                return condition.get("response", {})

        return rule.response or {"message": "No condition matched"}

    def _check_condition(self, condition: Dict[str, Any], request) -> bool:
        """Check if condition matches request"""

        # Check headers
        if "headers" in condition:
            for key, value in condition["headers"].items():
                if request.headers.get(key) != value:
                    return False

        # Check query parameters
        if "params" in condition:
            for key, value in condition["params"].items():
                if request.query.get(key) != value:
                    return False

        # Check body
        if "body" in condition and request.body_exists:
            body = asyncio.run(request.json())
            for key, value in condition["body"].items():
                if body.get(key) != value:
                    return False

        return True

    async def _proxy_request(self, rule: MockRule, request):
        """Proxy request to real service"""

        import aiohttp
        from aiohttp import web

        if not rule.proxy_url:
            return web.json_response({"error": "Proxy URL not configured"}, status=500)

        # Forward request
        async with aiohttp.ClientSession() as session:
            url = rule.proxy_url + request.path_qs

            async with session.request(
                method=request.method,
                url=url,
                headers=request.headers,
                data=await request.read() if request.body_exists else None,
            ) as response:
                body = await response.read()

                return web.Response(
                    body=body, status=response.status, headers=response.headers
                )

    async def _chaos_response(self, rule: MockRule, request):
        """Generate chaos engineering response"""

        from aiohttp import web

        chaos_config = rule.chaos_config or {}

        # Random failures
        failure_rate = chaos_config.get("failure_rate", 0.1)
        if random.random() < failure_rate:
            error_codes = chaos_config.get("error_codes", [500, 502, 503])
            return web.json_response(
                {"error": "Chaos failure"}, status=random.choice(error_codes)
            )

        # Random delays
        max_delay = chaos_config.get("max_delay_ms", 5000)
        delay = random.randint(0, max_delay)
        await asyncio.sleep(delay / 1000)

        # Malformed responses
        malform_rate = chaos_config.get("malform_rate", 0.05)
        if random.random() < malform_rate:
            return web.Response(text="Malformed response", status=200)

        # Normal response
        return web.json_response(rule.response or {"message": "Chaos success"})

    async def _record_and_forward(
        self, rule: MockRule, request, service: VirtualService
    ):
        """Record request and forward to real service"""

        # Forward request
        response = await self._proxy_request(rule, request)

        # Record interaction
        recording = {
            "timestamp": datetime.utcnow().isoformat(),
            "request": {
                "method": request.method,
                "path": request.path_qs,
                "headers": dict(request.headers),
                "body": await request.text() if request.body_exists else None,
            },
            "response": {
                "status": response.status,
                "headers": dict(response.headers),
                "body": response.text,
            },
        }

        service.recordings.append(recording)

        return response

    def _replay_response(
        self, rule: MockRule, request, service: VirtualService
    ) -> Dict[str, Any]:
        """Replay recorded response"""

        # Find matching recording
        for recording in service.recordings:
            req = recording["request"]
            if req["method"] == request.method and req["path"] == request.path_qs:
                return json.loads(recording["response"]["body"])

        return {"error": "No recording found"}

    def _find_available_port(self, start=3000, end=9000) -> int:
        """Find an available port"""

        import socket

        for port in range(start, end):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("localhost", port))
                    return port
                except OSError:
                    continue

        raise RuntimeError("No available ports")

    async def stop_service(self, service_id: str):
        """Stop a virtual service"""

        service = self.services.get(service_id)
        if not service or not service.is_running:
            return

        runner = self.running_servers.get(service_id)
        if runner:
            await runner.cleanup()
            del self.running_servers[service_id]

        service.is_running = False

    def export_recordings(self, service_id: str, format: str = "har") -> str:
        """Export service recordings"""

        service = self.services.get(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        if format == "har":
            # HTTP Archive format
            har = {
                "log": {
                    "version": "1.2",
                    "creator": {"name": "API Orchestrator", "version": "1.0"},
                    "entries": [],
                }
            }

            for recording in service.recordings:
                entry = {
                    "startedDateTime": recording["timestamp"],
                    "request": recording["request"],
                    "response": recording["response"],
                }
                har["log"]["entries"].append(entry)

            return json.dumps(har, indent=2)

        return json.dumps(service.recordings, indent=2)


class ChaosEngine:
    """Chaos engineering capabilities"""

    def __init__(self):
        self.scenarios = {
            "network_failure": self._network_failure,
            "high_latency": self._high_latency,
            "data_corruption": self._data_corruption,
            "resource_exhaustion": self._resource_exhaustion,
        }

    async def _network_failure(self, request):
        """Simulate network failure"""
        raise ConnectionError("Network failure")

    async def _high_latency(self, request):
        """Simulate high latency"""
        await asyncio.sleep(random.uniform(5, 30))

    async def _data_corruption(self, request):
        """Simulate data corruption"""
        return {"corrupted": "�����"}

    async def _resource_exhaustion(self, request):
        """Simulate resource exhaustion"""
        from aiohttp import web

        return web.json_response(
            {"error": "Resource exhausted"}, status=429, headers={"Retry-After": "60"}
        )


# Export for use
__all__ = [
    "ServiceVirtualizer",
    "VirtualService",
    "MockRule",
    "MockBehavior",
    "ChaosEngine",
]

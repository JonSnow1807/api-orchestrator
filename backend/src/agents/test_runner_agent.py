"""
Test Runner Agent - Executes API tests with assertions
Provides test execution, assertion validation, and result reporting
"""

import asyncio
import httpx
import json
import time
import re
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum

# Optional jsonpath support
try:
    from jsonpath_ng import parse

    HAS_JSONPATH = True
except ImportError:
    HAS_JSONPATH = False
    parse = None


class AssertionType(Enum):
    """Types of assertions supported"""

    STATUS_CODE = "status_code"
    RESPONSE_TIME = "response_time"
    BODY_CONTAINS = "body_contains"
    BODY_JSON_PATH = "body_json_path"
    HEADER_EXISTS = "header_exists"
    HEADER_VALUE = "header_value"
    BODY_SCHEMA = "body_schema"
    BODY_REGEX = "body_regex"
    BODY_NOT_CONTAINS = "body_not_contains"
    IS_JSON = "is_json"
    IS_XML = "is_xml"
    BODY_LENGTH = "body_length"


class TestStatus(Enum):
    """Test execution status"""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class Assertion:
    """Single assertion for a test"""

    def __init__(
        self,
        type: AssertionType,
        expected: Any,
        operator: str = "equals",
        description: str = "",
    ):
        self.type = type
        self.expected = expected
        self.operator = (
            operator  # equals, not_equals, greater_than, less_than, contains, regex
        )
        self.description = description
        self.actual = None
        self.passed = False
        self.error_message = None

    def evaluate(self, response: httpx.Response, response_time_ms: float) -> bool:
        """Evaluate assertion against response"""
        try:
            if self.type == AssertionType.STATUS_CODE:
                self.actual = response.status_code
                self.passed = self._compare(self.actual, self.expected)

            elif self.type == AssertionType.RESPONSE_TIME:
                self.actual = response_time_ms
                self.passed = self._compare(self.actual, self.expected)

            elif self.type == AssertionType.BODY_CONTAINS:
                self.actual = response.text
                self.passed = str(self.expected) in self.actual

            elif self.type == AssertionType.BODY_NOT_CONTAINS:
                self.actual = response.text
                self.passed = str(self.expected) not in self.actual

            elif self.type == AssertionType.BODY_JSON_PATH:
                # Parse JSON and evaluate JSONPath
                if not HAS_JSONPATH:
                    # Fallback to simple key access if jsonpath not available
                    try:
                        json_data = response.json()
                        path = self.expected.get("path", "")
                        # Simple path handling (e.g., "$.key" or "key")
                        key = path.replace("$.", "").replace("$", "")
                        if "." in key:
                            # Handle nested keys
                            keys = key.split(".")
                            value = json_data
                            for k in keys:
                                value = (
                                    value.get(k) if isinstance(value, dict) else None
                                )
                            self.actual = value
                        else:
                            self.actual = json_data.get(key) if key else json_data

                        expected_value = self.expected.get("value")
                        if expected_value is not None:
                            self.passed = self._compare(self.actual, expected_value)
                        else:
                            self.passed = self.actual is not None
                    except (json.JSONDecodeError, AttributeError):
                        self.passed = False
                        self.error_message = (
                            "Response is not valid JSON or path not found"
                        )
                else:
                    # Use jsonpath if available
                    try:
                        json_data = response.json()
                        jsonpath_expr = parse(self.expected.get("path", "$"))
                        matches = jsonpath_expr.find(json_data)

                        if matches:
                            self.actual = matches[0].value
                            expected_value = self.expected.get("value")
                            if expected_value is not None:
                                self.passed = self._compare(self.actual, expected_value)
                            else:
                                self.passed = True  # Path exists
                        else:
                            self.actual = None
                            self.passed = False
                            self.error_message = (
                                f"JSONPath '{self.expected.get('path')}' not found"
                            )
                    except json.JSONDecodeError:
                        self.passed = False
                        self.error_message = "Response is not valid JSON"

            elif self.type == AssertionType.HEADER_EXISTS:
                self.actual = self.expected in response.headers
                self.passed = self.actual

            elif self.type == AssertionType.HEADER_VALUE:
                header_name = self.expected.get("name")
                expected_value = self.expected.get("value")
                self.actual = response.headers.get(header_name)
                self.passed = self._compare(self.actual, expected_value)

            elif self.type == AssertionType.BODY_REGEX:
                self.actual = response.text
                pattern = re.compile(self.expected)
                self.passed = bool(pattern.search(self.actual))

            elif self.type == AssertionType.IS_JSON:
                try:
                    response.json()
                    self.actual = "valid JSON"
                    self.passed = True
                except Exception:
                    self.actual = "invalid JSON"
                    self.passed = False

            elif self.type == AssertionType.BODY_LENGTH:
                self.actual = len(response.text)
                self.passed = self._compare(self.actual, self.expected)

            if not self.passed and not self.error_message:
                self.error_message = (
                    f"Expected {self.operator} {self.expected}, got {self.actual}"
                )

        except Exception as e:
            self.passed = False
            self.error_message = f"Assertion error: {str(e)}"

        return self.passed

    def _compare(self, actual: Any, expected: Any) -> bool:
        """Compare values based on operator"""
        try:
            if self.operator == "equals":
                return actual == expected
            elif self.operator == "not_equals":
                return actual != expected
            elif self.operator == "greater_than":
                return float(actual) > float(expected)
            elif self.operator == "less_than":
                return float(actual) < float(expected)
            elif self.operator == "greater_or_equal":
                return float(actual) >= float(expected)
            elif self.operator == "less_or_equal":
                return float(actual) <= float(expected)
            elif self.operator == "contains":
                return str(expected) in str(actual)
            elif self.operator == "regex":
                return bool(re.match(str(expected), str(actual)))
            else:
                return actual == expected
        except Exception:
            return False


class TestCase:
    """Single test case with request and assertions"""

    def __init__(
        self,
        name: str,
        request: Dict[str, Any],
        assertions: List[Assertion] = None,
        setup_script: str = None,
        teardown_script: str = None,
    ):
        self.name = name
        self.request = request
        self.assertions = assertions or []
        self.setup_script = setup_script
        self.teardown_script = teardown_script
        self.status = TestStatus.PENDING
        self.response = None
        self.response_time_ms = 0
        self.error_message = None
        self.start_time = None
        self.end_time = None

    async def execute(
        self, environment: Dict[str, str] = None, timeout: int = 30
    ) -> Dict[str, Any]:
        """Execute the test case"""
        self.status = TestStatus.RUNNING
        self.start_time = datetime.utcnow()

        try:
            # Run setup script if provided
            if self.setup_script:
                exec(self.setup_script, {"environment": environment})

            # Prepare request with environment variables
            url = self._replace_variables(self.request.get("url", ""), environment)
            method = self.request.get("method", "GET")
            headers = self._replace_variables_dict(
                self.request.get("headers", {}), environment
            )
            params = self._replace_variables_dict(
                self.request.get("params", {}), environment
            )

            # Handle body
            body = self.request.get("body")
            json_body = None
            data = None

            if body:
                if isinstance(body, dict):
                    json_body = self._replace_variables_dict(body, environment)
                else:
                    data = self._replace_variables(str(body), environment)

            # Execute request
            async with httpx.AsyncClient(timeout=timeout) as client:
                start = time.time()
                self.response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_body,
                    data=data,
                )
                self.response_time_ms = (time.time() - start) * 1000

            # Run assertions
            all_passed = True
            for assertion in self.assertions:
                if not assertion.evaluate(self.response, self.response_time_ms):
                    all_passed = False

            self.status = TestStatus.PASSED if all_passed else TestStatus.FAILED

            # Run teardown script
            if self.teardown_script:
                exec(
                    self.teardown_script,
                    {"environment": environment, "response": self.response},
                )

        except Exception as e:
            self.status = TestStatus.ERROR
            self.error_message = str(e)

        self.end_time = datetime.utcnow()
        return self.get_result()

    def _replace_variables(self, text: str, environment: Dict[str, str]) -> str:
        """Replace {{variable}} with environment values"""
        if not environment or not text:
            return text

        import re

        pattern = r"\{\{(\w+)\}\}"

        def replacer(match):
            var_name = match.group(1)
            return str(environment.get(var_name, match.group(0)))

        return re.sub(pattern, replacer, str(text))

    def _replace_variables_dict(self, data: Dict, environment: Dict[str, str]) -> Dict:
        """Replace variables in dictionary"""
        if not data:
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._replace_variables(value, environment)
            elif isinstance(value, dict):
                result[key] = self._replace_variables_dict(value, environment)
            else:
                result[key] = value
        return result

    def get_result(self) -> Dict[str, Any]:
        """Get test result"""
        result = {
            "name": self.name,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (self.end_time - self.start_time).total_seconds() * 1000
            if self.end_time and self.start_time
            else 0,
            "assertions": [],
        }

        if self.error_message:
            result["error"] = self.error_message

        if self.response:
            result["response"] = {
                "status_code": self.response.status_code,
                "headers": dict(self.response.headers),
                "body": self.response.text[:1000],  # Limit body size
            }

        for assertion in self.assertions:
            result["assertions"].append(
                {
                    "type": assertion.type.value,
                    "expected": assertion.expected,
                    "actual": assertion.actual,
                    "operator": assertion.operator,
                    "passed": assertion.passed,
                    "error": assertion.error_message,
                    "description": assertion.description,
                }
            )

        return result


class TestSuite:
    """Collection of test cases to run together"""

    def __init__(self, name: str, tests: List[TestCase] = None):
        self.name = name
        self.tests = tests or []
        self.environment = {}
        self.setup_script = None
        self.teardown_script = None
        self.results = []
        self.start_time = None
        self.end_time = None

    async def run(
        self, environment: Dict[str, str] = None, parallel: bool = False
    ) -> Dict[str, Any]:
        """Run all tests in the suite"""
        self.start_time = datetime.utcnow()
        self.environment = environment or {}
        self.results = []

        # Run setup
        if self.setup_script:
            exec(self.setup_script, {"environment": self.environment})

        # Run tests
        if parallel:
            # Run tests in parallel
            tasks = [test.execute(self.environment) for test in self.tests]
            self.results = await asyncio.gather(*tasks)
        else:
            # Run tests sequentially
            for test in self.tests:
                result = await test.execute(self.environment)
                self.results.append(result)

                # Stop on failure if configured
                if test.status == TestStatus.ERROR:
                    break

        # Run teardown
        if self.teardown_script:
            exec(self.teardown_script, {"environment": self.environment})

        self.end_time = datetime.utcnow()
        return self.get_report()

    def get_report(self) -> Dict[str, Any]:
        """Get test suite report"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        errors = sum(1 for r in self.results if r["status"] == "error")
        skipped = sum(1 for r in self.results if r["status"] == "skipped")

        return {
            "name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (self.end_time - self.start_time).total_seconds() * 1000
            if self.end_time and self.start_time
            else 0,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "status": "passed" if failed == 0 and errors == 0 else "failed",
            "tests": self.results,
        }


class TestRunnerAgent:
    """Main test runner agent"""

    def __init__(self):
        self.test_suites = []
        self.history = []

    def create_assertion(
        self,
        type_str: str,
        expected: Any,
        operator: str = "equals",
        description: str = "",
    ) -> Assertion:
        """Create an assertion from string type"""
        assertion_type = AssertionType[type_str.upper()]
        return Assertion(assertion_type, expected, operator, description)

    def create_test_from_request(
        self,
        name: str,
        url: str,
        method: str = "GET",
        headers: Dict = None,
        body: Any = None,
        assertions: List[Dict] = None,
    ) -> TestCase:
        """Create a test case from request details"""
        request = {"url": url, "method": method, "headers": headers or {}, "body": body}

        # Convert assertion dicts to Assertion objects
        assertion_objects = []
        if assertions:
            for a in assertions:
                assertion = self.create_assertion(
                    a.get("type", "STATUS_CODE"),
                    a.get("expected"),
                    a.get("operator", "equals"),
                    a.get("description", ""),
                )
                assertion_objects.append(assertion)

        return TestCase(name, request, assertion_objects)

    async def run_single_test(
        self, test: TestCase, environment: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Run a single test case"""
        result = await test.execute(environment)
        self.history.append(result)
        return result

    async def run_suite(
        self,
        suite: TestSuite,
        environment: Dict[str, str] = None,
        parallel: bool = False,
    ) -> Dict[str, Any]:
        """Run a test suite"""
        report = await suite.run(environment, parallel)
        self.history.append(report)
        return report

    def create_default_assertions(self, expected_status: int = 200) -> List[Assertion]:
        """Create default assertions for a test"""
        return [
            Assertion(
                AssertionType.STATUS_CODE,
                expected_status,
                "equals",
                "Status code should be " + str(expected_status),
            ),
            Assertion(
                AssertionType.RESPONSE_TIME,
                2000,
                "less_than",
                "Response time should be under 2 seconds",
            ),
            Assertion(
                AssertionType.IS_JSON, True, "equals", "Response should be valid JSON"
            ),
        ]

    def generate_postman_assertions(self, postman_tests: str) -> List[Assertion]:
        """Convert Postman test scripts to assertions"""
        assertions = []

        # Parse common Postman test patterns
        patterns = [
            (r"pm\.response\.to\.have\.status\((\d+)\)", AssertionType.STATUS_CODE),
            (r"pm\.response\.to\.be\.json", AssertionType.IS_JSON),
            (
                r'pm\.expect\(pm\.response\.text\(\)\)\.to\.include\(["\'](.+?)["\']\)',
                AssertionType.BODY_CONTAINS,
            ),
            (
                r'pm\.response\.to\.have\.header\(["\'](.+?)["\']\)',
                AssertionType.HEADER_EXISTS,
            ),
        ]

        for pattern, assertion_type in patterns:
            matches = re.findall(pattern, postman_tests)
            for match in matches:
                if assertion_type == AssertionType.STATUS_CODE:
                    assertions.append(Assertion(assertion_type, int(match)))
                elif assertion_type == AssertionType.IS_JSON:
                    assertions.append(Assertion(assertion_type, True))
                elif assertion_type == AssertionType.BODY_CONTAINS:
                    assertions.append(Assertion(assertion_type, match))
                elif assertion_type == AssertionType.HEADER_EXISTS:
                    assertions.append(Assertion(assertion_type, match))

        return assertions if assertions else self.create_default_assertions()

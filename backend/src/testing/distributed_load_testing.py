"""
Distributed Load Testing System
Enterprise-grade load testing for API Orchestrator with comprehensive scenarios
"""

import asyncio
import aiohttp
import time
import json
import statistics
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random
import uuid
from pathlib import Path
import psutil
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class LoadTestConfig:
    """Load test configuration"""

    base_url: str = "http://localhost:8000"
    concurrent_users: int = 100
    test_duration_seconds: int = 300  # 5 minutes
    ramp_up_time_seconds: int = 60
    scenarios: List[str] = field(
        default_factory=lambda: [
            "api_discovery",
            "spec_generation",
            "test_generation",
            "mock_server",
            "ai_collaboration",
            "security_audit",
        ]
    )

    # Rate limiting
    requests_per_second: int = 1000
    max_response_time_ms: int = 5000
    success_rate_threshold: float = 0.95

    # Resource monitoring
    monitor_resources: bool = True
    cpu_threshold: float = 80.0
    memory_threshold: float = 80.0

    # Data generation
    api_endpoints_per_test: int = 50
    test_files_per_endpoint: int = 10


@dataclass
class LoadTestResult:
    """Load test result metrics"""

    scenario: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    error_types: Dict[str, int] = field(default_factory=dict)
    throughput_rps: float = 0.0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None


class ResourceMonitor:
    """System resource monitoring during load tests"""

    def __init__(self):
        self.cpu_usage = []
        self.memory_usage = []
        self.is_monitoring = False

    async def start_monitoring(self, interval: float = 1.0):
        """Start resource monitoring"""
        self.is_monitoring = True
        while self.is_monitoring:
            self.cpu_usage.append(psutil.cpu_percent())
            self.memory_usage.append(psutil.virtual_memory().percent)
            await asyncio.sleep(interval)

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.is_monitoring = False

    def get_stats(self) -> Dict[str, Any]:
        """Get resource usage statistics"""
        if not self.cpu_usage or not self.memory_usage:
            return {}

        return {
            "cpu": {
                "avg": statistics.mean(self.cpu_usage),
                "max": max(self.cpu_usage),
                "min": min(self.cpu_usage),
            },
            "memory": {
                "avg": statistics.mean(self.memory_usage),
                "max": max(self.memory_usage),
                "min": min(self.memory_usage),
            },
        }


class DataGenerator:
    """Generate realistic test data for load testing"""

    @staticmethod
    def generate_project_data() -> Dict[str, Any]:
        """Generate realistic project data"""
        return {
            "name": f"LoadTest-Project-{uuid.uuid4().hex[:8]}",
            "description": f"Load testing project created at {datetime.utcnow()}",
            "source_type": random.choice(["directory", "url", "git"]),
            "source_path": f"/tmp/test-{uuid.uuid4().hex[:8]}",
            "apis": DataGenerator.generate_apis(),
        }

    @staticmethod
    def generate_apis(count: int = 20) -> List[Dict[str, Any]]:
        """Generate API endpoint data"""
        apis = []
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        endpoints = [
            "/users",
            "/users/{id}",
            "/projects",
            "/projects/{id}",
            "/apis",
            "/apis/{id}",
            "/tests",
            "/tests/{id}",
            "/auth/login",
            "/auth/logout",
            "/auth/refresh",
            "/admin/users",
            "/admin/stats",
            "/webhooks",
        ]

        for i in range(count):
            apis.append(
                {
                    "endpoint": random.choice(endpoints),
                    "method": random.choice(methods),
                    "description": f"Load test API endpoint {i}",
                    "parameters": DataGenerator.generate_parameters(),
                    "responses": DataGenerator.generate_responses(),
                }
            )

        return apis

    @staticmethod
    def generate_parameters() -> List[Dict[str, Any]]:
        """Generate API parameters"""
        param_types = ["string", "integer", "boolean", "array", "object"]
        return [
            {
                "name": f"param_{i}",
                "type": random.choice(param_types),
                "required": random.choice([True, False]),
                "description": f"Test parameter {i}",
            }
            for i in range(random.randint(1, 5))
        ]

    @staticmethod
    def generate_responses() -> Dict[str, Any]:
        """Generate API response schemas"""
        return {
            "200": {
                "description": "Success",
                "schema": {
                    "type": "object",
                    "properties": {"success": {"type": "boolean"}},
                },
            },
            "400": {
                "description": "Bad Request",
                "schema": {
                    "type": "object",
                    "properties": {"error": {"type": "string"}},
                },
            },
            "500": {
                "description": "Internal Server Error",
                "schema": {
                    "type": "object",
                    "properties": {"error": {"type": "string"}},
                },
            },
        }


class LoadTestScenario:
    """Base class for load test scenarios"""

    def __init__(self, session: aiohttp.ClientSession, config: LoadTestConfig):
        self.session = session
        self.config = config
        self.logger = logging.getLogger(f"LoadTest.{self.__class__.__name__}")

    async def execute(self) -> LoadTestResult:
        """Execute the load test scenario"""
        raise NotImplementedError

    async def authenticate(self) -> Optional[str]:
        """Get authentication token"""
        try:
            auth_data = {"email": "demo@streamapi.dev", "password": "Demo123!"}

            async with self.session.post(
                f"{self.config.base_url}/auth/login", json=auth_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("access_token")
        except Exception as e:
            self.logger.warning(f"Authentication failed: {e}")

        return None


class APIDiscoveryLoadTest(LoadTestScenario):
    """Load test for API discovery functionality"""

    async def execute(self) -> LoadTestResult:
        result = LoadTestResult(scenario="api_discovery")
        token = await self.authenticate()

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # Create projects and run discovery
        for i in range(self.config.concurrent_users):
            try:
                start_time = time.time()

                # Create project
                project_data = DataGenerator.generate_project_data()
                async with self.session.post(
                    f"{self.config.base_url}/api/v1/projects",
                    json=project_data,
                    headers=headers,
                ) as response:
                    response_time = time.time() - start_time
                    result.response_times.append(response_time * 1000)

                    if response.status == 200:
                        result.successful_requests += 1

                        # Run discovery on the project
                        project_id = (await response.json())["id"]
                        await self._run_discovery(project_id, headers, result)
                    else:
                        result.failed_requests += 1
                        result.error_types[f"status_{response.status}"] = (
                            result.error_types.get(f"status_{response.status}", 0) + 1
                        )

            except Exception as e:
                result.failed_requests += 1
                result.error_types[str(type(e).__name__)] = (
                    result.error_types.get(str(type(e).__name__), 0) + 1
                )

        result.total_requests = result.successful_requests + result.failed_requests
        result.end_time = datetime.utcnow()

        return result

    async def _run_discovery(
        self, project_id: str, headers: Dict[str, str], result: LoadTestResult
    ):
        """Run API discovery on a project"""
        try:
            start_time = time.time()

            async with self.session.post(
                f"{self.config.base_url}/api/v1/projects/{project_id}/discover",
                headers=headers,
            ) as response:
                response_time = time.time() - start_time
                result.response_times.append(response_time * 1000)

                if response.status == 200:
                    result.successful_requests += 1
                else:
                    result.failed_requests += 1

        except Exception:
            result.failed_requests += 1


class AICollaborationLoadTest(LoadTestScenario):
    """Load test for AI agent collaboration"""

    async def execute(self) -> LoadTestResult:
        result = LoadTestResult(scenario="ai_collaboration")
        token = await self.authenticate()

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # Test different collaboration modes
        collaboration_modes = ["swarm", "parallel", "hierarchical", "adaptive"]

        for mode in collaboration_modes:
            for i in range(self.config.concurrent_users // len(collaboration_modes)):
                try:
                    start_time = time.time()

                    collaboration_data = {
                        "mode": mode,
                        "agents": ["discovery", "spec_generator", "test_generator"],
                        "task": f"Process load test scenario {i}",
                        "parameters": {
                            "concurrent_tasks": random.randint(5, 15),
                            "timeout": 30,
                        },
                    }

                    async with self.session.post(
                        f"{self.config.base_url}/api/v1/ai/collaborate",
                        json=collaboration_data,
                        headers=headers,
                    ) as response:
                        response_time = time.time() - start_time
                        result.response_times.append(response_time * 1000)

                        if response.status == 200:
                            result.successful_requests += 1
                        else:
                            result.failed_requests += 1
                            result.error_types[f"status_{response.status}"] = (
                                result.error_types.get(f"status_{response.status}", 0)
                                + 1
                            )

                except Exception as e:
                    result.failed_requests += 1
                    result.error_types[str(type(e).__name__)] = (
                        result.error_types.get(str(type(e).__name__), 0) + 1
                    )

        result.total_requests = result.successful_requests + result.failed_requests
        result.end_time = datetime.utcnow()

        return result


class SecurityAuditLoadTest(LoadTestScenario):
    """Load test for security audit functionality"""

    async def execute(self) -> LoadTestResult:
        result = LoadTestResult(scenario="security_audit")
        token = await self.authenticate()

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        for i in range(self.config.concurrent_users):
            try:
                start_time = time.time()

                # Run comprehensive security audit
                audit_data = {
                    "scan_type": "comprehensive",
                    "include_patterns": ["**/*.py", "**/*.js", "**/*.ts"],
                    "exclude_patterns": ["**/node_modules/**", "**/.git/**"],
                    "severity_threshold": "medium",
                }

                async with self.session.post(
                    f"{self.config.base_url}/api/v1/security/audit",
                    json=audit_data,
                    headers=headers,
                ) as response:
                    response_time = time.time() - start_time
                    result.response_times.append(response_time * 1000)

                    if response.status == 200:
                        result.successful_requests += 1
                    else:
                        result.failed_requests += 1
                        result.error_types[f"status_{response.status}"] = (
                            result.error_types.get(f"status_{response.status}", 0) + 1
                        )

            except Exception as e:
                result.failed_requests += 1
                result.error_types[str(type(e).__name__)] = (
                    result.error_types.get(str(type(e).__name__), 0) + 1
                )

        result.total_requests = result.successful_requests + result.failed_requests
        result.end_time = datetime.utcnow()

        return result


class DistributedLoadTester:
    """Main distributed load testing orchestrator"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.resource_monitor = ResourceMonitor()
        self.logger = logging.getLogger("DistributedLoadTester")

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def run_load_test(self) -> Dict[str, LoadTestResult]:
        """Run comprehensive load test"""
        self.logger.info(
            f"Starting distributed load test with {self.config.concurrent_users} users"
        )

        # Start resource monitoring
        if self.config.monitor_resources:
            monitor_task = asyncio.create_task(self.resource_monitor.start_monitoring())

        results = {}

        try:
            # Create HTTP session with connection pooling
            timeout = aiohttp.ClientTimeout(
                total=self.config.max_response_time_ms / 1000
            )
            connector = aiohttp.TCPConnector(
                limit=self.config.concurrent_users * 2,
                limit_per_host=self.config.concurrent_users,
            )

            async with aiohttp.ClientSession(
                timeout=timeout, connector=connector
            ) as session:
                # Run scenarios in parallel
                scenario_tasks = []

                for scenario_name in self.config.scenarios:
                    scenario_class = self._get_scenario_class(scenario_name)
                    if scenario_class:
                        scenario = scenario_class(session, self.config)
                        task = asyncio.create_task(scenario.execute())
                        scenario_tasks.append((scenario_name, task))

                # Wait for all scenarios to complete
                for scenario_name, task in scenario_tasks:
                    try:
                        result = await task
                        result = self._calculate_metrics(result)
                        results[scenario_name] = result

                        self.logger.info(
                            f"Scenario {scenario_name} completed: "
                            f"{result.successful_requests}/{result.total_requests} successful, "
                            f"avg response time: {result.avg_response_time:.2f}ms"
                        )

                    except Exception as e:
                        self.logger.error(f"Scenario {scenario_name} failed: {e}")
                        results[scenario_name] = LoadTestResult(
                            scenario=scenario_name,
                            failed_requests=1,
                            error_types={"exception": 1},
                        )

        finally:
            # Stop resource monitoring
            if self.config.monitor_resources:
                self.resource_monitor.stop_monitoring()
                if "monitor_task" in locals():
                    monitor_task.cancel()
                    try:
                        await monitor_task
                    except asyncio.CancelledError:
                        pass

        # Add resource stats to results
        if self.config.monitor_resources:
            resource_stats = self.resource_monitor.get_stats()
            for result in results.values():
                if resource_stats:
                    result.cpu_usage = self.resource_monitor.cpu_usage.copy()
                    result.memory_usage = self.resource_monitor.memory_usage.copy()

        return results

    def _get_scenario_class(self, scenario_name: str) -> Optional[type]:
        """Get scenario class by name"""
        scenario_classes = {
            "api_discovery": APIDiscoveryLoadTest,
            "ai_collaboration": AICollaborationLoadTest,
            "security_audit": SecurityAuditLoadTest,
            # Add more scenarios as needed
        }
        return scenario_classes.get(scenario_name)

    def _calculate_metrics(self, result: LoadTestResult) -> LoadTestResult:
        """Calculate performance metrics"""
        if result.response_times:
            result.avg_response_time = statistics.mean(result.response_times)
            result.p95_response_time = self._percentile(result.response_times, 95)
            result.p99_response_time = self._percentile(result.response_times, 99)

        if result.end_time and result.start_time:
            duration = (result.end_time - result.start_time).total_seconds()
            result.throughput_rps = (
                result.total_requests / duration if duration > 0 else 0
            )

        return result

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]

    def generate_report(self, results: Dict[str, LoadTestResult]) -> Dict[str, Any]:
        """Generate comprehensive load test report"""
        report = {
            "test_configuration": {
                "concurrent_users": self.config.concurrent_users,
                "test_duration": self.config.test_duration_seconds,
                "scenarios": self.config.scenarios,
                "target_rps": self.config.requests_per_second,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "scenarios": {},
            "summary": {
                "total_requests": 0,
                "total_successful": 0,
                "total_failed": 0,
                "overall_success_rate": 0.0,
                "avg_response_time": 0.0,
                "total_throughput": 0.0,
            },
        }

        total_requests = 0
        total_successful = 0
        total_failed = 0
        all_response_times = []
        total_throughput = 0

        for scenario_name, result in results.items():
            scenario_report = {
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "success_rate": result.successful_requests / result.total_requests
                if result.total_requests > 0
                else 0,
                "avg_response_time_ms": result.avg_response_time,
                "p95_response_time_ms": result.p95_response_time,
                "p99_response_time_ms": result.p99_response_time,
                "throughput_rps": result.throughput_rps,
                "error_breakdown": result.error_types,
            }

            # Add resource usage if available
            if result.cpu_usage:
                scenario_report["resource_usage"] = {
                    "avg_cpu_percent": statistics.mean(result.cpu_usage),
                    "max_cpu_percent": max(result.cpu_usage),
                    "avg_memory_percent": statistics.mean(result.memory_usage)
                    if result.memory_usage
                    else 0,
                    "max_memory_percent": max(result.memory_usage)
                    if result.memory_usage
                    else 0,
                }

            report["scenarios"][scenario_name] = scenario_report

            # Aggregate totals
            total_requests += result.total_requests
            total_successful += result.successful_requests
            total_failed += result.failed_requests
            all_response_times.extend(result.response_times)
            total_throughput += result.throughput_rps

        # Calculate summary metrics
        report["summary"]["total_requests"] = total_requests
        report["summary"]["total_successful"] = total_successful
        report["summary"]["total_failed"] = total_failed
        report["summary"]["overall_success_rate"] = (
            total_successful / total_requests if total_requests > 0 else 0
        )
        report["summary"]["avg_response_time"] = (
            statistics.mean(all_response_times) if all_response_times else 0
        )
        report["summary"]["total_throughput"] = total_throughput

        # Performance assessment
        success_rate = report["summary"]["overall_success_rate"]
        avg_response_time = report["summary"]["avg_response_time"]

        if (
            success_rate >= self.config.success_rate_threshold
            and avg_response_time <= self.config.max_response_time_ms
        ):
            report["assessment"] = "PASS"
        else:
            report["assessment"] = "FAIL"
            report["issues"] = []

            if success_rate < self.config.success_rate_threshold:
                report["issues"].append(
                    f"Success rate {success_rate:.2%} below threshold {self.config.success_rate_threshold:.2%}"
                )

            if avg_response_time > self.config.max_response_time_ms:
                report["issues"].append(
                    f"Average response time {avg_response_time:.2f}ms above threshold {self.config.max_response_time_ms}ms"
                )

        return report


async def main():
    """Main function to run distributed load tests"""

    # Configure load test
    config = LoadTestConfig(
        base_url="http://localhost:8000",
        concurrent_users=50,  # Start with moderate load
        test_duration_seconds=180,  # 3 minutes
        scenarios=["api_discovery", "ai_collaboration", "security_audit"],
        requests_per_second=500,
        success_rate_threshold=0.90,
    )

    # Run load test
    tester = DistributedLoadTester(config)
    results = await tester.run_load_test()

    # Generate and save report
    report = tester.generate_report(results)

    # Save report to file
    report_file = Path("distributed_load_test_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print("DISTRIBUTED LOAD TEST RESULTS")
    print(f"{'='*60}")
    print(f"Assessment: {report['assessment']}")
    print(f"Total Requests: {report['summary']['total_requests']}")
    print(f"Success Rate: {report['summary']['overall_success_rate']:.2%}")
    print(f"Average Response Time: {report['summary']['avg_response_time']:.2f}ms")
    print(f"Total Throughput: {report['summary']['total_throughput']:.2f} RPS")

    if report["assessment"] == "FAIL" and "issues" in report:
        print(f"\nIssues identified:")
        for issue in report["issues"]:
            print(f"  - {issue}")

    print(f"\nDetailed report saved to: {report_file}")

    return report


if __name__ == "__main__":
    asyncio.run(main())

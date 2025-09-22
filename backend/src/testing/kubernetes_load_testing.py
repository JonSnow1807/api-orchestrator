"""
Kubernetes Distributed Load Testing
Advanced load testing for Kubernetes deployments with auto-scaling validation
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import subprocess
import yaml
from pathlib import Path


@dataclass
class KubernetesTestConfig:
    """Kubernetes load test configuration"""

    namespace: str = "api-orchestrator"
    service_name: str = "api-orchestrator-service"
    deployment_name: str = "api-orchestrator"

    # Load test parameters
    initial_replicas: int = 2
    max_replicas: int = 10
    target_cpu_utilization: int = 70

    # Test scenarios
    ramp_up_duration: int = 300  # 5 minutes
    plateau_duration: int = 600  # 10 minutes
    ramp_down_duration: int = 300  # 5 minutes

    # Load parameters
    concurrent_users_start: int = 10
    concurrent_users_peak: int = 1000
    requests_per_user: int = 100


@dataclass
class KubernetesMetrics:
    """Kubernetes cluster metrics"""

    timestamp: datetime
    pod_count: int
    cpu_usage_percent: float
    memory_usage_percent: float
    request_rate: float
    response_time_p95: float
    error_rate: float


class KubernetesManager:
    """Manage Kubernetes resources for load testing"""

    def __init__(self, config: KubernetesTestConfig):
        self.config = config
        self.logger = logging.getLogger("KubernetesManager")

    async def setup_hpa(self) -> bool:
        """Set up Horizontal Pod Autoscaler"""
        try:
            hpa_config = {
                "apiVersion": "autoscaling/v2",
                "kind": "HorizontalPodAutoscaler",
                "metadata": {
                    "name": f"{self.config.deployment_name}-hpa",
                    "namespace": self.config.namespace,
                },
                "spec": {
                    "scaleTargetRef": {
                        "apiVersion": "apps/v1",
                        "kind": "Deployment",
                        "name": self.config.deployment_name,
                    },
                    "minReplicas": self.config.initial_replicas,
                    "maxReplicas": self.config.max_replicas,
                    "metrics": [
                        {
                            "type": "Resource",
                            "resource": {
                                "name": "cpu",
                                "target": {
                                    "type": "Utilization",
                                    "averageUtilization": self.config.target_cpu_utilization,
                                },
                            },
                        },
                        {
                            "type": "Resource",
                            "resource": {
                                "name": "memory",
                                "target": {
                                    "type": "Utilization",
                                    "averageUtilization": 80,
                                },
                            },
                        },
                    ],
                },
            }

            # Write HPA config to temporary file
            hpa_file = Path("/tmp/hpa-config.yaml")
            with open(hpa_file, "w") as f:
                yaml.dump(hpa_config, f)

            # Apply HPA configuration
            result = subprocess.run(
                ["kubectl", "apply", "-f", str(hpa_file)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info("HPA configured successfully")
                return True
            else:
                self.logger.error(f"Failed to configure HPA: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error setting up HPA: {e}")
            return False

    async def get_pod_metrics(self) -> Optional[KubernetesMetrics]:
        """Get current pod metrics"""
        try:
            # Get pod count
            pod_result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-n",
                    self.config.namespace,
                    "-l",
                    f"app={self.config.deployment_name}",
                    "--field-selector=status.phase=Running",
                    "-o",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

            if pod_result.returncode != 0:
                return None

            pod_data = json.loads(pod_result.stdout)
            pod_count = len(pod_data.get("items", []))

            # Get resource usage from metrics server
            metrics_result = subprocess.run(
                [
                    "kubectl",
                    "top",
                    "pods",
                    "-n",
                    self.config.namespace,
                    "-l",
                    f"app={self.config.deployment_name}",
                    "--no-headers",
                ],
                capture_output=True,
                text=True,
            )

            cpu_usage = 0.0
            memory_usage = 0.0

            if metrics_result.returncode == 0:
                lines = metrics_result.stdout.strip().split("\n")
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                # Parse CPU (e.g., "123m" -> 123 millicores)
                                cpu_str = parts[1].rstrip("m")
                                cpu_usage += float(cpu_str) / 1000  # Convert to cores

                                # Parse Memory (e.g., "256Mi" -> MB)
                                memory_str = parts[2].rstrip("Mi")
                                memory_usage += float(memory_str)
                            except ValueError:
                                continue

            return KubernetesMetrics(
                timestamp=datetime.utcnow(),
                pod_count=pod_count,
                cpu_usage_percent=cpu_usage * 100 / pod_count if pod_count > 0 else 0,
                memory_usage_percent=memory_usage / (512 * pod_count) * 100
                if pod_count > 0
                else 0,  # Assuming 512Mi per pod
                request_rate=0.0,  # Will be filled by load tester
                response_time_p95=0.0,  # Will be filled by load tester
                error_rate=0.0,  # Will be filled by load tester
            )

        except Exception as e:
            self.logger.error(f"Error getting pod metrics: {e}")
            return None

    async def cleanup(self):
        """Clean up HPA resources"""
        try:
            subprocess.run(
                [
                    "kubectl",
                    "delete",
                    "hpa",
                    f"{self.config.deployment_name}-hpa",
                    "-n",
                    self.config.namespace,
                ],
                capture_output=True,
            )
            self.logger.info("HPA cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up HPA: {e}")


class KubernetesLoadTester:
    """Advanced load tester for Kubernetes environments"""

    def __init__(self, config: KubernetesTestConfig):
        self.config = config
        self.k8s_manager = KubernetesManager(config)
        self.metrics_history: List[KubernetesMetrics] = []
        self.logger = logging.getLogger("KubernetesLoadTester")

    async def run_distributed_load_test(self) -> Dict[str, Any]:
        """Run comprehensive distributed load test"""
        self.logger.info("Starting Kubernetes distributed load test")

        # Setup HPA
        if not await self.k8s_manager.setup_hpa():
            raise Exception("Failed to setup HPA")

        try:
            results = {
                "test_phases": {
                    "ramp_up": await self._run_ramp_up_phase(),
                    "plateau": await self._run_plateau_phase(),
                    "ramp_down": await self._run_ramp_down_phase(),
                },
                "scaling_analysis": self._analyze_scaling_behavior(),
                "performance_summary": self._generate_performance_summary(),
            }

            return results

        finally:
            await self.k8s_manager.cleanup()

    async def _run_ramp_up_phase(self) -> Dict[str, Any]:
        """Run ramp-up phase with gradually increasing load"""
        self.logger.info("Starting ramp-up phase")

        phase_results = {
            "duration_seconds": self.config.ramp_up_duration,
            "metrics": [],
            "scaling_events": [],
        }

        start_time = time.time()
        end_time = start_time + self.config.ramp_up_duration

        while time.time() < end_time:
            # Calculate current load based on progress
            progress = (time.time() - start_time) / self.config.ramp_up_duration
            current_users = int(
                self.config.concurrent_users_start
                + (
                    self.config.concurrent_users_peak
                    - self.config.concurrent_users_start
                )
                * progress
            )

            # Run load test with current user count
            load_result = await self._run_load_burst(current_users, duration=30)

            # Get Kubernetes metrics
            k8s_metrics = await self.k8s_manager.get_pod_metrics()
            if k8s_metrics:
                k8s_metrics.request_rate = load_result.get("request_rate", 0)
                k8s_metrics.response_time_p95 = load_result.get("p95_response_time", 0)
                k8s_metrics.error_rate = load_result.get("error_rate", 0)

                phase_results["metrics"].append(k8s_metrics)
                self.metrics_history.append(k8s_metrics)

                # Detect scaling events
                if len(self.metrics_history) > 1:
                    prev_metrics = self.metrics_history[-2]
                    if k8s_metrics.pod_count != prev_metrics.pod_count:
                        scaling_event = {
                            "timestamp": k8s_metrics.timestamp,
                            "from_pods": prev_metrics.pod_count,
                            "to_pods": k8s_metrics.pod_count,
                            "trigger": "cpu_utilization"
                            if k8s_metrics.cpu_usage_percent
                            > self.config.target_cpu_utilization
                            else "scale_down",
                        }
                        phase_results["scaling_events"].append(scaling_event)

            # Wait before next iteration
            await asyncio.sleep(10)

        return phase_results

    async def _run_plateau_phase(self) -> Dict[str, Any]:
        """Run plateau phase with sustained peak load"""
        self.logger.info("Starting plateau phase")

        phase_results = {
            "duration_seconds": self.config.plateau_duration,
            "metrics": [],
            "stability_analysis": {},
        }

        start_time = time.time()
        end_time = start_time + self.config.plateau_duration

        while time.time() < end_time:
            # Run load test with peak user count
            load_result = await self._run_load_burst(
                self.config.concurrent_users_peak, duration=60
            )

            # Get Kubernetes metrics
            k8s_metrics = await self.k8s_manager.get_pod_metrics()
            if k8s_metrics:
                k8s_metrics.request_rate = load_result.get("request_rate", 0)
                k8s_metrics.response_time_p95 = load_result.get("p95_response_time", 0)
                k8s_metrics.error_rate = load_result.get("error_rate", 0)

                phase_results["metrics"].append(k8s_metrics)
                self.metrics_history.append(k8s_metrics)

            # Wait before next iteration
            await asyncio.sleep(30)

        # Analyze stability
        if phase_results["metrics"]:
            pod_counts = [m.pod_count for m in phase_results["metrics"]]
            response_times = [m.response_time_p95 for m in phase_results["metrics"]]
            error_rates = [m.error_rate for m in phase_results["metrics"]]

            phase_results["stability_analysis"] = {
                "pod_count_stability": max(pod_counts) - min(pod_counts) <= 1,
                "avg_pod_count": sum(pod_counts) / len(pod_counts),
                "avg_response_time": sum(response_times) / len(response_times),
                "avg_error_rate": sum(error_rates) / len(error_rates),
                "max_error_rate": max(error_rates) if error_rates else 0,
            }

        return phase_results

    async def _run_ramp_down_phase(self) -> Dict[str, Any]:
        """Run ramp-down phase with gradually decreasing load"""
        self.logger.info("Starting ramp-down phase")

        phase_results = {
            "duration_seconds": self.config.ramp_down_duration,
            "metrics": [],
            "scale_down_events": [],
        }

        start_time = time.time()
        end_time = start_time + self.config.ramp_down_duration

        while time.time() < end_time:
            # Calculate current load based on progress
            progress = (time.time() - start_time) / self.config.ramp_down_duration
            current_users = int(
                self.config.concurrent_users_peak
                - (
                    self.config.concurrent_users_peak
                    - self.config.concurrent_users_start
                )
                * progress
            )

            # Run load test with current user count
            load_result = await self._run_load_burst(max(current_users, 1), duration=30)

            # Get Kubernetes metrics
            k8s_metrics = await self.k8s_manager.get_pod_metrics()
            if k8s_metrics:
                k8s_metrics.request_rate = load_result.get("request_rate", 0)
                k8s_metrics.response_time_p95 = load_result.get("p95_response_time", 0)
                k8s_metrics.error_rate = load_result.get("error_rate", 0)

                phase_results["metrics"].append(k8s_metrics)
                self.metrics_history.append(k8s_metrics)

                # Detect scale-down events
                if len(self.metrics_history) > 1:
                    prev_metrics = self.metrics_history[-2]
                    if k8s_metrics.pod_count < prev_metrics.pod_count:
                        scale_down_event = {
                            "timestamp": k8s_metrics.timestamp,
                            "from_pods": prev_metrics.pod_count,
                            "to_pods": k8s_metrics.pod_count,
                            "cpu_utilization": k8s_metrics.cpu_usage_percent,
                        }
                        phase_results["scale_down_events"].append(scale_down_event)

            # Wait before next iteration
            await asyncio.sleep(15)

        return phase_results

    async def _run_load_burst(
        self, concurrent_users: int, duration: int
    ) -> Dict[str, Any]:
        """Run a load burst with specified parameters"""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(limit=concurrent_users * 2)

            async with aiohttp.ClientSession(
                timeout=timeout, connector=connector
            ) as session:
                # Get service URL (assuming LoadBalancer or NodePort)
                service_url = await self._get_service_url()

                # Run concurrent requests
                tasks = []
                for _ in range(concurrent_users):
                    task = asyncio.create_task(self._make_request(session, service_url))
                    tasks.append(task)

                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

                # Analyze results
                successful_requests = sum(
                    1 for r in results if isinstance(r, dict) and r.get("success")
                )
                failed_requests = len(results) - successful_requests
                response_times = [
                    r.get("response_time", 0) for r in results if isinstance(r, dict)
                ]

                request_rate = (
                    len(results) / (end_time - start_time)
                    if end_time > start_time
                    else 0
                )
                error_rate = failed_requests / len(results) if results else 0
                p95_response_time = (
                    self._percentile(response_times, 95) if response_times else 0
                )

                return {
                    "request_rate": request_rate,
                    "error_rate": error_rate,
                    "p95_response_time": p95_response_time,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                }

        except Exception as e:
            self.logger.error(f"Error in load burst: {e}")
            return {"request_rate": 0, "error_rate": 1.0, "p95_response_time": 0}

    async def _get_service_url(self) -> str:
        """Get the service URL for load testing"""
        try:
            # Try to get LoadBalancer external IP
            result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "service",
                    self.config.service_name,
                    "-n",
                    self.config.namespace,
                    "-o",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                service_data = json.loads(result.stdout)

                # Check for LoadBalancer
                if service_data.get("spec", {}).get("type") == "LoadBalancer":
                    ingress = (
                        service_data.get("status", {})
                        .get("loadBalancer", {})
                        .get("ingress", [])
                    )
                    if ingress:
                        external_ip = ingress[0].get("ip") or ingress[0].get("hostname")
                        if external_ip:
                            port = (
                                service_data.get("spec", {})
                                .get("ports", [{}])[0]
                                .get("port", 80)
                            )
                            return f"http://{external_ip}:{port}"

                # Fallback to NodePort or ClusterIP with port-forward
                ports = service_data.get("spec", {}).get("ports", [])
                if ports:
                    port = ports[0].get("nodePort") or ports[0].get("port", 80)
                    return f"http://localhost:{port}"

        except Exception as e:
            self.logger.warning(f"Could not get service URL: {e}")

        # Default fallback
        return "http://localhost:8000"

    async def _make_request(
        self, session: aiohttp.ClientSession, base_url: str
    ) -> Dict[str, Any]:
        """Make a single HTTP request"""
        try:
            start_time = time.time()

            async with session.get(f"{base_url}/health") as response:
                response_time = time.time() - start_time

                return {
                    "success": response.status == 200,
                    "response_time": response_time * 1000,  # Convert to ms
                    "status_code": response.status,
                }

        except Exception as e:
            return {"success": False, "response_time": 0, "error": str(e)}

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        index = min(index, len(sorted_data) - 1)
        return sorted_data[index]

    def _analyze_scaling_behavior(self) -> Dict[str, Any]:
        """Analyze autoscaling behavior"""
        if not self.metrics_history:
            return {}

        pod_counts = [m.pod_count for m in self.metrics_history]
        cpu_usage = [m.cpu_usage_percent for m in self.metrics_history]
        response_times = [m.response_time_p95 for m in self.metrics_history]

        return {
            "min_pods": min(pod_counts),
            "max_pods": max(pod_counts),
            "avg_pods": sum(pod_counts) / len(pod_counts),
            "scaling_efficiency": {
                "scale_up_triggered": any(
                    cpu > self.config.target_cpu_utilization for cpu in cpu_usage
                ),
                "max_cpu_utilization": max(cpu_usage) if cpu_usage else 0,
                "avg_cpu_utilization": sum(cpu_usage) / len(cpu_usage)
                if cpu_usage
                else 0,
                "response_time_stability": max(response_times) - min(response_times)
                if response_times
                else 0,
            },
        }

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate overall performance summary"""
        if not self.metrics_history:
            return {}

        error_rates = [m.error_rate for m in self.metrics_history]
        response_times = [m.response_time_p95 for m in self.metrics_history]
        request_rates = [m.request_rate for m in self.metrics_history]

        return {
            "test_duration_minutes": len(self.metrics_history)
            * 0.5,  # Assuming 30s intervals
            "average_error_rate": sum(error_rates) / len(error_rates)
            if error_rates
            else 0,
            "max_error_rate": max(error_rates) if error_rates else 0,
            "average_response_time": sum(response_times) / len(response_times)
            if response_times
            else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "average_throughput": sum(request_rates) / len(request_rates)
            if request_rates
            else 0,
            "peak_throughput": max(request_rates) if request_rates else 0,
            "performance_grade": self._calculate_performance_grade(
                error_rates, response_times
            ),
        }

    def _calculate_performance_grade(
        self, error_rates: List[float], response_times: List[float]
    ) -> str:
        """Calculate overall performance grade"""
        if not error_rates or not response_times:
            return "INSUFFICIENT_DATA"

        avg_error_rate = sum(error_rates) / len(error_rates)
        avg_response_time = sum(response_times) / len(response_times)

        if (
            avg_error_rate < 0.01 and avg_response_time < 500
        ):  # <1% errors, <500ms response
            return "EXCELLENT"
        elif (
            avg_error_rate < 0.05 and avg_response_time < 1000
        ):  # <5% errors, <1s response
            return "GOOD"
        elif (
            avg_error_rate < 0.10 and avg_response_time < 2000
        ):  # <10% errors, <2s response
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"


async def main():
    """Main function for Kubernetes load testing"""
    config = KubernetesTestConfig(
        namespace="api-orchestrator",
        concurrent_users_start=10,
        concurrent_users_peak=500,
        ramp_up_duration=180,  # 3 minutes
        plateau_duration=300,  # 5 minutes
        ramp_down_duration=120,  # 2 minutes
    )

    tester = KubernetesLoadTester(config)

    try:
        results = await tester.run_distributed_load_test()

        # Save results
        with open("kubernetes_load_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("\n" + "=" * 60)
        print("KUBERNETES DISTRIBUTED LOAD TEST RESULTS")
        print("=" * 60)

        summary = results.get("performance_summary", {})
        print(f"Performance Grade: {summary.get('performance_grade', 'N/A')}")
        print(f"Average Error Rate: {summary.get('average_error_rate', 0)*100:.2f}%")
        print(f"Average Response Time: {summary.get('average_response_time', 0):.2f}ms")
        print(f"Peak Throughput: {summary.get('peak_throughput', 0):.2f} RPS")

        scaling = results.get("scaling_analysis", {})
        print(f"\nScaling Analysis:")
        print(f"  Min Pods: {scaling.get('min_pods', 'N/A')}")
        print(f"  Max Pods: {scaling.get('max_pods', 'N/A')}")
        print(
            f"  Avg CPU: {scaling.get('scaling_efficiency', {}).get('avg_cpu_utilization', 0):.2f}%"
        )

        print(f"\nDetailed results saved to: kubernetes_load_test_results.json")

    except Exception as e:
        print(f"Load test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())

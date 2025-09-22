#!/usr/bin/env python3
"""
Comprehensive Load Testing Suite Runner
Orchestrates all distributed load testing capabilities for API Orchestrator
"""

import asyncio
import json
import logging
import time
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# Import our testing modules
from src.testing.distributed_load_testing import DistributedLoadTester, LoadTestConfig
from src.testing.kubernetes_load_testing import KubernetesLoadTester, KubernetesTestConfig
from src.testing.chaos_engineering import ChaosEngineer, create_standard_experiment_suite

class ComprehensiveLoadTestSuite:
    """Comprehensive load testing suite orchestrator"""

    def __init__(self):
        self.logger = logging.getLogger("ComprehensiveLoadTestSuite")
        self.results = {
            "suite_start_time": datetime.utcnow(),
            "tests_run": [],
            "overall_results": {}
        }

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('load_test_suite.log'),
                logging.StreamHandler()
            ]
        )

    async def run_all_tests(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run all load testing scenarios"""
        self.logger.info("Starting comprehensive load testing suite")

        # Test configurations
        basic_config = LoadTestConfig(
            base_url=config.get("base_url", "http://localhost:8000"),
            concurrent_users=config.get("concurrent_users", 50),
            test_duration_seconds=config.get("test_duration", 180),
            scenarios=config.get("scenarios", ["api_discovery", "ai_collaboration", "security_audit"])
        )

        kubernetes_config = KubernetesTestConfig(
            namespace=config.get("k8s_namespace", "api-orchestrator"),
            concurrent_users_peak=config.get("k8s_peak_users", 500)
        )

        try:
            # 1. Basic Distributed Load Testing
            if config.get("run_basic_load_test", True):
                self.logger.info("Running basic distributed load tests")
                basic_results = await self._run_basic_load_test(basic_config)
                self.results["basic_load_test"] = basic_results

            # 2. Kubernetes Load Testing (if available)
            if config.get("run_kubernetes_test", False):
                self.logger.info("Running Kubernetes load tests")
                k8s_results = await self._run_kubernetes_test(kubernetes_config)
                self.results["kubernetes_load_test"] = k8s_results

            # 3. Chaos Engineering (if enabled)
            if config.get("run_chaos_test", False):
                self.logger.info("Running chaos engineering tests")
                chaos_results = await self._run_chaos_engineering()
                self.results["chaos_engineering"] = chaos_results

            # 4. Performance Baseline Verification
            if config.get("run_baseline_verification", True):
                self.logger.info("Running performance baseline verification")
                baseline_results = await self._run_baseline_verification(basic_config)
                self.results["baseline_verification"] = baseline_results

            # Generate comprehensive report
            self.results["suite_end_time"] = datetime.utcnow()
            comprehensive_report = self._generate_comprehensive_report()
            self.results["comprehensive_analysis"] = comprehensive_report

            return self.results

        except Exception as e:
            self.logger.error(f"Load testing suite failed: {e}")
            self.results["error"] = str(e)
            return self.results

    async def _run_basic_load_test(self, config: LoadTestConfig) -> Dict[str, Any]:
        """Run basic distributed load testing"""
        try:
            tester = DistributedLoadTester(config)
            results = await tester.run_load_test()
            report = tester.generate_report(results)

            self.logger.info(f"Basic load test completed - Assessment: {report.get('assessment', 'N/A')}")
            return report

        except Exception as e:
            self.logger.error(f"Basic load test failed: {e}")
            return {"error": str(e), "assessment": "FAILED"}

    async def _run_kubernetes_test(self, config: KubernetesTestConfig) -> Dict[str, Any]:
        """Run Kubernetes-specific load testing"""
        try:
            tester = KubernetesLoadTester(config)
            results = await tester.run_distributed_load_test()

            performance_grade = results.get("performance_summary", {}).get("performance_grade", "N/A")
            self.logger.info(f"Kubernetes load test completed - Grade: {performance_grade}")
            return results

        except Exception as e:
            self.logger.error(f"Kubernetes load test failed: {e}")
            return {"error": str(e), "performance_grade": "FAILED"}

    async def _run_chaos_engineering(self) -> Dict[str, Any]:
        """Run chaos engineering experiments"""
        try:
            engineer = ChaosEngineer()
            experiments = create_standard_experiment_suite()

            # Run a subset of experiments for safety
            safe_experiments = [exp for exp in experiments if exp.chaos_type.value in ["cpu_stress", "memory_stress"]]

            results = await engineer.run_experiment_suite(safe_experiments)

            resilience_score = results.get("suite_summary", {}).get("resilience_score", 0)
            self.logger.info(f"Chaos engineering completed - Resilience Score: {resilience_score:.1f}/100")
            return results

        except Exception as e:
            self.logger.error(f"Chaos engineering failed: {e}")
            return {"error": str(e), "resilience_score": 0}

    async def _run_baseline_verification(self, config: LoadTestConfig) -> Dict[str, Any]:
        """Verify performance against established baselines"""
        try:
            # Run a quick baseline test
            baseline_config = LoadTestConfig(
                base_url=config.base_url,
                concurrent_users=10,  # Light load
                test_duration_seconds=60,  # Short duration
                scenarios=["api_discovery"]  # Single scenario
            )

            tester = DistributedLoadTester(baseline_config)
            results = await tester.run_load_test()

            # Analyze against baselines
            baseline_analysis = self._analyze_baseline_performance(results)

            self.logger.info(f"Baseline verification completed")
            return baseline_analysis

        except Exception as e:
            self.logger.error(f"Baseline verification failed: {e}")
            return {"error": str(e), "baseline_met": False}

    def _analyze_baseline_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance against established baselines"""

        # Define performance baselines
        baselines = {
            "max_response_time_ms": 2000,
            "min_success_rate": 0.95,
            "min_throughput_rps": 10
        }

        analysis = {
            "baselines": baselines,
            "actual_performance": {},
            "baseline_met": True,
            "violations": []
        }

        # Extract performance metrics
        for scenario_name, scenario_data in results.items():
            if isinstance(scenario_data, dict) and "total_requests" in scenario_data:
                scenario_metrics = {
                    "response_time_ms": scenario_data.get("avg_response_time_ms", 0),
                    "success_rate": scenario_data.get("success_rate", 0),
                    "throughput_rps": scenario_data.get("throughput_rps", 0)
                }

                analysis["actual_performance"][scenario_name] = scenario_metrics

                # Check baseline violations
                if scenario_metrics["response_time_ms"] > baselines["max_response_time_ms"]:
                    violation = f"{scenario_name}: Response time {scenario_metrics['response_time_ms']:.2f}ms exceeds baseline {baselines['max_response_time_ms']}ms"
                    analysis["violations"].append(violation)
                    analysis["baseline_met"] = False

                if scenario_metrics["success_rate"] < baselines["min_success_rate"]:
                    violation = f"{scenario_name}: Success rate {scenario_metrics['success_rate']:.2%} below baseline {baselines['min_success_rate']:.2%}"
                    analysis["violations"].append(violation)
                    analysis["baseline_met"] = False

                if scenario_metrics["throughput_rps"] < baselines["min_throughput_rps"]:
                    violation = f"{scenario_name}: Throughput {scenario_metrics['throughput_rps']:.2f} RPS below baseline {baselines['min_throughput_rps']} RPS"
                    analysis["violations"].append(violation)
                    analysis["baseline_met"] = False

        return analysis

    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis across all test types"""

        report = {
            "executive_summary": {},
            "detailed_analysis": {},
            "recommendations": [],
            "risk_assessment": {},
            "deployment_readiness": {}
        }

        # Executive Summary
        tests_passed = 0
        total_tests = 0

        # Analyze basic load test
        if "basic_load_test" in self.results:
            total_tests += 1
            basic_result = self.results["basic_load_test"]
            if basic_result.get("assessment") == "PASS":
                tests_passed += 1

        # Analyze Kubernetes test
        if "kubernetes_load_test" in self.results:
            total_tests += 1
            k8s_result = self.results["kubernetes_load_test"]
            performance_grade = k8s_result.get("performance_summary", {}).get("performance_grade")
            if performance_grade in ["EXCELLENT", "GOOD"]:
                tests_passed += 1

        # Analyze chaos engineering
        if "chaos_engineering" in self.results:
            total_tests += 1
            chaos_result = self.results["chaos_engineering"]
            resilience_score = chaos_result.get("suite_summary", {}).get("resilience_score", 0)
            if resilience_score >= 70:
                tests_passed += 1

        # Analyze baseline verification
        if "baseline_verification" in self.results:
            total_tests += 1
            baseline_result = self.results["baseline_verification"]
            if baseline_result.get("baseline_met", False):
                tests_passed += 1

        # Executive Summary
        overall_score = (tests_passed / total_tests * 100) if total_tests > 0 else 0
        report["executive_summary"] = {
            "overall_score": overall_score,
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "recommendation": self._get_deployment_recommendation(overall_score)
        }

        # Risk Assessment
        risk_level = "LOW"
        if overall_score < 50:
            risk_level = "HIGH"
        elif overall_score < 75:
            risk_level = "MEDIUM"

        report["risk_assessment"] = {
            "risk_level": risk_level,
            "critical_issues": self._identify_critical_issues(),
            "mitigation_strategies": self._get_mitigation_strategies(risk_level)
        }

        # Recommendations
        report["recommendations"] = self._generate_deployment_recommendations()

        return report

    def _get_deployment_recommendation(self, score: float) -> str:
        """Get deployment recommendation based on overall score"""
        if score >= 90:
            return "READY_FOR_PRODUCTION"
        elif score >= 75:
            return "READY_WITH_MONITORING"
        elif score >= 60:
            return "NEEDS_IMPROVEMENTS"
        else:
            return "NOT_READY"

    def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues from all test results"""
        issues = []

        # Check basic load test issues
        if "basic_load_test" in self.results:
            basic_result = self.results["basic_load_test"]
            if basic_result.get("assessment") == "FAIL":
                if "issues" in basic_result:
                    issues.extend([f"Load Test: {issue}" for issue in basic_result["issues"]])

        # Check baseline violations
        if "baseline_verification" in self.results:
            baseline_result = self.results["baseline_verification"]
            if not baseline_result.get("baseline_met", True):
                violations = baseline_result.get("violations", [])
                issues.extend([f"Baseline: {violation}" for violation in violations])

        # Check chaos engineering failures
        if "chaos_engineering" in self.results:
            chaos_result = self.results["chaos_engineering"]
            resilience_score = chaos_result.get("suite_summary", {}).get("resilience_score", 100)
            if resilience_score < 70:
                issues.append(f"Resilience: Low resilience score ({resilience_score:.1f}/100)")

        return issues

    def _get_mitigation_strategies(self, risk_level: str) -> List[str]:
        """Get mitigation strategies based on risk level"""
        strategies = []

        if risk_level == "HIGH":
            strategies.extend([
                "Implement comprehensive monitoring and alerting",
                "Set up auto-scaling policies",
                "Deploy circuit breakers for external dependencies",
                "Implement graceful degradation mechanisms"
            ])
        elif risk_level == "MEDIUM":
            strategies.extend([
                "Enhance monitoring coverage",
                "Implement load balancing",
                "Set up automated recovery procedures"
            ])
        else:  # LOW
            strategies.extend([
                "Maintain current monitoring",
                "Regular performance testing",
                "Periodic chaos engineering exercises"
            ])

        return strategies

    def _generate_deployment_recommendations(self) -> List[str]:
        """Generate specific deployment recommendations"""
        recommendations = [
            "Implement comprehensive monitoring and alerting",
            "Set up horizontal pod autoscaling for Kubernetes deployments",
            "Configure proper resource limits and requests",
            "Implement health checks and readiness probes",
            "Set up distributed tracing for better observability",
            "Regular load testing in staging environment",
            "Implement feature flags for gradual rollouts"
        ]

        return recommendations

async def main():
    """Main function to run comprehensive load testing suite"""

    # Configuration for the test suite
    config = {
        "base_url": "http://localhost:8000",
        "concurrent_users": 50,
        "test_duration": 180,  # 3 minutes
        "scenarios": ["api_discovery", "ai_collaboration", "security_audit"],

        # Test selection
        "run_basic_load_test": True,
        "run_kubernetes_test": False,  # Requires Kubernetes cluster
        "run_chaos_test": False,       # Requires sudo permissions
        "run_baseline_verification": True,

        # Kubernetes settings (if enabled)
        "k8s_namespace": "api-orchestrator",
        "k8s_peak_users": 500
    }

    # Create and run test suite
    suite = ComprehensiveLoadTestSuite()

    try:
        print("🚀 Starting Comprehensive Load Testing Suite")
        print("=" * 60)

        results = await suite.run_all_tests(config)

        # Save detailed results
        results_file = Path("comprehensive_load_test_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Print summary
        print("\n" + "=" * 60)
        print("COMPREHENSIVE LOAD TESTING RESULTS")
        print("=" * 60)

        if "comprehensive_analysis" in results:
            analysis = results["comprehensive_analysis"]
            summary = analysis.get("executive_summary", {})

            print(f"Overall Score: {summary.get('overall_score', 0):.1f}/100")
            print(f"Tests Passed: {summary.get('tests_passed', 0)}/{summary.get('total_tests', 0)}")
            print(f"Deployment Recommendation: {summary.get('recommendation', 'N/A')}")

            risk = analysis.get("risk_assessment", {})
            print(f"Risk Level: {risk.get('risk_level', 'UNKNOWN')}")

            if risk.get("critical_issues"):
                print(f"\nCritical Issues:")
                for issue in risk["critical_issues"][:3]:  # Show top 3
                    print(f"  - {issue}")

        print(f"\nDetailed results saved to: {results_file}")

        # Return exit code based on results
        if "comprehensive_analysis" in results:
            recommendation = results["comprehensive_analysis"]["executive_summary"].get("recommendation")
            if recommendation in ["READY_FOR_PRODUCTION", "READY_WITH_MONITORING"]:
                return 0  # Success
            else:
                return 1  # Issues found
        else:
            return 2  # Test suite failed

    except KeyboardInterrupt:
        print("\nLoad testing interrupted by user")
        return 130

    except Exception as e:
        print(f"Load testing suite failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
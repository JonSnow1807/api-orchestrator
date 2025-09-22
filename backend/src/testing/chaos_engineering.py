"""
Chaos Engineering Test Suite
Advanced resilience testing for distributed API Orchestrator systems
"""

import asyncio
import aiohttp
import time
import json
import logging
import random
import subprocess
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import psutil
import signal
import os

class ChaosType(Enum):
    """Types of chaos engineering tests"""
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"
    NETWORK_LATENCY = "network_latency"
    NETWORK_PARTITION = "network_partition"
    DISK_IO_STRESS = "disk_io_stress"
    SERVICE_KILL = "service_kill"
    DATABASE_SLOW = "database_slow"
    EXTERNAL_API_FAILURE = "external_api_failure"

@dataclass
class ChaosExperiment:
    """Chaos engineering experiment configuration"""
    name: str
    chaos_type: ChaosType
    duration_seconds: int
    intensity: float  # 0.0 to 1.0
    target_components: List[str]
    success_criteria: Dict[str, Any]
    rollback_strategy: str

@dataclass
class ChaosResult:
    """Results from a chaos engineering experiment"""
    experiment_name: str
    chaos_type: ChaosType
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    metrics_before: Dict[str, Any] = field(default_factory=dict)
    metrics_during: Dict[str, Any] = field(default_factory=dict)
    metrics_after: Dict[str, Any] = field(default_factory=dict)
    observations: List[str] = field(default_factory=list)
    failure_points: List[str] = field(default_factory=list)
    recovery_time: Optional[float] = None

class SystemMetricsCollector:
    """Collect system metrics during chaos experiments"""

    @staticmethod
    async def collect_metrics() -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        try:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
                    "core_count": psutil.cpu_count()
                },
                "memory": {
                    "usage_percent": psutil.virtual_memory().percent,
                    "available_gb": psutil.virtual_memory().available / (1024**3),
                    "used_gb": psutil.virtual_memory().used / (1024**3)
                },
                "disk": {
                    "usage_percent": psutil.disk_usage('/').percent,
                    "free_gb": psutil.disk_usage('/').free / (1024**3),
                    "io_stats": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                },
                "network": {
                    "io_stats": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
                    "connections": len(psutil.net_connections())
                },
                "processes": {
                    "count": len(psutil.pids()),
                    "api_orchestrator_processes": SystemMetricsCollector._get_api_processes()
                }
            }
        except Exception as e:
            logging.error(f"Error collecting metrics: {e}")
            return {"error": str(e)}

    @staticmethod
    def _get_api_processes() -> List[Dict[str, Any]]:
        """Get API Orchestrator related processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower() or 'uvicorn' in proc.info['name'].lower():
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

class ChaosInducer:
    """Induce various types of chaos in the system"""

    def __init__(self):
        self.active_chaos: Dict[str, Any] = {}
        self.logger = logging.getLogger("ChaosInducer")

    async def induce_cpu_stress(self, intensity: float, duration: int) -> str:
        """Induce CPU stress"""
        chaos_id = f"cpu_stress_{int(time.time())}"

        # Use stress-ng if available, otherwise use Python CPU stress
        try:
            # Try to use stress-ng
            cmd = [
                "stress-ng",
                "--cpu", str(int(psutil.cpu_count() * intensity)),
                "--timeout", f"{duration}s",
                "--quiet"
            ]

            process = subprocess.Popen(cmd)
            self.active_chaos[chaos_id] = {
                "type": "cpu_stress",
                "process": process,
                "start_time": time.time()
            }

        except FileNotFoundError:
            # Fallback to Python CPU stress
            process = await self._python_cpu_stress(intensity, duration)
            self.active_chaos[chaos_id] = {
                "type": "cpu_stress",
                "process": process,
                "start_time": time.time()
            }

        return chaos_id

    async def induce_memory_stress(self, intensity: float, duration: int) -> str:
        """Induce memory stress"""
        chaos_id = f"memory_stress_{int(time.time())}"

        # Calculate memory to allocate (in MB)
        total_memory_gb = psutil.virtual_memory().total / (1024**3)
        memory_to_allocate = int(total_memory_gb * intensity * 1024)  # MB

        try:
            cmd = [
                "stress-ng",
                "--vm", "1",
                "--vm-bytes", f"{memory_to_allocate}M",
                "--timeout", f"{duration}s",
                "--quiet"
            ]

            process = subprocess.Popen(cmd)
            self.active_chaos[chaos_id] = {
                "type": "memory_stress",
                "process": process,
                "start_time": time.time()
            }

        except FileNotFoundError:
            # Fallback to Python memory stress
            process = await self._python_memory_stress(intensity, duration)
            self.active_chaos[chaos_id] = {
                "type": "memory_stress",
                "process": process,
                "start_time": time.time()
            }

        return chaos_id

    async def induce_network_latency(self, latency_ms: int, duration: int) -> str:
        """Induce network latency using tc (traffic control)"""
        chaos_id = f"network_latency_{int(time.time())}"

        try:
            # Add network latency
            subprocess.run([
                "sudo", "tc", "qdisc", "add", "dev", "lo", "root", "netem",
                "delay", f"{latency_ms}ms"
            ], check=True)

            self.active_chaos[chaos_id] = {
                "type": "network_latency",
                "interface": "lo",
                "start_time": time.time(),
                "duration": duration
            }

            # Schedule cleanup
            asyncio.create_task(self._cleanup_network_latency(chaos_id, duration))

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.warning(f"Could not induce network latency: {e}")
            chaos_id = None

        return chaos_id

    async def induce_service_kill(self, service_pattern: str) -> str:
        """Kill services matching pattern"""
        chaos_id = f"service_kill_{int(time.time())}"

        killed_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if service_pattern.lower() in proc.info['name'].lower() or \
                   any(service_pattern.lower() in arg.lower() for arg in proc.info['cmdline']):
                    proc.terminate()
                    killed_processes.append(proc.info['pid'])
                    self.logger.info(f"Terminated process {proc.info['pid']} ({proc.info['name']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        self.active_chaos[chaos_id] = {
            "type": "service_kill",
            "killed_processes": killed_processes,
            "start_time": time.time()
        }

        return chaos_id

    async def _python_cpu_stress(self, intensity: float, duration: int):
        """Python-based CPU stress (fallback)"""
        async def cpu_stress():
            end_time = time.time() + duration
            while time.time() < end_time:
                # Busy wait to consume CPU
                for _ in range(int(1000000 * intensity)):
                    pass
                await asyncio.sleep(0.01)  # Small yield to prevent complete lockup

        return asyncio.create_task(cpu_stress())

    async def _python_memory_stress(self, intensity: float, duration: int):
        """Python-based memory stress (fallback)"""
        async def memory_stress():
            memory_blocks = []
            block_size = 1024 * 1024  # 1MB blocks
            total_memory = psutil.virtual_memory().total
            target_memory = int(total_memory * intensity)
            blocks_needed = target_memory // block_size

            try:
                # Allocate memory
                for _ in range(blocks_needed):
                    memory_blocks.append(b'0' * block_size)

                # Hold memory for duration
                await asyncio.sleep(duration)

            finally:
                # Release memory
                memory_blocks.clear()

        return asyncio.create_task(memory_stress())

    async def _cleanup_network_latency(self, chaos_id: str, duration: int):
        """Clean up network latency after duration"""
        await asyncio.sleep(duration)
        try:
            subprocess.run([
                "sudo", "tc", "qdisc", "del", "dev", "lo", "root"
            ], check=True)
            self.logger.info(f"Cleaned up network latency for {chaos_id}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to cleanup network latency: {e}")

    async def stop_chaos(self, chaos_id: str):
        """Stop a specific chaos experiment"""
        if chaos_id not in self.active_chaos:
            return

        chaos_info = self.active_chaos[chaos_id]
        chaos_type = chaos_info["type"]

        try:
            if chaos_type in ["cpu_stress", "memory_stress"] and "process" in chaos_info:
                process = chaos_info["process"]
                if hasattr(process, 'terminate'):
                    process.terminate()
                elif hasattr(process, 'cancel'):
                    process.cancel()

            elif chaos_type == "network_latency":
                subprocess.run([
                    "sudo", "tc", "qdisc", "del", "dev", chaos_info["interface"], "root"
                ], check=True)

            del self.active_chaos[chaos_id]
            self.logger.info(f"Stopped chaos experiment {chaos_id}")

        except Exception as e:
            self.logger.error(f"Error stopping chaos {chaos_id}: {e}")

    async def stop_all_chaos(self):
        """Stop all active chaos experiments"""
        for chaos_id in list(self.active_chaos.keys()):
            await self.stop_chaos(chaos_id)

class ChaosEngineer:
    """Main chaos engineering orchestrator"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.chaos_inducer = ChaosInducer()
        self.metrics_collector = SystemMetricsCollector()
        self.logger = logging.getLogger("ChaosEngineer")

    async def run_experiment(self, experiment: ChaosExperiment) -> ChaosResult:
        """Run a single chaos engineering experiment"""
        self.logger.info(f"Starting chaos experiment: {experiment.name}")

        result = ChaosResult(
            experiment_name=experiment.name,
            chaos_type=experiment.chaos_type,
            start_time=datetime.utcnow()
        )

        try:
            # Collect baseline metrics
            result.metrics_before = await self.metrics_collector.collect_metrics()

            # Verify system health before chaos
            if not await self._verify_system_health():
                result.observations.append("System was unhealthy before chaos injection")
                return result

            # Inject chaos based on type
            chaos_id = await self._inject_chaos(experiment)

            if chaos_id:
                # Monitor system during chaos
                result.metrics_during = await self._monitor_during_chaos(experiment.duration_seconds)

                # Stop chaos
                await self.chaos_inducer.stop_chaos(chaos_id)

                # Wait for recovery and collect metrics
                await asyncio.sleep(30)  # Recovery period
                result.metrics_after = await self.metrics_collector.collect_metrics()

                # Verify recovery
                recovery_start = time.time()
                recovered = await self._wait_for_recovery(timeout=300)  # 5 minutes max

                if recovered:
                    result.recovery_time = time.time() - recovery_start
                    result.success = await self._evaluate_success_criteria(experiment, result)
                else:
                    result.failure_points.append("System did not recover within timeout")

            else:
                result.failure_points.append("Failed to inject chaos")

        except Exception as e:
            result.failure_points.append(f"Experiment failed with exception: {e}")
            self.logger.error(f"Chaos experiment failed: {e}")

        finally:
            result.end_time = datetime.utcnow()
            # Ensure all chaos is stopped
            await self.chaos_inducer.stop_all_chaos()

        return result

    async def _inject_chaos(self, experiment: ChaosExperiment) -> Optional[str]:
        """Inject chaos based on experiment type"""
        chaos_type = experiment.chaos_type
        intensity = experiment.intensity
        duration = experiment.duration_seconds

        if chaos_type == ChaosType.CPU_STRESS:
            return await self.chaos_inducer.induce_cpu_stress(intensity, duration)

        elif chaos_type == ChaosType.MEMORY_STRESS:
            return await self.chaos_inducer.induce_memory_stress(intensity, duration)

        elif chaos_type == ChaosType.NETWORK_LATENCY:
            latency_ms = int(intensity * 1000)  # Convert to milliseconds
            return await self.chaos_inducer.induce_network_latency(latency_ms, duration)

        elif chaos_type == ChaosType.SERVICE_KILL:
            # Kill processes matching target components
            for component in experiment.target_components:
                return await self.chaos_inducer.induce_service_kill(component)

        else:
            self.logger.warning(f"Unsupported chaos type: {chaos_type}")
            return None

    async def _monitor_during_chaos(self, duration: int) -> Dict[str, Any]:
        """Monitor system metrics during chaos"""
        metrics = []

        # Collect metrics every 10 seconds during chaos
        intervals = max(1, duration // 10)

        for _ in range(intervals):
            metrics.append(await self.metrics_collector.collect_metrics())
            await asyncio.sleep(10)

        return {
            "samples": metrics,
            "duration_seconds": duration
        }

    async def _verify_system_health(self) -> bool:
        """Verify system is healthy"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False

    async def _wait_for_recovery(self, timeout: int = 300) -> bool:
        """Wait for system to recover after chaos"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if await self._verify_system_health():
                return True
            await asyncio.sleep(5)

        return False

    async def _evaluate_success_criteria(self, experiment: ChaosExperiment, result: ChaosResult) -> bool:
        """Evaluate if experiment met success criteria"""
        criteria = experiment.success_criteria

        # Check if system recovered
        if not result.recovery_time:
            return False

        # Check recovery time threshold
        if "max_recovery_time" in criteria:
            if result.recovery_time > criteria["max_recovery_time"]:
                result.failure_points.append(f"Recovery time {result.recovery_time:.2f}s exceeded threshold {criteria['max_recovery_time']}s")
                return False

        # Check error rate during chaos
        if "max_error_rate" in criteria:
            # This would need integration with actual API testing
            pass

        # Check if critical services remained available
        if "critical_services_available" in criteria:
            # This would need integration with service discovery
            pass

        return True

    async def run_experiment_suite(self, experiments: List[ChaosExperiment]) -> Dict[str, Any]:
        """Run a suite of chaos engineering experiments"""
        self.logger.info(f"Starting chaos engineering suite with {len(experiments)} experiments")

        results = {}
        suite_start_time = datetime.utcnow()

        for experiment in experiments:
            try:
                result = await self.run_experiment(experiment)
                results[experiment.name] = result

                # Wait between experiments for system stabilization
                await asyncio.sleep(60)

            except Exception as e:
                self.logger.error(f"Failed to run experiment {experiment.name}: {e}")
                results[experiment.name] = ChaosResult(
                    experiment_name=experiment.name,
                    chaos_type=experiment.chaos_type,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    success=False,
                    failure_points=[f"Exception: {e}"]
                )

        # Generate suite summary
        suite_summary = {
            "start_time": suite_start_time,
            "end_time": datetime.utcnow(),
            "total_experiments": len(experiments),
            "successful_experiments": sum(1 for r in results.values() if r.success),
            "failed_experiments": sum(1 for r in results.values() if not r.success),
            "resilience_score": self._calculate_resilience_score(results),
            "recommendations": self._generate_recommendations(results)
        }

        return {
            "suite_summary": suite_summary,
            "experiment_results": results
        }

    def _calculate_resilience_score(self, results: Dict[str, ChaosResult]) -> float:
        """Calculate overall resilience score (0-100)"""
        if not results:
            return 0.0

        total_score = 0
        for result in results.values():
            experiment_score = 0

            # Base score for success
            if result.success:
                experiment_score += 50

            # Recovery time bonus (faster recovery = higher score)
            if result.recovery_time:
                if result.recovery_time < 30:
                    experiment_score += 30
                elif result.recovery_time < 60:
                    experiment_score += 20
                elif result.recovery_time < 120:
                    experiment_score += 10

            # Deduct points for failures
            experiment_score -= len(result.failure_points) * 10

            total_score += max(0, experiment_score)

        return min(100, total_score / len(results))

    def _generate_recommendations(self, results: Dict[str, ChaosResult]) -> List[str]:
        """Generate resilience improvement recommendations"""
        recommendations = []

        # Analyze common failure patterns
        failure_types = {}
        recovery_times = []

        for result in results.values():
            for failure in result.failure_points:
                failure_types[failure] = failure_types.get(failure, 0) + 1

            if result.recovery_time:
                recovery_times.append(result.recovery_time)

        # Recovery time recommendations
        if recovery_times:
            avg_recovery = sum(recovery_times) / len(recovery_times)
            if avg_recovery > 120:
                recommendations.append("Consider implementing faster health checks and auto-recovery mechanisms")
            if max(recovery_times) > 300:
                recommendations.append("Some experiments had very long recovery times - investigate circuit breakers")

        # Common failure recommendations
        if any("timeout" in failure.lower() for failure in failure_types):
            recommendations.append("Implement proper timeout handling and retry mechanisms")

        if any("connection" in failure.lower() for failure in failure_types):
            recommendations.append("Improve connection pooling and error handling")

        # General recommendations
        recommendations.extend([
            "Implement comprehensive monitoring and alerting",
            "Add automated recovery procedures",
            "Consider implementing bulkhead patterns for isolation",
            "Regular chaos engineering testing in staging environments"
        ])

        return recommendations

def create_standard_experiment_suite() -> List[ChaosExperiment]:
    """Create a standard suite of chaos engineering experiments"""

    return [
        ChaosExperiment(
            name="CPU Stress Test",
            chaos_type=ChaosType.CPU_STRESS,
            duration_seconds=120,
            intensity=0.8,  # 80% CPU load
            target_components=["api-orchestrator"],
            success_criteria={"max_recovery_time": 60},
            rollback_strategy="automatic"
        ),

        ChaosExperiment(
            name="Memory Pressure Test",
            chaos_type=ChaosType.MEMORY_STRESS,
            duration_seconds=90,
            intensity=0.7,  # 70% memory usage
            target_components=["api-orchestrator"],
            success_criteria={"max_recovery_time": 30},
            rollback_strategy="automatic"
        ),

        ChaosExperiment(
            name="Network Latency Test",
            chaos_type=ChaosType.NETWORK_LATENCY,
            duration_seconds=180,
            intensity=0.5,  # 500ms latency
            target_components=["network"],
            success_criteria={"max_recovery_time": 15},
            rollback_strategy="automatic"
        ),

        ChaosExperiment(
            name="Service Kill Test",
            chaos_type=ChaosType.SERVICE_KILL,
            duration_seconds=60,
            intensity=1.0,
            target_components=["uvicorn"],
            success_criteria={"max_recovery_time": 120},
            rollback_strategy="manual"
        )
    ]

async def main():
    """Main function for chaos engineering tests"""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create chaos engineer
    engineer = ChaosEngineer()

    # Create experiment suite
    experiments = create_standard_experiment_suite()

    try:
        # Run experiment suite
        results = await engineer.run_experiment_suite(experiments)

        # Save results
        with open("chaos_engineering_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Print summary
        summary = results["suite_summary"]
        print("\n" + "="*60)
        print("CHAOS ENGINEERING RESULTS")
        print("="*60)
        print(f"Resilience Score: {summary['resilience_score']:.1f}/100")
        print(f"Successful Experiments: {summary['successful_experiments']}/{summary['total_experiments']}")

        print(f"\nRecommendations:")
        for rec in summary['recommendations'][:5]:
            print(f"  - {rec}")

        print(f"\nDetailed results saved to: chaos_engineering_results.json")

    except KeyboardInterrupt:
        print("\nChaos engineering interrupted by user")
        await engineer.chaos_inducer.stop_all_chaos()

    except Exception as e:
        print(f"Chaos engineering failed: {e}")
        await engineer.chaos_inducer.stop_all_chaos()

if __name__ == "__main__":
    asyncio.run(main())
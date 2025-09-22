#!/usr/bin/env python3
"""
Advanced Performance Testing Suite for AI Agent Collaboration System
Tests concurrent agent operations, memory usage, and response times
"""

import asyncio
import time
import psutil
import pytest
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime, timedelta

from src.ai_agent_collaboration import (
    RealTimeCollaborationEngine,
    CollaborationMode,
    TaskPriority,
    create_collaboration_task,
    get_collaboration_status
)

# Configure logging for performance tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Performance metrics collection and analysis"""

    def __init__(self):
        self.response_times: List[float] = []
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.task_completion_times: Dict[str, float] = {}
        self.error_count = 0

    def record_response_time(self, time_ms: float):
        self.response_times.append(time_ms)

    def record_memory_usage(self):
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_usage.append(memory_mb)

    def record_cpu_usage(self):
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_usage.append(cpu_percent)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        stats = {}

        if self.response_times:
            stats['response_times'] = {
                'mean': statistics.mean(self.response_times),
                'median': statistics.median(self.response_times),
                'min': min(self.response_times),
                'max': max(self.response_times),
                'std_dev': statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0,
                'p95': self._percentile(self.response_times, 0.95),
                'p99': self._percentile(self.response_times, 0.99)
            }

        if self.memory_usage:
            stats['memory_usage_mb'] = {
                'mean': statistics.mean(self.memory_usage),
                'max': max(self.memory_usage),
                'min': min(self.memory_usage)
            }

        if self.cpu_usage:
            stats['cpu_usage_percent'] = {
                'mean': statistics.mean(self.cpu_usage),
                'max': max(self.cpu_usage)
            }

        stats['error_count'] = self.error_count
        stats['total_requests'] = len(self.response_times)

        return stats

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

class AICollaborationPerformanceTest:
    """Comprehensive performance test suite for AI collaboration"""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.collaboration_engine = None

    async def setup(self):
        """Setup collaboration engine for testing"""
        try:
            self.collaboration_engine = RealTimeCollaborationEngine()
            await self.collaboration_engine.initialize_collaboration()
            logger.info("✅ Collaboration engine initialized for performance testing")
        except Exception as e:
            logger.error(f"❌ Failed to setup collaboration engine: {e}")
            raise

    async def teardown(self):
        """Cleanup after performance tests"""
        if self.collaboration_engine:
            await self.collaboration_engine.shutdown()
            logger.info("✅ Collaboration engine shutdown complete")

    async def test_concurrent_task_creation(self, num_tasks: int = 100) -> Dict[str, Any]:
        """Test creating multiple tasks concurrently"""
        logger.info(f"🚀 Testing concurrent task creation ({num_tasks} tasks)")

        start_time = time.time()
        tasks = []

        # Create tasks concurrently
        for i in range(num_tasks):
            task_description = f"Performance test task {i}"
            task_coro = create_collaboration_task(
                task_description,
                task_type="performance_test"
            )
            tasks.append(task_coro)

        # Execute all tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Analyze results
            successful_tasks = [r for r in results if not isinstance(r, Exception)]
            failed_tasks = [r for r in results if isinstance(r, Exception)]

            total_time = time.time() - start_time

            self.metrics.record_response_time(total_time * 1000)  # Convert to ms
            self.metrics.record_memory_usage()
            self.metrics.record_cpu_usage()

            return {
                "total_tasks": num_tasks,
                "successful_tasks": len(successful_tasks),
                "failed_tasks": len(failed_tasks),
                "total_time_seconds": total_time,
                "tasks_per_second": num_tasks / total_time if total_time > 0 else 0,
                "average_time_per_task_ms": (total_time * 1000) / num_tasks
            }

        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"❌ Concurrent task creation failed: {e}")
            return {"error": str(e)}

    async def test_different_collaboration_modes(self) -> Dict[str, Any]:
        """Test performance of different collaboration modes"""
        logger.info("🔄 Testing different collaboration modes")

        modes = [
            CollaborationMode.SWARM,
            CollaborationMode.PARALLEL,
            CollaborationMode.SEQUENTIAL,
            CollaborationMode.HIERARCHICAL
        ]

        results = {}

        for mode in modes:
            logger.info(f"Testing {mode.value} mode")
            start_time = time.time()

            try:
                task_description = f"Performance test for {mode.value} mode"
                task_id = await self.collaboration_engine.create_collaboration_task(
                    task_description=task_description,
                    task_type="performance_test",
                    priority=TaskPriority.HIGH,
                    collaboration_mode=mode
                )

                # Wait a bit for task processing
                await asyncio.sleep(2)

                # Check task status
                status = self.collaboration_engine.get_collaboration_status()

                execution_time = time.time() - start_time
                self.metrics.record_response_time(execution_time * 1000)

                results[mode.value] = {
                    "execution_time_seconds": execution_time,
                    "task_id": task_id,
                    "agent_status": status.get("agent_statuses", {}),
                    "success": True
                }

            except Exception as e:
                self.metrics.error_count += 1
                logger.error(f"❌ {mode.value} mode failed: {e}")
                results[mode.value] = {
                    "error": str(e),
                    "success": False
                }

        return results

    async def test_agent_scalability(self) -> Dict[str, Any]:
        """Test system performance with increasing agent loads"""
        logger.info("📈 Testing agent scalability")

        # Test with different numbers of simultaneous tasks
        load_levels = [1, 5, 10, 20, 50]
        scalability_results = {}

        for load in load_levels:
            logger.info(f"Testing with {load} simultaneous tasks")

            start_time = time.time()
            tasks = []

            # Create multiple tasks simultaneously
            for i in range(load):
                task_coro = self.collaboration_engine.create_collaboration_task(
                    task_description=f"Scalability test task {i}",
                    task_type="scalability_test",
                    priority=TaskPriority.MEDIUM,
                    collaboration_mode=CollaborationMode.PARALLEL
                )
                tasks.append(task_coro)

            try:
                # Execute all tasks
                task_ids = await asyncio.gather(*tasks, return_exceptions=True)

                # Wait for processing
                await asyncio.sleep(3)

                # Get system status
                status = self.collaboration_engine.get_collaboration_status()
                execution_time = time.time() - start_time

                self.metrics.record_response_time(execution_time * 1000)
                self.metrics.record_memory_usage()
                self.metrics.record_cpu_usage()

                scalability_results[f"load_{load}"] = {
                    "execution_time_seconds": execution_time,
                    "throughput_tasks_per_second": load / execution_time if execution_time > 0 else 0,
                    "active_agents": status.get("active_agents", 0),
                    "total_agents": status.get("total_agents", 0),
                    "successful_tasks": len([tid for tid in task_ids if not isinstance(tid, Exception)]),
                    "failed_tasks": len([tid for tid in task_ids if isinstance(tid, Exception)])
                }

            except Exception as e:
                self.metrics.error_count += 1
                logger.error(f"❌ Load test {load} failed: {e}")
                scalability_results[f"load_{load}"] = {
                    "error": str(e),
                    "load": load
                }

        return scalability_results

    async def test_memory_leak_detection(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Test for memory leaks during sustained operation"""
        logger.info(f"🔍 Testing for memory leaks over {duration_seconds} seconds")

        start_time = time.time()
        memory_samples = []
        task_count = 0

        while time.time() - start_time < duration_seconds:
            try:
                # Create a task
                task_id = await self.collaboration_engine.create_collaboration_task(
                    task_description=f"Memory leak test task {task_count}",
                    task_type="memory_test",
                    priority=TaskPriority.LOW
                )
                task_count += 1

                # Sample memory usage
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append({
                    "timestamp": time.time(),
                    "memory_mb": memory_mb,
                    "task_count": task_count
                })

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)

            except Exception as e:
                self.metrics.error_count += 1
                logger.error(f"❌ Memory leak test error: {e}")

        # Analyze memory trend
        if len(memory_samples) > 1:
            initial_memory = memory_samples[0]["memory_mb"]
            final_memory = memory_samples[-1]["memory_mb"]
            memory_growth = final_memory - initial_memory

            # Calculate memory growth rate
            time_span = memory_samples[-1]["timestamp"] - memory_samples[0]["timestamp"]
            growth_rate_mb_per_second = memory_growth / time_span if time_span > 0 else 0

            return {
                "duration_seconds": duration_seconds,
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_growth_mb": memory_growth,
                "growth_rate_mb_per_second": growth_rate_mb_per_second,
                "total_tasks_created": task_count,
                "samples_collected": len(memory_samples),
                "potential_leak": memory_growth > 50  # Flag if growth > 50MB
            }
        else:
            return {"error": "Insufficient memory samples collected"}

# Performance test execution functions
@pytest.mark.asyncio
async def test_ai_collaboration_performance():
    """Main performance test runner"""
    performance_test = AICollaborationPerformanceTest()

    try:
        # Setup
        await performance_test.setup()

        # Run performance tests
        logger.info("🏁 Starting AI Collaboration Performance Tests")

        # Test 1: Concurrent task creation
        concurrent_results = await performance_test.test_concurrent_task_creation(50)
        logger.info(f"Concurrent task results: {concurrent_results}")

        # Test 2: Different collaboration modes
        mode_results = await performance_test.test_different_collaboration_modes()
        logger.info(f"Collaboration mode results: {mode_results}")

        # Test 3: Agent scalability
        scalability_results = await performance_test.test_agent_scalability()
        logger.info(f"Scalability results: {scalability_results}")

        # Test 4: Memory leak detection (shorter duration for tests)
        memory_results = await performance_test.test_memory_leak_detection(30)
        logger.info(f"Memory leak results: {memory_results}")

        # Generate final performance report
        final_stats = performance_test.metrics.get_statistics()

        performance_report = {
            "test_timestamp": datetime.now().isoformat(),
            "concurrent_task_performance": concurrent_results,
            "collaboration_mode_performance": mode_results,
            "scalability_performance": scalability_results,
            "memory_leak_analysis": memory_results,
            "overall_statistics": final_stats
        }

        logger.info("📊 Performance Test Report:")
        for key, value in performance_report.items():
            logger.info(f"  {key}: {value}")

        # Assert performance requirements
        if final_stats.get("response_times", {}).get("mean", 0) > 5000:  # 5 seconds
            pytest.fail(f"Average response time too high: {final_stats['response_times']['mean']}ms")

        if memory_results.get("potential_leak", False):
            pytest.fail(f"Potential memory leak detected: {memory_results['memory_growth_mb']}MB growth")

        if performance_test.metrics.error_count > 0:
            logger.warning(f"⚠️ {performance_test.metrics.error_count} errors occurred during testing")

        logger.info("✅ AI Collaboration Performance Tests Completed Successfully")

    finally:
        # Cleanup
        await performance_test.teardown()

if __name__ == "__main__":
    # Run performance tests directly
    asyncio.run(test_ai_collaboration_performance())
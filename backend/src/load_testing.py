"""
Load Testing Module for API Orchestrator
Supports load, stress, spike, and soak testing
"""

import asyncio
import time
import statistics
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from enum import Enum

class LoadTestType(Enum):
    LOAD = "load"          # Gradual increase to target load
    STRESS = "stress"      # Push beyond normal capacity
    SPIKE = "spike"        # Sudden increase in traffic
    SOAK = "soak"          # Extended duration testing

@dataclass
class LoadTestResult:
    """Single request result"""
    request_id: int
    timestamp: datetime
    response_time_ms: float
    status_code: int
    success: bool
    error: Optional[str] = None
    response_size_bytes: int = 0

@dataclass
class LoadTestSummary:
    """Summary of load test results"""
    test_type: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_seconds: float
    requests_per_second: float
    
    # Response time statistics (in ms)
    min_response_time: float
    max_response_time: float
    mean_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    
    # Error analysis
    error_rate: float
    status_code_distribution: Dict[int, int]
    errors_by_type: Dict[str, int]
    
    # Throughput
    total_bytes_received: int
    avg_bytes_per_second: float
    
    # Time series data for visualization
    response_times_over_time: List[Dict[str, Any]]
    requests_per_second_over_time: List[Dict[str, Any]]

class LoadTester:
    """Main load testing class"""
    
    def __init__(self):
        self.results: List[LoadTestResult] = []
        self.is_running = False
        self.start_time = None
        self.end_time = None
        
    async def run_load_test(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        test_type: LoadTestType = LoadTestType.LOAD,
        duration_seconds: int = 60,
        target_rps: int = 10,
        concurrent_users: int = 10,
        ramp_up_seconds: int = 10
    ) -> LoadTestSummary:
        """
        Run a load test against the specified endpoint
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            body: Request body
            test_type: Type of load test
            duration_seconds: Total test duration
            target_rps: Target requests per second
            concurrent_users: Number of concurrent users/connections
            ramp_up_seconds: Time to ramp up to target load
        """
        
        self.results = []
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        try:
            if test_type == LoadTestType.LOAD:
                await self._run_load_pattern(
                    url, method, headers, body,
                    duration_seconds, target_rps, concurrent_users, ramp_up_seconds
                )
            elif test_type == LoadTestType.STRESS:
                await self._run_stress_pattern(
                    url, method, headers, body,
                    duration_seconds, target_rps * 2, concurrent_users * 2
                )
            elif test_type == LoadTestType.SPIKE:
                await self._run_spike_pattern(
                    url, method, headers, body,
                    duration_seconds, target_rps, concurrent_users
                )
            elif test_type == LoadTestType.SOAK:
                await self._run_soak_pattern(
                    url, method, headers, body,
                    duration_seconds * 5, target_rps, concurrent_users
                )
        finally:
            self.is_running = False
            self.end_time = datetime.utcnow()
        
        return self._generate_summary(test_type.value)
    
    async def _run_load_pattern(
        self, url: str, method: str, headers: Dict, body: Any,
        duration: int, target_rps: int, users: int, ramp_up: int
    ):
        """Standard load test with gradual ramp-up"""
        
        tasks = []
        request_delay = 1.0 / target_rps if target_rps > 0 else 1.0
        
        # Ramp-up phase
        for i in range(ramp_up):
            current_rps = (target_rps / ramp_up) * (i + 1)
            current_delay = 1.0 / current_rps if current_rps > 0 else 1.0
            
            for _ in range(int(current_rps)):
                task = asyncio.create_task(
                    self._make_request(len(self.results), url, method, headers, body)
                )
                tasks.append(task)
                await asyncio.sleep(current_delay)
        
        # Sustained load phase
        remaining_time = duration - ramp_up
        total_requests = int(target_rps * remaining_time)
        
        for i in range(total_requests):
            task = asyncio.create_task(
                self._make_request(len(self.results) + i, url, method, headers, body)
            )
            tasks.append(task)
            await asyncio.sleep(request_delay)
        
        # Wait for all requests to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_stress_pattern(
        self, url: str, method: str, headers: Dict, body: Any,
        duration: int, target_rps: int, users: int
    ):
        """Stress test - push beyond normal capacity"""
        
        tasks = []
        request_delay = 1.0 / target_rps if target_rps > 0 else 0.1
        total_requests = int(target_rps * duration)
        
        # Send requests as fast as possible
        for i in range(total_requests):
            task = asyncio.create_task(
                self._make_request(i, url, method, headers, body)
            )
            tasks.append(task)
            
            # Minimal delay to avoid overwhelming the system
            if i % users == 0:
                await asyncio.sleep(request_delay)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_spike_pattern(
        self, url: str, method: str, headers: Dict, body: Any,
        duration: int, target_rps: int, users: int
    ):
        """Spike test - sudden traffic increase"""
        
        tasks = []
        
        # Normal load for first third
        normal_duration = duration // 3
        normal_rps = target_rps // 2
        
        for i in range(int(normal_rps * normal_duration)):
            task = asyncio.create_task(
                self._make_request(i, url, method, headers, body)
            )
            tasks.append(task)
            await asyncio.sleep(1.0 / normal_rps)
        
        # Spike for middle third
        spike_rps = target_rps * 3
        for i in range(int(spike_rps * normal_duration)):
            task = asyncio.create_task(
                self._make_request(len(self.results) + i, url, method, headers, body)
            )
            tasks.append(task)
            await asyncio.sleep(1.0 / spike_rps)
        
        # Return to normal for last third
        for i in range(int(normal_rps * normal_duration)):
            task = asyncio.create_task(
                self._make_request(len(self.results) + i, url, method, headers, body)
            )
            tasks.append(task)
            await asyncio.sleep(1.0 / normal_rps)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_soak_pattern(
        self, url: str, method: str, headers: Dict, body: Any,
        duration: int, target_rps: int, users: int
    ):
        """Soak test - extended duration at steady load"""
        
        # Run at steady load for extended period
        await self._run_load_pattern(
            url, method, headers, body,
            duration, target_rps, users, 30  # 30 second ramp-up
        )
    
    async def _make_request(
        self, request_id: int, url: str, method: str,
        headers: Optional[Dict], body: Optional[Any]
    ) -> LoadTestResult:
        """Make a single HTTP request and record the result"""
        
        start_time = time.time()
        result = LoadTestResult(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            response_time_ms=0,
            status_code=0,
            success=False
        )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    content=body if isinstance(body, (str, bytes)) else None
                )
                
                result.response_time_ms = (time.time() - start_time) * 1000
                result.status_code = response.status_code
                result.success = 200 <= response.status_code < 300
                result.response_size_bytes = len(response.content)
                
        except httpx.TimeoutException:
            result.error = "Request timeout"
            result.response_time_ms = 30000  # 30 second timeout
        except httpx.RequestError as e:
            result.error = f"Request error: {str(e)}"
            result.response_time_ms = (time.time() - start_time) * 1000
        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"
            result.response_time_ms = (time.time() - start_time) * 1000
        
        self.results.append(result)
        return result
    
    def _generate_summary(self, test_type: str) -> LoadTestSummary:
        """Generate summary statistics from test results"""
        
        if not self.results:
            return LoadTestSummary(
                test_type=test_type,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_duration_seconds=0,
                requests_per_second=0,
                min_response_time=0,
                max_response_time=0,
                mean_response_time=0,
                median_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                error_rate=0,
                status_code_distribution={},
                errors_by_type={},
                total_bytes_received=0,
                avg_bytes_per_second=0,
                response_times_over_time=[],
                requests_per_second_over_time=[]
            )
        
        # Basic counts
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.success)
        failed_requests = total_requests - successful_requests
        
        # Duration
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Response times
        response_times = [r.response_time_ms for r in self.results]
        response_times.sort()
        
        # Percentiles
        p95_index = int(len(response_times) * 0.95)
        p99_index = int(len(response_times) * 0.99)
        
        # Status code distribution
        status_codes = {}
        for r in self.results:
            status_codes[r.status_code] = status_codes.get(r.status_code, 0) + 1
        
        # Error types
        error_types = {}
        for r in self.results:
            if r.error:
                error_type = r.error.split(':')[0]
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Throughput
        total_bytes = sum(r.response_size_bytes for r in self.results)
        
        # Time series data (sample every second)
        response_times_series = []
        rps_series = []
        
        if self.results:
            start = self.results[0].timestamp
            current_second = 0
            second_results = []
            
            for result in self.results:
                elapsed = (result.timestamp - start).total_seconds()
                if int(elapsed) > current_second:
                    if second_results:
                        response_times_series.append({
                            "time": current_second,
                            "avg_response_time": statistics.mean(second_results),
                            "count": len(second_results)
                        })
                        rps_series.append({
                            "time": current_second,
                            "rps": len(second_results)
                        })
                    current_second = int(elapsed)
                    second_results = [result.response_time_ms]
                else:
                    second_results.append(result.response_time_ms)
        
        return LoadTestSummary(
            test_type=test_type,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_duration_seconds=duration,
            requests_per_second=total_requests / duration if duration > 0 else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            mean_response_time=statistics.mean(response_times) if response_times else 0,
            median_response_time=statistics.median(response_times) if response_times else 0,
            p95_response_time=response_times[p95_index] if p95_index < len(response_times) else 0,
            p99_response_time=response_times[p99_index] if p99_index < len(response_times) else 0,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            status_code_distribution=status_codes,
            errors_by_type=error_types,
            total_bytes_received=total_bytes,
            avg_bytes_per_second=total_bytes / duration if duration > 0 else 0,
            response_times_over_time=response_times_series,
            requests_per_second_over_time=rps_series
        )
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current statistics while test is running"""
        
        if not self.results:
            return {"status": "No results yet"}
        
        current_time = datetime.utcnow()
        elapsed = (current_time - self.start_time).total_seconds() if self.start_time else 0
        
        recent_results = [r for r in self.results[-100:]]  # Last 100 results
        
        return {
            "is_running": self.is_running,
            "elapsed_seconds": elapsed,
            "total_requests": len(self.results),
            "successful_requests": sum(1 for r in self.results if r.success),
            "current_rps": len(recent_results) / 10 if len(recent_results) > 0 else 0,
            "avg_response_time_ms": statistics.mean([r.response_time_ms for r in recent_results]) if recent_results else 0
        }
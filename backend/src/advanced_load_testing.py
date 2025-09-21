"""
Advanced Load Testing Framework for API Orchestrator
Supports distributed load testing, performance metrics collection, and AI-powered test generation
"""

from typing import Optional, Dict, Any, List, Callable, AsyncGenerator
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiohttp
import json
import uuid
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Boolean, Text

from src.database import Base, get_db
from src.config import settings

class LoadTestType(str, Enum):
    STRESS = "stress"
    SPIKE = "spike"
    VOLUME = "volume"
    ENDURANCE = "endurance"
    BREAKPOINT = "breakpoint"
    SOAK = "soak"

class TestPhase(str, Enum):
    RAMP_UP = "ramp_up"
    STEADY_STATE = "steady_state"
    RAMP_DOWN = "ramp_down"
    SPIKE_BURST = "spike_burst"

class MetricType(str, Enum):
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    NETWORK_IO = "network_io"
    DATABASE_CONNECTIONS = "database_connections"

@dataclass
class LoadTestConfig:
    """Load test configuration"""
    test_name: str
    test_type: LoadTestType
    target_url: str
    duration_seconds: int
    max_users: int
    ramp_up_seconds: int = 60
    ramp_down_seconds: int = 30
    think_time_seconds: float = 1.0
    request_timeout: int = 30
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Optional[Dict[str, Any]] = None
    method: str = "GET"
    success_criteria: Dict[str, float] = field(default_factory=lambda: {
        "max_response_time_p95": 2000,  # ms
        "max_error_rate": 0.05,  # 5%
        "min_throughput": 100  # requests per second
    })
    geo_distribution: List[str] = field(default_factory=lambda: ["us-east-1"])
    custom_assertions: List[str] = field(default_factory=list)

@dataclass
class RequestMetrics:
    """Individual request metrics"""
    timestamp: datetime
    response_time_ms: float
    status_code: int
    error: Optional[str] = None
    bytes_sent: int = 0
    bytes_received: int = 0
    worker_id: str = ""

@dataclass
class AggregatedMetrics:
    """Aggregated test metrics"""
    timestamp: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    throughput_rps: float
    bytes_transferred: int
    active_users: int
    errors_by_type: Dict[str, int] = field(default_factory=dict)

class LoadTestResult(Base):
    """Database model for load test results"""
    __tablename__ = "load_test_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    test_name = Column(String, nullable=False)
    test_type = Column(String, nullable=False)
    target_url = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String, default="running")  # running, completed, failed, cancelled
    summary_metrics = Column(JSON)
    detailed_metrics = Column(JSON)
    performance_score = Column(Float)
    recommendations = Column(JSON)
    created_by = Column(String)
    tags = Column(JSON)

class DistributedWorker:
    """Distributed load testing worker"""

    def __init__(self, worker_id: str, region: str = "local"):
        self.worker_id = worker_id
        self.region = region
        self.session = None
        self.metrics_buffer: List[RequestMetrics] = []
        self.is_running = False

    async def initialize(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(
            limit=1000,
            limit_per_host=100,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

    async def execute_request(
        self,
        config: LoadTestConfig,
        user_context: Dict[str, Any] = None
    ) -> RequestMetrics:
        """Execute single HTTP request with metrics collection"""
        start_time = time.time()
        timestamp = datetime.utcnow()

        try:
            headers = config.headers.copy()
            if user_context and "auth_token" in user_context:
                headers["Authorization"] = f"Bearer {user_context['auth_token']}"

            async with self.session.request(
                method=config.method,
                url=config.target_url,
                headers=headers,
                json=config.payload,
                timeout=aiohttp.ClientTimeout(total=config.request_timeout)
            ) as response:
                content = await response.read()
                response_time_ms = (time.time() - start_time) * 1000

                return RequestMetrics(
                    timestamp=timestamp,
                    response_time_ms=response_time_ms,
                    status_code=response.status,
                    bytes_sent=len(json.dumps(config.payload).encode()) if config.payload else 0,
                    bytes_received=len(content),
                    worker_id=self.worker_id
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return RequestMetrics(
                timestamp=timestamp,
                response_time_ms=response_time_ms,
                status_code=0,
                error=str(e),
                worker_id=self.worker_id
            )

    async def user_session(
        self,
        config: LoadTestConfig,
        user_id: int,
        metrics_callback: Callable[[RequestMetrics], None]
    ):
        """Simulate single user session"""
        user_context = {"user_id": user_id, "session_start": datetime.utcnow()}

        while self.is_running:
            try:
                # Execute request
                metrics = await self.execute_request(config, user_context)
                metrics_callback(metrics)

                # Apply think time
                if config.think_time_seconds > 0:
                    await asyncio.sleep(config.think_time_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in user session {user_id}: {e}")
                await asyncio.sleep(1)

class LoadTestOrchestrator:
    """Main load testing orchestrator"""

    def __init__(self):
        self.workers: List[DistributedWorker] = []
        self.metrics_buffer: List[RequestMetrics] = []
        self.aggregated_metrics: List[AggregatedMetrics] = []
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.test_id: Optional[str] = None
        self.is_running = False

    def add_worker(self, region: str = "local") -> DistributedWorker:
        """Add distributed worker"""
        worker_id = f"worker-{region}-{len(self.workers)}"
        worker = DistributedWorker(worker_id, region)
        self.workers.append(worker)
        return worker

    async def initialize_workers(self):
        """Initialize all workers"""
        for worker in self.workers:
            await worker.initialize()

    async def cleanup_workers(self):
        """Cleanup all workers"""
        for worker in self.workers:
            await worker.cleanup()

    def collect_metrics(self, metrics: RequestMetrics):
        """Collect metrics from workers"""
        self.metrics_buffer.append(metrics)

    def calculate_aggregated_metrics(
        self,
        window_start: datetime,
        window_end: datetime,
        active_users: int
    ) -> AggregatedMetrics:
        """Calculate aggregated metrics for time window"""
        window_metrics = [
            m for m in self.metrics_buffer
            if window_start <= m.timestamp <= window_end
        ]

        if not window_metrics:
            return AggregatedMetrics(
                timestamp=window_end,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                error_rate=0.0,
                avg_response_time=0.0,
                p50_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                throughput_rps=0.0,
                bytes_transferred=0,
                active_users=active_users
            )

        successful = [m for m in window_metrics if m.error is None and 200 <= m.status_code < 400]
        failed = [m for m in window_metrics if m.error is not None or m.status_code >= 400]

        response_times = [m.response_time_ms for m in window_metrics]

        window_duration = (window_end - window_start).total_seconds()
        throughput = len(window_metrics) / window_duration if window_duration > 0 else 0

        errors_by_type = {}
        for m in failed:
            error_key = m.error or f"HTTP_{m.status_code}"
            errors_by_type[error_key] = errors_by_type.get(error_key, 0) + 1

        return AggregatedMetrics(
            timestamp=window_end,
            total_requests=len(window_metrics),
            successful_requests=len(successful),
            failed_requests=len(failed),
            error_rate=len(failed) / len(window_metrics),
            avg_response_time=statistics.mean(response_times),
            p50_response_time=np.percentile(response_times, 50),
            p95_response_time=np.percentile(response_times, 95),
            p99_response_time=np.percentile(response_times, 99),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            throughput_rps=throughput,
            bytes_transferred=sum(m.bytes_received for m in window_metrics),
            active_users=active_users,
            errors_by_type=errors_by_type
        )

    async def run_load_test(
        self,
        config: LoadTestConfig,
        db: Session,
        progress_callback: Optional[Callable[[AggregatedMetrics], None]] = None
    ) -> str:
        """Execute distributed load test"""

        # Create test record
        test_result = LoadTestResult(
            test_name=config.test_name,
            test_type=config.test_type.value,
            target_url=config.target_url,
            config=config.__dict__,
            start_time=datetime.utcnow(),
            status="running"
        )
        db.add(test_result)
        db.commit()
        self.test_id = test_result.id

        try:
            # Initialize workers
            if not self.workers:
                # Create default local worker
                self.add_worker("local")

            await self.initialize_workers()

            # Start load test phases
            await self._execute_test_phases(config, progress_callback)

            # Calculate final metrics
            final_metrics = self._calculate_final_metrics()
            performance_score = self._calculate_performance_score(config, final_metrics)
            recommendations = self._generate_recommendations(config, final_metrics)

            # Update test result
            test_result.end_time = datetime.utcnow()
            test_result.status = "completed"
            test_result.summary_metrics = final_metrics
            test_result.performance_score = performance_score
            test_result.recommendations = recommendations
            db.commit()

            return test_result.id

        except Exception as e:
            test_result.status = "failed"
            test_result.summary_metrics = {"error": str(e)}
            db.commit()
            raise
        finally:
            await self.cleanup_workers()
            self.is_running = False

    async def _execute_test_phases(
        self,
        config: LoadTestConfig,
        progress_callback: Optional[Callable[[AggregatedMetrics], None]] = None
    ):
        """Execute load test phases with proper ramping"""
        self.is_running = True
        test_start = datetime.utcnow()
        user_tasks = []

        # Phase 1: Ramp up
        for i in range(config.max_users):
            if not self.is_running:
                break

            # Select worker (round robin)
            worker = self.workers[i % len(self.workers)]
            worker.is_running = True

            # Start user session
            task = asyncio.create_task(
                worker.user_session(config, i, self.collect_metrics)
            )
            user_tasks.append(task)

            # Ramp up delay
            ramp_delay = config.ramp_up_seconds / config.max_users
            await asyncio.sleep(ramp_delay)

            # Report progress every 10 users
            if i % 10 == 0 and progress_callback:
                current_time = datetime.utcnow()
                window_start = current_time - timedelta(seconds=10)
                metrics = self.calculate_aggregated_metrics(window_start, current_time, i + 1)
                progress_callback(metrics)

        # Phase 2: Steady state
        steady_duration = config.duration_seconds - config.ramp_up_seconds - config.ramp_down_seconds
        if steady_duration > 0:
            await asyncio.sleep(steady_duration)

        # Phase 3: Ramp down
        for worker in self.workers:
            worker.is_running = False

        # Cancel user tasks
        for task in user_tasks:
            task.cancel()

        # Wait for graceful shutdown
        await asyncio.sleep(config.ramp_down_seconds)

    def _calculate_final_metrics(self) -> Dict[str, Any]:
        """Calculate final aggregated metrics"""
        if not self.metrics_buffer:
            return {}

        successful = [m for m in self.metrics_buffer if m.error is None and 200 <= m.status_code < 400]
        failed = [m for m in self.metrics_buffer if m.error is not None or m.status_code >= 400]
        response_times = [m.response_time_ms for m in self.metrics_buffer]

        test_duration = (max(m.timestamp for m in self.metrics_buffer) -
                        min(m.timestamp for m in self.metrics_buffer)).total_seconds()

        return {
            "total_requests": len(self.metrics_buffer),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "error_rate": len(failed) / len(self.metrics_buffer),
            "avg_response_time_ms": statistics.mean(response_times),
            "p50_response_time_ms": np.percentile(response_times, 50),
            "p95_response_time_ms": np.percentile(response_times, 95),
            "p99_response_time_ms": np.percentile(response_times, 99),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "throughput_rps": len(self.metrics_buffer) / test_duration if test_duration > 0 else 0,
            "total_bytes_transferred": sum(m.bytes_received for m in self.metrics_buffer),
            "test_duration_seconds": test_duration,
            "workers_used": len(self.workers)
        }

    def _calculate_performance_score(self, config: LoadTestConfig, metrics: Dict[str, Any]) -> float:
        """Calculate performance score based on success criteria"""
        score = 100.0
        criteria = config.success_criteria

        # Response time check
        if metrics.get("p95_response_time_ms", 0) > criteria.get("max_response_time_p95", 2000):
            score -= 30

        # Error rate check
        if metrics.get("error_rate", 0) > criteria.get("max_error_rate", 0.05):
            score -= 40

        # Throughput check
        if metrics.get("throughput_rps", 0) < criteria.get("min_throughput", 100):
            score -= 30

        return max(0, score)

    def _generate_recommendations(self, config: LoadTestConfig, metrics: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        if metrics.get("p95_response_time_ms", 0) > 2000:
            recommendations.append("Consider implementing response caching to reduce latency")
            recommendations.append("Review database query performance and add appropriate indexes")

        if metrics.get("error_rate", 0) > 0.05:
            recommendations.append("Investigate error patterns and implement circuit breakers")
            recommendations.append("Add request retry logic with exponential backoff")

        if metrics.get("throughput_rps", 0) < 100:
            recommendations.append("Consider horizontal scaling or load balancing")
            recommendations.append("Review application server configuration and connection pooling")

        return recommendations

# Global orchestrator instance
load_test_orchestrator = LoadTestOrchestrator()

class AITestGenerator:
    """AI-powered test case generation"""

    @staticmethod
    def generate_realistic_test_scenarios(api_spec: Dict[str, Any]) -> List[LoadTestConfig]:
        """Generate realistic load test scenarios from API specification"""
        scenarios = []

        # Extract endpoints from OpenAPI spec
        paths = api_spec.get("paths", {})

        for path, methods in paths.items():
            for method, spec in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE"]:
                    # Generate stress test
                    stress_config = LoadTestConfig(
                        test_name=f"Stress Test - {method.upper()} {path}",
                        test_type=LoadTestType.STRESS,
                        target_url=f"{api_spec.get('servers', [{}])[0].get('url', '')}{path}",
                        duration_seconds=300,  # 5 minutes
                        max_users=100,
                        method=method.upper()
                    )
                    scenarios.append(stress_config)

                    # Generate spike test
                    spike_config = LoadTestConfig(
                        test_name=f"Spike Test - {method.upper()} {path}",
                        test_type=LoadTestType.SPIKE,
                        target_url=f"{api_spec.get('servers', [{}])[0].get('url', '')}{path}",
                        duration_seconds=180,  # 3 minutes
                        max_users=200,
                        ramp_up_seconds=10,  # Quick spike
                        method=method.upper()
                    )
                    scenarios.append(spike_config)

        return scenarios

    @staticmethod
    def generate_smart_payloads(endpoint_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate smart test payloads based on schema"""
        payloads = []

        request_body = endpoint_spec.get("requestBody", {})
        if request_body:
            schema = request_body.get("content", {}).get("application/json", {}).get("schema", {})

            # Generate valid payload
            valid_payload = {}
            properties = schema.get("properties", {})

            for prop_name, prop_spec in properties.items():
                if prop_spec.get("type") == "string":
                    valid_payload[prop_name] = f"test_{prop_name}"
                elif prop_spec.get("type") == "integer":
                    valid_payload[prop_name] = 42
                elif prop_spec.get("type") == "boolean":
                    valid_payload[prop_name] = True

            payloads.append(valid_payload)

            # Generate edge case payloads
            if properties:
                # Empty payload
                payloads.append({})

                # Maximum length strings
                max_payload = {}
                for prop_name, prop_spec in properties.items():
                    if prop_spec.get("type") == "string":
                        max_len = prop_spec.get("maxLength", 1000)
                        max_payload[prop_name] = "x" * max_len
                payloads.append(max_payload)

        return payloads

# Utility functions
async def quick_stress_test(target_url: str, max_users: int = 50, duration: int = 60) -> Dict[str, Any]:
    """Quick stress test utility"""
    config = LoadTestConfig(
        test_name="Quick Stress Test",
        test_type=LoadTestType.STRESS,
        target_url=target_url,
        duration_seconds=duration,
        max_users=max_users,
        ramp_up_seconds=10
    )

    orchestrator = LoadTestOrchestrator()
    orchestrator.add_worker("local")

    from src.database import SessionLocal
    db = SessionLocal()
    try:
        test_id = await orchestrator.run_load_test(config, db)
        result = db.query(LoadTestResult).filter(LoadTestResult.id == test_id).first()
        return result.summary_metrics
    finally:
        db.close()

def create_performance_dashboard_data(test_id: str, db: Session) -> Dict[str, Any]:
    """Create dashboard data for performance visualization"""
    test_result = db.query(LoadTestResult).filter(LoadTestResult.id == test_id).first()
    if not test_result:
        return {}

    metrics = test_result.summary_metrics or {}

    return {
        "test_overview": {
            "test_name": test_result.test_name,
            "test_type": test_result.test_type,
            "duration": metrics.get("test_duration_seconds", 0),
            "performance_score": test_result.performance_score,
            "status": test_result.status
        },
        "key_metrics": {
            "total_requests": metrics.get("total_requests", 0),
            "error_rate": f"{metrics.get('error_rate', 0) * 100:.2f}%",
            "avg_response_time": f"{metrics.get('avg_response_time_ms', 0):.0f}ms",
            "p95_response_time": f"{metrics.get('p95_response_time_ms', 0):.0f}ms",
            "throughput": f"{metrics.get('throughput_rps', 0):.1f} RPS"
        },
        "performance_breakdown": {
            "response_times": {
                "min": metrics.get("min_response_time_ms", 0),
                "p50": metrics.get("p50_response_time_ms", 0),
                "p95": metrics.get("p95_response_time_ms", 0),
                "p99": metrics.get("p99_response_time_ms", 0),
                "max": metrics.get("max_response_time_ms", 0)
            },
            "success_rate": f"{(1 - metrics.get('error_rate', 0)) * 100:.2f}%",
            "data_transferred": f"{metrics.get('total_bytes_transferred', 0) / 1024 / 1024:.2f} MB"
        },
        "recommendations": test_result.recommendations or []
    }
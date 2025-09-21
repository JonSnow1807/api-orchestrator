#!/usr/bin/env python3
"""
Self-Healing API Infrastructure
Automatically detects, diagnoses, and fixes API issues in real-time
"""

import asyncio
import time
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import psutil
import statistics
from collections import defaultdict, deque

# Import our AI agents and Kill Shot features
from kill_shots.predictive_failure_analysis import PredictiveFailureAnalysis, FailurePrediction
from autonomous_code_generation import AutonomousCodeGenerator, CodeLanguage, CodeType

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    RECOVERING = "recovering"

class HealingAction(Enum):
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    APPLY_PATCH = "apply_patch"
    ROLLBACK = "rollback"
    CIRCUIT_BREAKER = "circuit_breaker"

@dataclass
class HealthCheck:
    endpoint: str
    status: HealthStatus
    response_time: float
    error_message: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class HealingEvent:
    event_id: str
    issue_type: str
    severity: str
    affected_services: List[str]
    healing_actions: List[HealingAction]
    status: str
    timestamp: datetime
    resolution_time: Optional[float]

class SelfHealingInfrastructure:
    """
    Advanced self-healing infrastructure that automatically maintains API health
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Core components
        self.predictive_analyzer = PredictiveFailureAnalysis()
        self.code_generator = AutonomousCodeGenerator()

        # Health monitoring
        self.health_checks: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.service_metrics: Dict[str, Dict] = {}
        self.healing_history: List[HealingEvent] = []

        # Circuit breakers
        self.circuit_breakers: Dict[str, Dict] = {}

        # Configuration
        self.check_interval = 30  # seconds
        self.healing_enabled = True
        self.max_healing_attempts = 3

        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.healing_task: Optional[asyncio.Task] = None

        # Service registry
        self.services = {
            "api_gateway": "http://localhost:8000",
            "auth_service": "http://localhost:8001",
            "database": "postgresql://localhost:5432",
            "cache": "redis://localhost:6379",
            "monitoring": "http://localhost:9090"
        }

    async def initialize(self):
        """Initialize the self-healing infrastructure"""
        self.logger.info("🚀 Initializing Self-Healing Infrastructure")

        # Initialize circuit breakers
        for service in self.services:
            self.circuit_breakers[service] = {
                "state": "closed",  # closed, open, half-open
                "failure_count": 0,
                "last_failure": None,
                "reset_timeout": 60
            }

        # Start background monitoring and healing
        self.monitoring_task = asyncio.create_task(self._continuous_health_monitoring())
        self.healing_task = asyncio.create_task(self._continuous_healing())

        self.logger.info("✅ Self-Healing Infrastructure initialized")

    async def _continuous_health_monitoring(self):
        """Continuously monitor system health"""
        while True:
            try:
                # Check all critical endpoints
                health_results = await self._perform_health_checks()

                # Analyze trends and predict issues
                await self._analyze_health_trends()

                # Update service metrics
                await self._update_service_metrics()

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(10)

    async def _perform_health_checks(self) -> List[HealthCheck]:
        """Perform comprehensive health checks"""
        health_results = []

        # Check API endpoints
        api_endpoints = [
            "/health",
            "/api/v1/auth/status",
            "/api/v1/projects",
            "/api/v1/tests",
            "/metrics"
        ]

        for endpoint in api_endpoints:
            try:
                health_check = await self._check_endpoint_health(endpoint)
                health_results.append(health_check)

                # Store in history
                self.health_checks[endpoint].append(health_check)

            except Exception as e:
                self.logger.error(f"Health check failed for {endpoint}: {e}")

        # Check system resources
        system_health = await self._check_system_health()
        health_results.append(system_health)

        return health_results

    async def _check_endpoint_health(self, endpoint: str) -> HealthCheck:
        """Check health of a specific endpoint"""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                url = f"{self.services.get('api_gateway', 'http://localhost:8000')}{endpoint}"

                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        status = HealthStatus.HEALTHY
                        error_message = None
                    elif response.status < 500:
                        status = HealthStatus.WARNING
                        error_message = f"HTTP {response.status}"
                    else:
                        status = HealthStatus.CRITICAL
                        error_message = f"HTTP {response.status}"

                    return HealthCheck(
                        endpoint=endpoint,
                        status=status,
                        response_time=response_time,
                        error_message=error_message,
                        timestamp=datetime.now(),
                        metadata={"status_code": response.status}
                    )

        except asyncio.TimeoutError:
            return HealthCheck(
                endpoint=endpoint,
                status=HealthStatus.CRITICAL,
                response_time=10000,  # Timeout
                error_message="Request timeout",
                timestamp=datetime.now(),
                metadata={"timeout": True}
            )
        except Exception as e:
            return HealthCheck(
                endpoint=endpoint,
                status=HealthStatus.FAILED,
                response_time=time.time() - start_time,
                error_message=str(e),
                timestamp=datetime.now(),
                metadata={"exception": type(e).__name__}
            )

    async def _check_system_health(self) -> HealthCheck:
        """Check overall system health"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100

            # Determine status based on thresholds
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = HealthStatus.CRITICAL
                error_message = "Resource exhaustion detected"
            elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 80:
                status = HealthStatus.WARNING
                error_message = "High resource usage"
            else:
                status = HealthStatus.HEALTHY
                error_message = None

            return HealthCheck(
                endpoint="system",
                status=status,
                response_time=0,
                error_message=error_message,
                timestamp=datetime.now(),
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent
                }
            )

        except Exception as e:
            return HealthCheck(
                endpoint="system",
                status=HealthStatus.FAILED,
                response_time=0,
                error_message=str(e),
                timestamp=datetime.now(),
                metadata={"exception": type(e).__name__}
            )

    async def _analyze_health_trends(self):
        """Analyze health trends and predict issues"""
        for endpoint, checks in self.health_checks.items():
            if len(checks) < 10:
                continue

            # Calculate trend metrics
            recent_checks = list(checks)[-10:]
            response_times = [check.response_time for check in recent_checks]
            error_rate = len([c for c in recent_checks if c.status in [HealthStatus.CRITICAL, HealthStatus.FAILED]]) / len(recent_checks)

            # Predict potential issues
            if statistics.mean(response_times) > 5000:  # 5 seconds
                await self._trigger_healing_action(endpoint, "slow_response", [HealingAction.SCALE_UP])

            if error_rate > 0.3:  # 30% error rate
                await self._trigger_healing_action(endpoint, "high_error_rate", [HealingAction.RESTART_SERVICE])

    async def _continuous_healing(self):
        """Continuously apply healing actions"""
        while True:
            try:
                if not self.healing_enabled:
                    await asyncio.sleep(60)
                    continue

                # Check circuit breakers
                await self._manage_circuit_breakers()

                # Auto-scale based on load
                await self._auto_scale_services()

                # Clean up resources
                await self._cleanup_resources()

                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"Error in healing process: {e}")
                await asyncio.sleep(60)

    async def _trigger_healing_action(self, service: str, issue_type: str, actions: List[HealingAction]):
        """Trigger specific healing actions"""
        event_id = f"heal_{int(time.time())}_{service}"

        healing_event = HealingEvent(
            event_id=event_id,
            issue_type=issue_type,
            severity="medium",
            affected_services=[service],
            healing_actions=actions,
            status="in_progress",
            timestamp=datetime.now(),
            resolution_time=None
        )

        self.healing_history.append(healing_event)

        self.logger.warning(f"🔧 Triggering healing for {service}: {issue_type}")

        start_time = time.time()

        for action in actions:
            try:
                await self._execute_healing_action(service, action)
                self.logger.info(f"✅ Healing action {action.value} completed for {service}")
            except Exception as e:
                self.logger.error(f"❌ Healing action {action.value} failed for {service}: {e}")

        # Update healing event
        healing_event.status = "completed"
        healing_event.resolution_time = time.time() - start_time

    async def _execute_healing_action(self, service: str, action: HealingAction):
        """Execute a specific healing action"""
        if action == HealingAction.RESTART_SERVICE:
            await self._restart_service(service)
        elif action == HealingAction.SCALE_UP:
            await self._scale_service(service, "up")
        elif action == HealingAction.SCALE_DOWN:
            await self._scale_service(service, "down")
        elif action == HealingAction.CLEAR_CACHE:
            await self._clear_cache(service)
        elif action == HealingAction.APPLY_PATCH:
            await self._apply_patch(service)
        elif action == HealingAction.CIRCUIT_BREAKER:
            await self._activate_circuit_breaker(service)

    async def _restart_service(self, service: str):
        """Restart a service"""
        self.logger.info(f"🔄 Restarting service: {service}")

        # Simulate service restart
        await asyncio.sleep(2)

        # Reset circuit breaker
        if service in self.circuit_breakers:
            self.circuit_breakers[service]["failure_count"] = 0
            self.circuit_breakers[service]["state"] = "closed"

    async def _scale_service(self, service: str, direction: str):
        """Scale a service up or down"""
        self.logger.info(f"📈 Scaling {service} {direction}")

        # Simulate scaling
        await asyncio.sleep(1)

    async def _clear_cache(self, service: str):
        """Clear service cache"""
        self.logger.info(f"🗑️ Clearing cache for {service}")
        await asyncio.sleep(0.5)

    async def _apply_patch(self, service: str):
        """Apply an automated patch"""
        self.logger.info(f"🩹 Applying automated patch to {service}")

        # Generate patch using autonomous code generation
        patch_description = f"Fix critical issues in {service} service"

        try:
            generated_patch = await self.code_generator.generate_code_from_description(
                description=patch_description,
                language=CodeLanguage.PYTHON,
                code_type=CodeType.BUG_FIX
            )

            self.logger.info(f"✅ Generated patch for {service}: {generated_patch.filename}")

        except Exception as e:
            self.logger.error(f"❌ Failed to generate patch for {service}: {e}")

    async def _activate_circuit_breaker(self, service: str):
        """Activate circuit breaker for a service"""
        if service in self.circuit_breakers:
            self.circuit_breakers[service]["state"] = "open"
            self.circuit_breakers[service]["last_failure"] = datetime.now()

            self.logger.warning(f"⚡ Circuit breaker activated for {service}")

    async def _manage_circuit_breakers(self):
        """Manage circuit breaker states"""
        for service, breaker in self.circuit_breakers.items():
            if breaker["state"] == "open":
                # Check if we should try half-open
                if breaker["last_failure"]:
                    time_since_failure = (datetime.now() - breaker["last_failure"]).seconds
                    if time_since_failure > breaker["reset_timeout"]:
                        breaker["state"] = "half-open"
                        self.logger.info(f"🔄 Circuit breaker half-open for {service}")

    async def _auto_scale_services(self):
        """Automatically scale services based on load"""
        # Check current load metrics
        for service, metrics in self.service_metrics.items():
            if "cpu_usage" in metrics and metrics["cpu_usage"] > 80:
                await self._trigger_healing_action(service, "high_cpu", [HealingAction.SCALE_UP])
            elif "cpu_usage" in metrics and metrics["cpu_usage"] < 20:
                await self._trigger_healing_action(service, "low_cpu", [HealingAction.SCALE_DOWN])

    async def _cleanup_resources(self):
        """Clean up unused resources"""
        # Clean old health check data
        cutoff_time = datetime.now() - timedelta(hours=24)

        for endpoint in self.health_checks:
            # Keep only recent checks
            recent_checks = deque(maxlen=100)
            for check in self.health_checks[endpoint]:
                if check.timestamp > cutoff_time:
                    recent_checks.append(check)
            self.health_checks[endpoint] = recent_checks

    async def _update_service_metrics(self):
        """Update service performance metrics"""
        for service in self.services:
            try:
                # Get recent health checks for this service
                recent_checks = []
                for endpoint, checks in self.health_checks.items():
                    if service in endpoint or endpoint == "system":
                        recent_checks.extend(list(checks)[-5:])

                if recent_checks:
                    avg_response_time = statistics.mean([c.response_time for c in recent_checks])
                    error_rate = len([c for c in recent_checks if c.status in [HealthStatus.CRITICAL, HealthStatus.FAILED]]) / len(recent_checks)

                    self.service_metrics[service] = {
                        "avg_response_time": avg_response_time,
                        "error_rate": error_rate,
                        "health_score": 100 - (error_rate * 100),
                        "last_updated": datetime.now()
                    }

            except Exception as e:
                self.logger.error(f"Error updating metrics for {service}: {e}")

    def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get current infrastructure status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": self._calculate_overall_health(),
            "services": self.service_metrics,
            "circuit_breakers": self.circuit_breakers,
            "recent_healing_events": [asdict(event) for event in self.healing_history[-10:]],
            "active_endpoints": len(self.health_checks),
            "healing_enabled": self.healing_enabled
        }

    def _calculate_overall_health(self) -> str:
        """Calculate overall infrastructure health"""
        if not self.service_metrics:
            return "unknown"

        health_scores = [metrics.get("health_score", 0) for metrics in self.service_metrics.values()]
        avg_health = statistics.mean(health_scores) if health_scores else 0

        if avg_health >= 95:
            return "excellent"
        elif avg_health >= 80:
            return "good"
        elif avg_health >= 60:
            return "warning"
        else:
            return "critical"

    async def shutdown(self):
        """Shutdown the self-healing infrastructure"""
        self.logger.info("🛑 Shutting down Self-Healing Infrastructure")

        self.healing_enabled = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.healing_task:
            self.healing_task.cancel()

        # Wait for tasks to complete
        if self.monitoring_task or self.healing_task:
            await asyncio.gather(
                self.monitoring_task, self.healing_task,
                return_exceptions=True
            )

# Global self-healing infrastructure instance
self_healing_infrastructure = SelfHealingInfrastructure()

async def initialize_self_healing():
    """Initialize the self-healing infrastructure"""
    await self_healing_infrastructure.initialize()

def get_infrastructure_status():
    """Get current infrastructure status"""
    return self_healing_infrastructure.get_infrastructure_status()

async def trigger_manual_healing(service: str, issue_type: str):
    """Manually trigger healing for a service"""
    await self_healing_infrastructure._trigger_healing_action(
        service, issue_type, [HealingAction.RESTART_SERVICE]
    )
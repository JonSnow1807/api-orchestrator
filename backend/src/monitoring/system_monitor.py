#!/usr/bin/env python3
"""
Real-Time System Monitoring and Health Checks
Advanced monitoring system for AI agents, performance metrics, and system health
"""

import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from collections import deque, defaultdict
import aiofiles


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime
    message: Optional[str] = None


@dataclass
class SystemAlert:
    alert_id: str
    severity: AlertSeverity
    component: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class RealTimeMonitor:
    """
    Comprehensive real-time monitoring system
    Tracks system health, performance metrics, and AI agent status
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Monitoring state
        self.is_monitoring = False
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.active_alerts: Dict[str, SystemAlert] = {}
        self.health_checks: Dict[str, HealthMetric] = {}

        # Performance tracking
        self.start_time = datetime.now()
        self.monitoring_interval = self.config.get("monitoring_interval", 30)  # seconds

        # Background tasks
        self._monitoring_tasks: List[asyncio.Task] = []

        # Thresholds (configurable)
        self.thresholds = {
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "disk_usage": {"warning": 85.0, "critical": 95.0},
            "response_time": {"warning": 2000.0, "critical": 5000.0},  # milliseconds
            "error_rate": {"warning": 5.0, "critical": 10.0},  # percentage
            "agent_failure_rate": {"warning": 15.0, "critical": 30.0},  # percentage
        }

    async def start_monitoring(self):
        """Start the real-time monitoring system"""
        if self.is_monitoring:
            self.logger.warning("Monitoring is already running")
            return

        self.logger.info("🔍 Starting Real-Time System Monitoring")
        self.is_monitoring = True

        # Start monitoring tasks
        self._monitoring_tasks = [
            asyncio.create_task(self._monitor_system_resources()),
            asyncio.create_task(self._monitor_ai_agents()),
            asyncio.create_task(self._monitor_application_health()),
            asyncio.create_task(self._process_alerts()),
            asyncio.create_task(self._cleanup_old_metrics()),
        ]

        self.logger.info("✅ Real-time monitoring started successfully")

    async def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.is_monitoring:
            return

        self.logger.info("🛑 Stopping Real-Time System Monitoring")
        self.is_monitoring = False

        # Cancel all monitoring tasks
        for task in self._monitoring_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks, return_exceptions=True)

        self.logger.info("✅ Monitoring stopped successfully")

    async def _monitor_system_resources(self):
        """Monitor CPU, memory, disk usage"""
        while self.is_monitoring:
            try:
                # CPU Usage
                cpu_percent = psutil.cpu_percent(interval=1)
                await self._record_metric("cpu_usage", cpu_percent, "%")

                # Memory Usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                await self._record_metric("memory_usage", memory_percent, "%")

                # Disk Usage
                disk = psutil.disk_usage("/")
                disk_percent = (disk.used / disk.total) * 100
                await self._record_metric("disk_usage", disk_percent, "%")

                # Network I/O
                network = psutil.net_io_counters()
                await self._record_metric(
                    "network_bytes_sent", network.bytes_sent, "bytes"
                )
                await self._record_metric(
                    "network_bytes_recv", network.bytes_recv, "bytes"
                )

                # Process count
                process_count = len(psutil.pids())
                await self._record_metric("process_count", process_count, "count")

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error monitoring system resources: {e}")
                await asyncio.sleep(60)

    async def _monitor_ai_agents(self):
        """Monitor AI agent health and performance"""
        while self.is_monitoring:
            try:
                # Import here to avoid circular imports
                from src.ai_agent_collaboration import get_collaboration_status

                # Get collaboration system status
                collab_status = get_collaboration_status()

                if collab_status:
                    # Agent availability
                    total_agents = collab_status.get("total_agents", 0)
                    active_agents = collab_status.get("active_agents", 0)
                    idle_agents = collab_status.get("idle_agents", 0)

                    # Calculate agent metrics
                    if total_agents > 0:
                        agent_utilization = (active_agents / total_agents) * 100
                        await self._record_metric(
                            "agent_utilization", agent_utilization, "%"
                        )

                    await self._record_metric("total_agents", total_agents, "count")
                    await self._record_metric("active_agents", active_agents, "count")
                    await self._record_metric("idle_agents", idle_agents, "count")

                    # Task metrics
                    active_tasks = collab_status.get("active_tasks", 0)
                    completed_tasks = collab_status.get("completed_tasks", 0)
                    await self._record_metric("active_tasks", active_tasks, "count")
                    await self._record_metric(
                        "completed_tasks", completed_tasks, "count"
                    )

                    # Collaboration metrics
                    metrics = collab_status.get("collaboration_metrics", {})
                    if metrics:
                        successful_collaborations = metrics.get(
                            "successful_collaborations", 0
                        )
                        failed_collaborations = metrics.get("failed_collaborations", 0)
                        total_collaborations = (
                            successful_collaborations + failed_collaborations
                        )

                        if total_collaborations > 0:
                            failure_rate = (
                                failed_collaborations / total_collaborations
                            ) * 100
                            await self._record_metric(
                                "agent_failure_rate", failure_rate, "%"
                            )

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error monitoring AI agents: {e}")
                await asyncio.sleep(60)

    async def _monitor_application_health(self):
        """Monitor application-specific health metrics"""
        while self.is_monitoring:
            try:
                # Uptime
                uptime = (datetime.now() - self.start_time).total_seconds()
                await self._record_metric("uptime", uptime, "seconds")

                # Response time simulation (would connect to actual app metrics)
                # This is a placeholder - in production, this would track actual request times
                import random

                simulated_response_time = random.uniform(50, 200)  # ms
                await self._record_metric(
                    "response_time", simulated_response_time, "ms"
                )

                # Error rate simulation
                simulated_error_rate = random.uniform(0, 3)  # %
                await self._record_metric("error_rate", simulated_error_rate, "%")

                # Database connection pool (if applicable)
                # This would monitor actual database connections
                await self._record_metric(
                    "db_connections", random.randint(1, 10), "count"
                )

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error monitoring application health: {e}")
                await asyncio.sleep(60)

    async def _record_metric(self, name: str, value: float, unit: str):
        """Record a metric and check thresholds"""
        timestamp = datetime.now()

        # Determine health status based on thresholds
        status = HealthStatus.HEALTHY
        message = None

        if name in self.thresholds:
            thresholds = self.thresholds[name]
            warning_threshold = thresholds["warning"]
            critical_threshold = thresholds["critical"]

            if value >= critical_threshold:
                status = HealthStatus.CRITICAL
                message = (
                    f"{name} is critical: {value}{unit} >= {critical_threshold}{unit}"
                )
                await self._create_alert(name, AlertSeverity.CRITICAL, message)
            elif value >= warning_threshold:
                status = HealthStatus.WARNING
                message = (
                    f"{name} is warning: {value}{unit} >= {warning_threshold}{unit}"
                )
                await self._create_alert(name, AlertSeverity.MEDIUM, message)
        else:
            warning_threshold = 0
            critical_threshold = 0

        # Create health metric
        metric = HealthMetric(
            name=name,
            value=value,
            unit=unit,
            status=status,
            threshold_warning=warning_threshold,
            threshold_critical=critical_threshold,
            timestamp=timestamp,
            message=message,
        )

        # Store metric
        self.health_checks[name] = metric
        self.metrics_history[name].append(
            {"value": value, "timestamp": timestamp.isoformat(), "status": status.value}
        )

    async def _create_alert(
        self, component: str, severity: AlertSeverity, message: str
    ):
        """Create a system alert"""
        alert_id = f"{component}_{int(time.time())}"

        # Check if similar alert already exists
        existing_alerts = [
            a
            for a in self.active_alerts.values()
            if a.component == component and not a.resolved
        ]

        if existing_alerts:
            # Update existing alert instead of creating new one
            existing_alert = existing_alerts[0]
            existing_alert.message = message
            existing_alert.timestamp = datetime.now()
            existing_alert.severity = severity
        else:
            # Create new alert
            alert = SystemAlert(
                alert_id=alert_id,
                severity=severity,
                component=component,
                message=message,
                timestamp=datetime.now(),
            )
            self.active_alerts[alert_id] = alert
            self.logger.warning(
                f"🚨 ALERT [{severity.value.upper()}] {component}: {message}"
            )

    async def _process_alerts(self):
        """Process and manage system alerts"""
        while self.is_monitoring:
            try:
                current_time = datetime.now()

                # Auto-resolve old alerts (after 5 minutes of no new occurrences)
                for alert_id, alert in list(self.active_alerts.items()):
                    if not alert.resolved:
                        time_since_alert = current_time - alert.timestamp
                        if time_since_alert > timedelta(minutes=5):
                            # Check if the condition is still present
                            metric = self.health_checks.get(alert.component)
                            if metric and metric.status == HealthStatus.HEALTHY:
                                alert.resolved = True
                                alert.resolution_time = current_time
                                self.logger.info(
                                    f"✅ RESOLVED: Alert {alert_id} for {alert.component}"
                                )

                # Clean up resolved alerts older than 1 hour
                cutoff_time = current_time - timedelta(hours=1)
                self.active_alerts = {
                    aid: alert
                    for aid, alert in self.active_alerts.items()
                    if not alert.resolved or alert.resolution_time > cutoff_time
                }

                await asyncio.sleep(60)  # Process alerts every minute

            except Exception as e:
                self.logger.error(f"Error processing alerts: {e}")
                await asyncio.sleep(60)

    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory growth"""
        while self.is_monitoring:
            try:
                cutoff_time = datetime.now() - timedelta(hours=24)

                for metric_name, history in self.metrics_history.items():
                    # Remove entries older than 24 hours
                    while (
                        history
                        and datetime.fromisoformat(history[0]["timestamp"])
                        < cutoff_time
                    ):
                        history.popleft()

                await asyncio.sleep(3600)  # Clean up every hour

            except Exception as e:
                self.logger.error(f"Error cleaning up metrics: {e}")
                await asyncio.sleep(3600)

    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        overall_status = HealthStatus.HEALTHY

        # Determine overall status based on individual metrics
        critical_count = sum(
            1 for m in self.health_checks.values() if m.status == HealthStatus.CRITICAL
        )
        warning_count = sum(
            1 for m in self.health_checks.values() if m.status == HealthStatus.WARNING
        )

        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning_count > 0:
            overall_status = HealthStatus.WARNING

        # Get current metrics
        current_metrics = {}
        for name, metric in self.health_checks.items():
            current_metrics[name] = {
                "value": metric.value,
                "unit": metric.unit,
                "status": metric.status.value,
                "last_updated": metric.timestamp.isoformat(),
                "message": metric.message,
            }

        # Get active alerts
        active_alerts = []
        for alert in self.active_alerts.values():
            if not alert.resolved:
                active_alerts.append(
                    {
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.value,
                        "component": alert.component,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                )

        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "metrics": current_metrics,
            "active_alerts": active_alerts,
            "alert_summary": {
                "total_active": len(active_alerts),
                "critical": len(
                    [a for a in active_alerts if a["severity"] == "critical"]
                ),
                "high": len([a for a in active_alerts if a["severity"] == "high"]),
                "medium": len([a for a in active_alerts if a["severity"] == "medium"]),
                "low": len([a for a in active_alerts if a["severity"] == "low"]),
            },
            "metric_summary": {
                "total_metrics": len(self.health_checks),
                "healthy": len(
                    [
                        m
                        for m in self.health_checks.values()
                        if m.status == HealthStatus.HEALTHY
                    ]
                ),
                "warning": warning_count,
                "critical": critical_count,
            },
        }

    def get_metric_history(
        self, metric_name: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric"""
        if metric_name not in self.metrics_history:
            return []

        history = list(self.metrics_history[metric_name])
        return history[-limit:] if limit else history

    async def save_health_report(self, filepath: str = None):
        """Save comprehensive health report to file"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"/tmp/health_report_{timestamp}.json"

        health_data = self.get_system_health()

        # Add historical data
        health_data["metric_history"] = {}
        for metric_name in self.metrics_history.keys():
            health_data["metric_history"][metric_name] = self.get_metric_history(
                metric_name, 50
            )

        try:
            async with aiofiles.open(filepath, "w") as f:
                await f.write(json.dumps(health_data, indent=2, default=str))
            self.logger.info(f"📄 Health report saved to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to save health report: {e}")
            return None


# Global monitor instance
system_monitor = RealTimeMonitor()


# Convenience functions
async def start_system_monitoring():
    """Start the global system monitor"""
    await system_monitor.start_monitoring()


async def stop_system_monitoring():
    """Stop the global system monitor"""
    await system_monitor.stop_monitoring()


def get_system_health():
    """Get current system health"""
    return system_monitor.get_system_health()


def get_metric_history(metric_name: str, limit: int = 100):
    """Get metric history"""
    return system_monitor.get_metric_history(metric_name, limit)


async def generate_health_report(filepath: str = None):
    """Generate and save health report"""
    return await system_monitor.save_health_report(filepath)

"""
PerformanceAgent - Real-time API performance monitoring and optimization agent
Continuously monitors API performance, detects issues, and provides optimization recommendations
"""

import asyncio
import json
import time
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading


@dataclass
class PerformanceMetric:
    """Represents a performance metric data point"""

    timestamp: datetime
    endpoint: str
    method: str
    response_time: float
    status_code: int
    content_length: int
    memory_usage: float
    cpu_usage: float
    error_message: Optional[str] = None


@dataclass
class PerformanceAlert:
    """Represents a performance alert"""

    alert_id: str
    severity: str  # critical, warning, info
    title: str
    description: str
    timestamp: datetime
    endpoint: str
    metric_type: str
    threshold_value: float
    actual_value: float
    recommendations: List[str]


@dataclass
class PerformanceSummary:
    """Summary of performance metrics"""

    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    throughput: float
    availability: float
    total_requests: int


class PerformanceAgent:
    """
    Enterprise-grade performance monitoring agent
    Real-time performance analysis with intelligent alerting and optimization suggestions
    """

    def __init__(self):
        self.name = "PerformanceAgent"
        self.version = "1.0.0"
        self.metrics_buffer = deque(maxlen=10000)  # Store last 10k metrics
        self.alerts_history = []
        self.performance_baselines = {}
        self.monitoring_active = True

        # Thresholds for different alert levels
        self.thresholds = {
            "critical": {
                "response_time": 10.0,  # seconds
                "error_rate": 0.1,  # 10%
                "availability": 0.95,  # 95%
            },
            "warning": {
                "response_time": 5.0,  # seconds
                "error_rate": 0.05,  # 5%
                "availability": 0.98,  # 98%
            },
        }

        # Start background monitoring
        self._start_background_monitoring()

    def _start_background_monitoring(self):
        """Start background monitoring thread"""

        def monitor():
            while self.monitoring_active:
                try:
                    self._check_performance_alerts()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    print(f"Performance monitoring error: {e}")

        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()

    async def record_performance_metric(self, metric: PerformanceMetric) -> None:
        """Record a new performance metric"""
        self.metrics_buffer.append(metric)

        # Update baselines periodically
        if len(self.metrics_buffer) % 100 == 0:
            await self._update_baselines()

    async def get_real_time_performance(
        self, endpoint: Optional[str] = None, time_window: int = 300
    ) -> Dict[str, Any]:
        """Get real-time performance metrics for the last N seconds"""
        try:
            cutoff_time = datetime.now() - timedelta(seconds=time_window)
            recent_metrics = [
                m for m in self.metrics_buffer if m.timestamp >= cutoff_time
            ]

            if endpoint:
                recent_metrics = [m for m in recent_metrics if m.endpoint == endpoint]

            if not recent_metrics:
                return {
                    "status": "no_data",
                    "message": f"No performance data available for the last {time_window} seconds",
                }

            # Calculate performance summary
            summary = await self._calculate_performance_summary(recent_metrics)

            # Get current alerts
            active_alerts = await self._get_active_alerts(endpoint)

            # Performance trends
            trends = await self._calculate_performance_trends(recent_metrics)

            # Optimization recommendations
            recommendations = await self._generate_performance_recommendations(
                summary, recent_metrics
            )

            return {
                "timestamp": datetime.now().isoformat(),
                "time_window_seconds": time_window,
                "endpoint": endpoint or "all_endpoints",
                "summary": asdict(summary),
                "active_alerts": [asdict(alert) for alert in active_alerts],
                "trends": trends,
                "recommendations": recommendations,
                "health_score": await self._calculate_health_score(summary),
                "total_requests": len(recent_metrics),
            }

        except Exception as e:
            return {
                "error": f"Failed to get real-time performance data: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    async def _calculate_performance_summary(
        self, metrics: List[PerformanceMetric]
    ) -> PerformanceSummary:
        """Calculate performance summary from metrics"""
        if not metrics:
            return PerformanceSummary(0, 0, 0, 0, 0, 0, 0)

        response_times = [m.response_time for m in metrics]
        error_count = sum(1 for m in metrics if m.status_code >= 400)
        total_requests = len(metrics)

        # Calculate percentiles
        response_times_sorted = sorted(response_times)
        p95_index = int(0.95 * len(response_times_sorted))
        p99_index = int(0.99 * len(response_times_sorted))

        # Calculate throughput (requests per second)
        if metrics:
            time_span = (metrics[-1].timestamp - metrics[0].timestamp).total_seconds()
            throughput = total_requests / max(time_span, 1)
        else:
            throughput = 0

        return PerformanceSummary(
            avg_response_time=statistics.mean(response_times),
            p95_response_time=response_times_sorted[p95_index]
            if response_times_sorted
            else 0,
            p99_response_time=response_times_sorted[p99_index]
            if response_times_sorted
            else 0,
            error_rate=error_count / total_requests,
            throughput=throughput,
            availability=1 - (error_count / total_requests),
            total_requests=total_requests,
        )

    def _check_performance_alerts(self):
        """Check for performance issues and generate alerts"""
        try:
            # Get recent metrics (last 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            recent_metrics = [
                m for m in self.metrics_buffer if m.timestamp >= cutoff_time
            ]

            if len(recent_metrics) < 10:  # Need minimum data points
                return

            # Group by endpoint for analysis
            endpoint_metrics = defaultdict(list)
            for metric in recent_metrics:
                endpoint_metrics[metric.endpoint].append(metric)

            # Check each endpoint
            for endpoint, metrics in endpoint_metrics.items():
                self._check_endpoint_alerts(endpoint, metrics)

        except Exception as e:
            print(f"Alert checking error: {e}")

    def _check_endpoint_alerts(self, endpoint: str, metrics: List[PerformanceMetric]):
        """Check for alerts on a specific endpoint"""
        if not metrics:
            return

        # Calculate current performance
        avg_response_time = statistics.mean([m.response_time for m in metrics])
        error_rate = sum(1 for m in metrics if m.status_code >= 400) / len(metrics)

        # Check response time alerts
        if avg_response_time > self.thresholds["critical"]["response_time"]:
            alert = PerformanceAlert(
                alert_id=f"{endpoint}_response_time_{int(time.time())}",
                severity="critical",
                title="Critical Response Time",
                description=f"Response time {avg_response_time:.2f}s exceeds critical threshold",
                timestamp=datetime.now(),
                endpoint=endpoint,
                metric_type="response_time",
                threshold_value=self.thresholds["critical"]["response_time"],
                actual_value=avg_response_time,
                recommendations=[
                    "Check database query performance",
                    "Review endpoint logic for optimization opportunities",
                    "Consider implementing caching",
                    "Scale infrastructure if needed",
                ],
            )
            self.alerts_history.append(alert)

        elif avg_response_time > self.thresholds["warning"]["response_time"]:
            alert = PerformanceAlert(
                alert_id=f"{endpoint}_response_time_{int(time.time())}",
                severity="warning",
                title="Slow Response Time",
                description=f"Response time {avg_response_time:.2f}s exceeds warning threshold",
                timestamp=datetime.now(),
                endpoint=endpoint,
                metric_type="response_time",
                threshold_value=self.thresholds["warning"]["response_time"],
                actual_value=avg_response_time,
                recommendations=[
                    "Monitor endpoint performance closely",
                    "Consider optimizing database queries",
                    "Review code for performance bottlenecks",
                ],
            )
            self.alerts_history.append(alert)

        # Check error rate alerts
        if error_rate > self.thresholds["critical"]["error_rate"]:
            alert = PerformanceAlert(
                alert_id=f"{endpoint}_error_rate_{int(time.time())}",
                severity="critical",
                title="High Error Rate",
                description=f"Error rate {error_rate:.1%} exceeds critical threshold",
                timestamp=datetime.now(),
                endpoint=endpoint,
                metric_type="error_rate",
                threshold_value=self.thresholds["critical"]["error_rate"],
                actual_value=error_rate,
                recommendations=[
                    "Investigate error causes immediately",
                    "Check endpoint logic and dependencies",
                    "Review recent deployments",
                    "Implement circuit breaker pattern",
                ],
            )
            self.alerts_history.append(alert)

    async def _get_active_alerts(
        self, endpoint: Optional[str] = None
    ) -> List[PerformanceAlert]:
        """Get active alerts (last hour)"""
        cutoff_time = datetime.now() - timedelta(hours=1)
        active_alerts = [a for a in self.alerts_history if a.timestamp >= cutoff_time]

        if endpoint:
            active_alerts = [a for a in active_alerts if a.endpoint == endpoint]

        return sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)[:10]

    async def _calculate_performance_trends(
        self, metrics: List[PerformanceMetric]
    ) -> Dict[str, Any]:
        """Calculate performance trends over time"""
        if len(metrics) < 2:
            return {"trend": "insufficient_data"}

        # Split metrics into time buckets (e.g., 1-minute buckets)
        bucket_size = 60  # seconds
        buckets = defaultdict(list)

        start_time = min(m.timestamp for m in metrics)
        for metric in metrics:
            bucket_key = int(
                (metric.timestamp - start_time).total_seconds() // bucket_size
            )
            buckets[bucket_key].append(metric)

        # Calculate trend data
        trend_data = []
        for bucket_key in sorted(buckets.keys()):
            bucket_metrics = buckets[bucket_key]
            avg_response = statistics.mean([m.response_time for m in bucket_metrics])
            error_rate = sum(1 for m in bucket_metrics if m.status_code >= 400) / len(
                bucket_metrics
            )

            trend_data.append(
                {
                    "time_bucket": bucket_key,
                    "avg_response_time": round(avg_response, 3),
                    "error_rate": round(error_rate, 3),
                    "request_count": len(bucket_metrics),
                }
            )

        # Calculate overall trend direction
        if len(trend_data) >= 2:
            first_half_avg = statistics.mean(
                [d["avg_response_time"] for d in trend_data[: len(trend_data) // 2]]
            )
            second_half_avg = statistics.mean(
                [d["avg_response_time"] for d in trend_data[len(trend_data) // 2 :]]
            )

            if second_half_avg > first_half_avg * 1.1:
                trend_direction = "degrading"
            elif second_half_avg < first_half_avg * 0.9:
                trend_direction = "improving"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "unknown"

        return {
            "trend_direction": trend_direction,
            "data_points": trend_data,
            "bucket_size_seconds": bucket_size,
        }

    async def _generate_performance_recommendations(
        self, summary: PerformanceSummary, metrics: List[PerformanceMetric]
    ) -> List[Dict[str, str]]:
        """Generate performance optimization recommendations"""
        recommendations = []

        # Response time recommendations
        if summary.avg_response_time > 2.0:
            recommendations.append(
                {
                    "type": "response_time",
                    "priority": "high" if summary.avg_response_time > 5.0 else "medium",
                    "title": "Optimize Response Time",
                    "description": f"Average response time ({summary.avg_response_time:.2f}s) can be improved",
                    "actions": [
                        "Implement caching for frequently accessed data",
                        "Optimize database queries",
                        "Consider asynchronous processing for heavy operations",
                        "Review code for performance bottlenecks",
                    ],
                }
            )

        # Error rate recommendations
        if summary.error_rate > 0.01:  # More than 1% errors
            recommendations.append(
                {
                    "type": "error_rate",
                    "priority": "high" if summary.error_rate > 0.05 else "medium",
                    "title": "Reduce Error Rate",
                    "description": f"Error rate ({summary.error_rate:.1%}) should be investigated",
                    "actions": [
                        "Analyze error logs for common failure patterns",
                        "Implement better input validation",
                        "Add retry mechanisms for transient failures",
                        "Improve error handling and recovery",
                    ],
                }
            )

        # Throughput recommendations
        if summary.throughput < 10:  # Low throughput
            recommendations.append(
                {
                    "type": "throughput",
                    "priority": "medium",
                    "title": "Improve Throughput",
                    "description": f"Current throughput ({summary.throughput:.1f} req/s) could be optimized",
                    "actions": [
                        "Implement connection pooling",
                        "Optimize resource utilization",
                        "Consider horizontal scaling",
                        "Review concurrent request handling",
                    ],
                }
            )

        # P99 latency recommendations
        if summary.p99_response_time > summary.avg_response_time * 3:
            recommendations.append(
                {
                    "type": "latency_variance",
                    "priority": "medium",
                    "title": "Reduce Latency Variance",
                    "description": "High P99 latency indicates inconsistent performance",
                    "actions": [
                        "Investigate outlier requests",
                        "Implement request timeout policies",
                        "Optimize resource contention scenarios",
                        "Consider load balancing improvements",
                    ],
                }
            )

        return recommendations[:5]  # Return top 5 recommendations

    async def _calculate_health_score(self, summary: PerformanceSummary) -> int:
        """Calculate overall health score (0-100)"""
        score = 100

        # Response time impact (0-40 points)
        if summary.avg_response_time > 10:
            score -= 40
        elif summary.avg_response_time > 5:
            score -= 30
        elif summary.avg_response_time > 2:
            score -= 15
        elif summary.avg_response_time > 1:
            score -= 5

        # Error rate impact (0-30 points)
        if summary.error_rate > 0.1:
            score -= 30
        elif summary.error_rate > 0.05:
            score -= 20
        elif summary.error_rate > 0.01:
            score -= 10
        elif summary.error_rate > 0.005:
            score -= 5

        # Availability impact (0-20 points)
        availability_loss = (1 - summary.availability) * 100
        score -= min(20, availability_loss * 2)

        # Throughput impact (0-10 points)
        if summary.throughput < 1:
            score -= 10
        elif summary.throughput < 5:
            score -= 5

        return max(0, min(100, int(score)))

    async def _update_baselines(self):
        """Update performance baselines based on historical data"""
        try:
            # Get last 24 hours of data for baseline
            cutoff_time = datetime.now() - timedelta(hours=24)
            baseline_metrics = [
                m for m in self.metrics_buffer if m.timestamp >= cutoff_time
            ]

            if len(baseline_metrics) < 100:  # Need sufficient data
                return

            # Group by endpoint
            endpoint_baselines = defaultdict(list)
            for metric in baseline_metrics:
                endpoint_baselines[metric.endpoint].append(metric.response_time)

            # Calculate baselines for each endpoint
            for endpoint, response_times in endpoint_baselines.items():
                if len(response_times) >= 10:
                    self.performance_baselines[endpoint] = {
                        "avg_response_time": statistics.mean(response_times),
                        "p95_response_time": statistics.quantiles(response_times, n=20)[
                            18
                        ],  # 95th percentile
                        "baseline_updated": datetime.now().isoformat(),
                    }

        except Exception as e:
            print(f"Baseline update error: {e}")

    async def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        try:
            # Get metrics for last hour
            recent_metrics = [
                m
                for m in self.metrics_buffer
                if m.timestamp >= datetime.now() - timedelta(hours=1)
            ]

            if not recent_metrics:
                return {
                    "status": "no_data",
                    "message": "No recent performance data available",
                }

            # Overall summary
            summary = await self._calculate_performance_summary(recent_metrics)

            # Top slow endpoints
            endpoint_performance = defaultdict(list)
            for metric in recent_metrics:
                endpoint_performance[metric.endpoint].append(metric.response_time)

            slow_endpoints = []
            for endpoint, times in endpoint_performance.items():
                avg_time = statistics.mean(times)
                slow_endpoints.append(
                    {
                        "endpoint": endpoint,
                        "avg_response_time": round(avg_time, 3),
                        "request_count": len(times),
                    }
                )

            slow_endpoints = sorted(
                slow_endpoints, key=lambda x: x["avg_response_time"], reverse=True
            )[:5]

            # Active alerts
            active_alerts = await self._get_active_alerts()

            # System health
            health_score = await self._calculate_health_score(summary)

            return {
                "timestamp": datetime.now().isoformat(),
                "summary": asdict(summary),
                "health_score": health_score,
                "slow_endpoints": slow_endpoints,
                "active_alerts": len(active_alerts),
                "critical_alerts": len(
                    [a for a in active_alerts if a.severity == "critical"]
                ),
                "performance_trends": await self._calculate_performance_trends(
                    recent_metrics
                ),
                "monitoring_status": "active" if self.monitoring_active else "inactive",
                "total_metrics_collected": len(self.metrics_buffer),
            }

        except Exception as e:
            return {
                "error": f"Failed to get dashboard data: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False

    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and statistics"""
        return {
            "name": self.name,
            "version": self.version,
            "monitoring_active": self.monitoring_active,
            "metrics_in_buffer": len(self.metrics_buffer),
            "alerts_history_count": len(self.alerts_history),
            "baselines_count": len(self.performance_baselines),
            "uptime": "Runtime monitoring active",
        }


# Usage example and testing
if __name__ == "__main__":

    async def test_performance_agent():
        agent = PerformanceAgent()

        # Create sample performance metrics
        sample_metrics = [
            PerformanceMetric(
                timestamp=datetime.now() - timedelta(seconds=i * 10),
                endpoint="/api/users",
                method="GET",
                response_time=1.5 + (i * 0.1),  # Gradually increasing response time
                status_code=200 if i < 8 else 500,  # Some errors at the end
                content_length=1024,
                memory_usage=50.0,
                cpu_usage=25.0,
            )
            for i in range(10)
        ]

        # Record metrics
        for metric in sample_metrics:
            await agent.record_performance_metric(metric)

        # Get real-time performance
        performance = await agent.get_real_time_performance()
        print("Performance Data:", json.dumps(performance, indent=2))

        # Get dashboard data
        dashboard = await agent.get_performance_dashboard_data()
        print("\nDashboard Data:", json.dumps(dashboard, indent=2))

        # Stop monitoring
        agent.stop_monitoring()

    # Run test
    asyncio.run(test_performance_agent())

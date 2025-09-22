"""
API Insights & Observability - Real-time API intelligence
Advanced analytics, failure detection, and proactive monitoring
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass
import statistics
import numpy as np
from collections import defaultdict, deque
import hashlib


class InsightType(Enum):
    """Types of insights"""

    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_SPIKE = "error_spike"
    TRAFFIC_ANOMALY = "traffic_anomaly"
    ENDPOINT_DEPRECATION = "endpoint_deprecation"
    SECURITY_THREAT = "security_threat"
    SLA_VIOLATION = "sla_violation"
    USAGE_PATTERN = "usage_pattern"
    DEPENDENCY_ISSUE = "dependency_issue"
    VERSION_MIGRATION = "version_migration"
    CONSUMER_BEHAVIOR = "consumer_behavior"


class InsightSeverity(Enum):
    """Severity levels for insights"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MetricAggregation(Enum):
    """Metric aggregation types"""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class APIMetric:
    """Individual API metric"""

    timestamp: datetime
    endpoint: str
    method: str
    version: str
    response_time_ms: float
    status_code: int
    consumer_id: Optional[str]
    error_message: Optional[str]
    request_size: int
    response_size: int


class Insight(BaseModel):
    """API insight/alert"""

    id: str = Field(
        default_factory=lambda: hashlib.sha256(
            str(datetime.now()).encode()
        ).hexdigest()[:16]
    )
    type: InsightType
    severity: InsightSeverity
    title: str
    description: str
    affected_endpoints: List[str]
    metrics: Dict[str, Any]
    recommendations: List[str]
    detected_at: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class FailurePattern(BaseModel):
    """Detected failure pattern"""

    pattern_id: str
    pattern_type: str  # timeout, rate_limit, auth_failure, etc.
    endpoints: List[str]
    frequency: int
    time_window: str
    error_codes: List[int]
    common_factors: Dict[str, Any]
    first_seen: datetime
    last_seen: datetime


class EndpointHealth(BaseModel):
    """Endpoint health status"""

    endpoint: str
    method: str
    version: str
    health_score: float  # 0-100
    availability: float  # Uptime percentage
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    request_volume: int
    trend: str  # improving, stable, degrading
    issues: List[str]


class VersionUsage(BaseModel):
    """API version usage statistics"""

    version: str
    usage_percentage: float
    total_requests: int
    unique_consumers: int
    deprecated: bool
    sunset_date: Optional[datetime]
    migration_status: Dict[str, int]  # consumer_id -> migration %


class ConsumerAnalytics(BaseModel):
    """Consumer behavior analytics"""

    consumer_id: str
    consumer_name: str
    total_requests: int
    error_rate: float
    avg_response_time: float
    most_used_endpoints: List[Dict[str, Any]]
    usage_pattern: str  # regular, sporadic, increasing, decreasing
    api_versions_used: List[str]
    last_activity: datetime
    anomaly_score: float  # 0-1, higher means more anomalous


class APIInsights:
    """Advanced API insights and observability engine"""

    def __init__(self):
        self.metrics_buffer: deque = deque(maxlen=100000)
        self.insights: List[Insight] = []
        self.failure_patterns: Dict[str, FailurePattern] = {}
        self.endpoint_health: Dict[str, EndpointHealth] = {}
        self.version_usage: Dict[str, VersionUsage] = {}
        self.consumer_analytics: Dict[str, ConsumerAnalytics] = {}

        # Anomaly detection parameters
        self.baseline_window = timedelta(days=7)
        self.anomaly_threshold = 2.5  # Standard deviations

        # SLA thresholds
        self.sla_thresholds = {
            "response_time_ms": 1000,
            "error_rate": 0.01,
            "availability": 0.999,
        }

        # Start background analysis
        self.analysis_task = None
        self.running = True

    async def start_analysis(self):
        """Start continuous analysis"""
        self.analysis_task = asyncio.create_task(self._continuous_analysis())

    async def stop_analysis(self):
        """Stop analysis"""
        self.running = False
        if self.analysis_task:
            await self.analysis_task

    async def ingest_metric(self, metric: APIMetric):
        """Ingest a new API metric"""
        self.metrics_buffer.append(metric)

        # Update endpoint health
        endpoint_key = f"{metric.method}:{metric.endpoint}:{metric.version}"
        if endpoint_key not in self.endpoint_health:
            self.endpoint_health[endpoint_key] = EndpointHealth(
                endpoint=metric.endpoint,
                method=metric.method,
                version=metric.version,
                health_score=100.0,
                availability=100.0,
                avg_response_time=metric.response_time_ms,
                p95_response_time=metric.response_time_ms,
                p99_response_time=metric.response_time_ms,
                error_rate=0.0,
                request_volume=0,
                trend="stable",
                issues=[],
            )

        # Update real-time stats
        health = self.endpoint_health[endpoint_key]
        health.request_volume += 1

        # Update response time with exponential moving average
        alpha = 0.1
        health.avg_response_time = (
            alpha * metric.response_time_ms + (1 - alpha) * health.avg_response_time
        )

        # Update error rate
        if metric.status_code >= 400:
            health.error_rate = alpha * 1.0 + (1 - alpha) * health.error_rate
        else:
            health.error_rate = alpha * 0.0 + (1 - alpha) * health.error_rate

        # Check for immediate alerts
        await self._check_immediate_alerts(metric)

    async def _continuous_analysis(self):
        """Run continuous analysis in background"""
        while self.running:
            try:
                # Run different analyses
                await self._analyze_performance_trends()
                await self._detect_failure_patterns()
                await self._analyze_version_migration()
                await self._analyze_consumer_behavior()
                await self._check_sla_violations()
                await self._detect_anomalies()

                # Sleep before next analysis cycle
                await asyncio.sleep(60)  # Run every minute

            except Exception as e:
                print(f"Analysis error: {e}")
                await asyncio.sleep(60)

    async def _analyze_performance_trends(self):
        """Analyze performance trends"""

        # Group metrics by endpoint
        endpoint_metrics = defaultdict(list)
        cutoff_time = datetime.now() - timedelta(hours=1)

        for metric in self.metrics_buffer:
            if metric.timestamp > cutoff_time:
                key = f"{metric.method}:{metric.endpoint}:{metric.version}"
                endpoint_metrics[key].append(metric)

        for endpoint_key, metrics in endpoint_metrics.items():
            if len(metrics) < 10:
                continue

            response_times = [m.response_time_ms for m in metrics]

            # Calculate percentiles
            p50 = np.percentile(response_times, 50)
            p95 = np.percentile(response_times, 95)
            p99 = np.percentile(response_times, 99)

            # Update health
            if endpoint_key in self.endpoint_health:
                health = self.endpoint_health[endpoint_key]
                health.p95_response_time = p95
                health.p99_response_time = p99

                # Detect degradation
                if p95 > self.sla_thresholds["response_time_ms"]:
                    insight = Insight(
                        type=InsightType.PERFORMANCE_DEGRADATION,
                        severity=InsightSeverity.HIGH,
                        title=f"Performance degradation detected on {endpoint_key}",
                        description=f"P95 response time ({p95:.0f}ms) exceeds SLA threshold",
                        affected_endpoints=[endpoint_key],
                        metrics={
                            "p50": p50,
                            "p95": p95,
                            "p99": p99,
                            "threshold": self.sla_thresholds["response_time_ms"],
                        },
                        recommendations=[
                            "Review recent deployments",
                            "Check database query performance",
                            "Consider implementing caching",
                            "Scale up resources if needed",
                        ],
                    )
                    self.insights.append(insight)

    async def _detect_failure_patterns(self):
        """Detect recurring failure patterns"""

        # Group errors by type and endpoint
        error_groups = defaultdict(list)
        cutoff_time = datetime.now() - timedelta(hours=1)

        for metric in self.metrics_buffer:
            if metric.timestamp > cutoff_time and metric.status_code >= 400:
                key = f"{metric.status_code}:{metric.endpoint}"
                error_groups[key].append(metric)

        for error_key, errors in error_groups.items():
            if len(errors) < 5:
                continue

            status_code, endpoint = error_key.split(":", 1)

            # Check for patterns
            pattern_id = hashlib.sha256(error_key.encode()).hexdigest()[:8]

            if pattern_id not in self.failure_patterns:
                pattern = FailurePattern(
                    pattern_id=pattern_id,
                    pattern_type=self._classify_error_pattern(int(status_code)),
                    endpoints=[endpoint],
                    frequency=len(errors),
                    time_window="1h",
                    error_codes=[int(status_code)],
                    common_factors={},
                    first_seen=min(e.timestamp for e in errors),
                    last_seen=max(e.timestamp for e in errors),
                )

                self.failure_patterns[pattern_id] = pattern

                # Create insight
                insight = Insight(
                    type=InsightType.ERROR_SPIKE,
                    severity=InsightSeverity.HIGH
                    if int(status_code) >= 500
                    else InsightSeverity.MEDIUM,
                    title=f"Failure pattern detected: {pattern.pattern_type}",
                    description=f"{len(errors)} errors on {endpoint} in the last hour",
                    affected_endpoints=[endpoint],
                    metrics={
                        "error_count": len(errors),
                        "status_code": status_code,
                        "pattern_type": pattern.pattern_type,
                    },
                    recommendations=self._get_error_recommendations(
                        pattern.pattern_type
                    ),
                )
                self.insights.append(insight)

    async def _analyze_version_migration(self):
        """Analyze API version migration status"""

        # Count requests per version
        version_counts = defaultdict(lambda: {"requests": 0, "consumers": set()})

        for metric in self.metrics_buffer:
            version_counts[metric.version]["requests"] += 1
            if metric.consumer_id:
                version_counts[metric.version]["consumers"].add(metric.consumer_id)

        total_requests = sum(v["requests"] for v in version_counts.values())

        for version, data in version_counts.items():
            usage = VersionUsage(
                version=version,
                usage_percentage=(data["requests"] / total_requests * 100)
                if total_requests > 0
                else 0,
                total_requests=data["requests"],
                unique_consumers=len(data["consumers"]),
                deprecated="deprecated" in version.lower()
                or version < "v2",  # Example logic
                sunset_date=datetime.now() + timedelta(days=90)
                if "v1" in version
                else None,
                migration_status={},
            )

            self.version_usage[version] = usage

            # Alert on deprecated version usage
            if usage.deprecated and usage.usage_percentage > 10:
                insight = Insight(
                    type=InsightType.VERSION_MIGRATION,
                    severity=InsightSeverity.MEDIUM,
                    title=f"Deprecated version {version} still in use",
                    description=f"{usage.usage_percentage:.1f}% of traffic still using deprecated version",
                    affected_endpoints=[],
                    metrics={
                        "version": version,
                        "usage_percentage": usage.usage_percentage,
                        "unique_consumers": usage.unique_consumers,
                    },
                    recommendations=[
                        f"Notify {usage.unique_consumers} consumers about migration",
                        "Provide migration guide and tools",
                        "Set clear sunset date",
                        "Implement version redirection if possible",
                    ],
                )
                self.insights.append(insight)

    async def _analyze_consumer_behavior(self):
        """Analyze consumer behavior patterns"""

        # Group metrics by consumer
        consumer_metrics = defaultdict(list)

        for metric in self.metrics_buffer:
            if metric.consumer_id:
                consumer_metrics[metric.consumer_id].append(metric)

        for consumer_id, metrics in consumer_metrics.items():
            if not metrics:
                continue

            # Calculate consumer analytics
            total_requests = len(metrics)
            errors = [m for m in metrics if m.status_code >= 400]
            error_rate = len(errors) / total_requests if total_requests > 0 else 0
            avg_response_time = statistics.mean(m.response_time_ms for m in metrics)

            # Find most used endpoints
            endpoint_counts = defaultdict(int)
            for m in metrics:
                endpoint_counts[f"{m.method} {m.endpoint}"] += 1

            most_used = sorted(
                [{"endpoint": k, "count": v} for k, v in endpoint_counts.items()],
                key=lambda x: x["count"],
                reverse=True,
            )[:5]

            # Detect usage pattern
            usage_pattern = self._detect_usage_pattern(metrics)

            # Calculate anomaly score
            anomaly_score = self._calculate_anomaly_score(metrics)

            analytics = ConsumerAnalytics(
                consumer_id=consumer_id,
                consumer_name=f"Consumer {consumer_id[:8]}",  # Placeholder
                total_requests=total_requests,
                error_rate=error_rate,
                avg_response_time=avg_response_time,
                most_used_endpoints=most_used,
                usage_pattern=usage_pattern,
                api_versions_used=list(set(m.version for m in metrics)),
                last_activity=max(m.timestamp for m in metrics),
                anomaly_score=anomaly_score,
            )

            self.consumer_analytics[consumer_id] = analytics

            # Alert on anomalous behavior
            if anomaly_score > 0.8:
                insight = Insight(
                    type=InsightType.CONSUMER_BEHAVIOR,
                    severity=InsightSeverity.MEDIUM,
                    title=f"Anomalous behavior detected for consumer {consumer_id[:8]}",
                    description=f"Consumer showing unusual API usage patterns",
                    affected_endpoints=[e["endpoint"] for e in most_used],
                    metrics={
                        "anomaly_score": anomaly_score,
                        "error_rate": error_rate,
                        "usage_pattern": usage_pattern,
                    },
                    recommendations=[
                        "Review consumer's recent activity",
                        "Check for potential security issues",
                        "Contact consumer if behavior persists",
                    ],
                )
                self.insights.append(insight)

    async def _check_sla_violations(self):
        """Check for SLA violations"""

        for endpoint_key, health in self.endpoint_health.items():
            violations = []

            if health.avg_response_time > self.sla_thresholds["response_time_ms"]:
                violations.append(
                    f"Response time {health.avg_response_time:.0f}ms exceeds SLA"
                )

            if health.error_rate > self.sla_thresholds["error_rate"]:
                violations.append(f"Error rate {health.error_rate:.2%} exceeds SLA")

            if health.availability < self.sla_thresholds["availability"] * 100:
                violations.append(f"Availability {health.availability:.2f}% below SLA")

            if violations:
                insight = Insight(
                    type=InsightType.SLA_VIOLATION,
                    severity=InsightSeverity.CRITICAL,
                    title=f"SLA violation on {endpoint_key}",
                    description=" | ".join(violations),
                    affected_endpoints=[endpoint_key],
                    metrics={
                        "response_time": health.avg_response_time,
                        "error_rate": health.error_rate,
                        "availability": health.availability,
                    },
                    recommendations=[
                        "Immediate investigation required",
                        "Scale resources if needed",
                        "Review recent changes",
                        "Implement circuit breaker if not present",
                    ],
                )
                self.insights.append(insight)

    async def _detect_anomalies(self):
        """Detect traffic and performance anomalies"""

        # Calculate baseline metrics
        baseline_cutoff = datetime.now() - self.baseline_window
        current_cutoff = datetime.now() - timedelta(hours=1)

        baseline_metrics = [
            m
            for m in self.metrics_buffer
            if baseline_cutoff < m.timestamp < current_cutoff
        ]
        current_metrics = [
            m for m in self.metrics_buffer if m.timestamp > current_cutoff
        ]

        if len(baseline_metrics) < 100 or len(current_metrics) < 10:
            return

        # Compare traffic volume
        baseline_volume = len(baseline_metrics) / (
            self.baseline_window.total_seconds() / 3600
        )
        current_volume = len(current_metrics)

        if abs(current_volume - baseline_volume) > baseline_volume * 0.5:
            anomaly_type = "spike" if current_volume > baseline_volume else "drop"

            insight = Insight(
                type=InsightType.TRAFFIC_ANOMALY,
                severity=InsightSeverity.HIGH,
                title=f"Traffic {anomaly_type} detected",
                description=f"Current traffic ({current_volume:.0f} req/h) significantly different from baseline ({baseline_volume:.0f} req/h)",
                affected_endpoints=[],
                metrics={
                    "current_volume": current_volume,
                    "baseline_volume": baseline_volume,
                    "change_percentage": (
                        (current_volume - baseline_volume) / baseline_volume * 100
                    ),
                },
                recommendations=[
                    "Check for DDoS attacks"
                    if anomaly_type == "spike"
                    else "Check service availability",
                    "Review recent deployments",
                    "Monitor resource utilization",
                    "Prepare to scale"
                    if anomaly_type == "spike"
                    else "Investigate root cause",
                ],
            )
            self.insights.append(insight)

    async def _check_immediate_alerts(self, metric: APIMetric):
        """Check for immediate alerts based on single metric"""

        # Security threats (e.g., multiple 401s from same consumer)
        if metric.status_code == 401:
            recent_401s = [
                m
                for m in self.metrics_buffer
                if m.consumer_id == metric.consumer_id
                and m.status_code == 401
                and m.timestamp > datetime.now() - timedelta(minutes=5)
            ]

            if len(recent_401s) > 10:
                insight = Insight(
                    type=InsightType.SECURITY_THREAT,
                    severity=InsightSeverity.CRITICAL,
                    title="Potential brute force attack detected",
                    description=f"Multiple authentication failures from consumer {metric.consumer_id[:8]}",
                    affected_endpoints=[metric.endpoint],
                    metrics={
                        "failure_count": len(recent_401s),
                        "consumer_id": metric.consumer_id,
                    },
                    recommendations=[
                        "Block or rate limit the consumer",
                        "Review authentication logs",
                        "Check for compromised credentials",
                        "Enable additional security measures",
                    ],
                )
                self.insights.append(insight)

    def _classify_error_pattern(self, status_code: int) -> str:
        """Classify error pattern based on status code"""
        if status_code == 401:
            return "authentication_failure"
        elif status_code == 403:
            return "authorization_failure"
        elif status_code == 404:
            return "not_found"
        elif status_code == 429:
            return "rate_limit"
        elif status_code == 500:
            return "server_error"
        elif status_code == 502:
            return "gateway_error"
        elif status_code == 503:
            return "service_unavailable"
        elif status_code == 504:
            return "timeout"
        else:
            return "unknown"

    def _get_error_recommendations(self, pattern_type: str) -> List[str]:
        """Get recommendations based on error pattern"""
        recommendations = {
            "authentication_failure": [
                "Review authentication configuration",
                "Check token expiration settings",
                "Verify API key validity",
            ],
            "rate_limit": [
                "Review rate limiting configuration",
                "Consider increasing limits for affected consumers",
                "Implement request queuing",
            ],
            "server_error": [
                "Check application logs",
                "Review recent deployments",
                "Monitor server resources",
                "Implement error recovery",
            ],
            "timeout": [
                "Optimize slow queries",
                "Increase timeout thresholds",
                "Implement caching",
                "Review network configuration",
            ],
        }

        return recommendations.get(
            pattern_type, ["Investigate error logs", "Review recent changes"]
        )

    def _detect_usage_pattern(self, metrics: List[APIMetric]) -> str:
        """Detect usage pattern from metrics"""
        if len(metrics) < 10:
            return "sporadic"

        # Calculate time between requests
        sorted_metrics = sorted(metrics, key=lambda x: x.timestamp)
        time_diffs = [
            (
                sorted_metrics[i + 1].timestamp - sorted_metrics[i].timestamp
            ).total_seconds()
            for i in range(len(sorted_metrics) - 1)
        ]

        if not time_diffs:
            return "sporadic"

        avg_diff = statistics.mean(time_diffs)
        std_diff = statistics.stdev(time_diffs) if len(time_diffs) > 1 else 0

        if std_diff < avg_diff * 0.2:
            return "regular"
        elif len(metrics) > len(set(m.timestamp.date() for m in metrics)) * 100:
            return "heavy"
        else:
            return "sporadic"

    def _calculate_anomaly_score(self, metrics: List[APIMetric]) -> float:
        """Calculate anomaly score for consumer behavior"""
        if len(metrics) < 10:
            return 0.0

        score = 0.0
        factors = 0

        # Check error rate
        error_rate = len([m for m in metrics if m.status_code >= 400]) / len(metrics)
        if error_rate > 0.1:
            score += min(error_rate * 2, 1.0)
            factors += 1

        # Check response time variance
        response_times = [m.response_time_ms for m in metrics]
        if len(response_times) > 1:
            cv = statistics.stdev(response_times) / statistics.mean(response_times)
            if cv > 1.0:
                score += min(cv / 2, 1.0)
                factors += 1

        # Check request patterns
        hours = [m.timestamp.hour for m in metrics]
        if len(set(hours)) == 1:  # All requests in same hour
            score += 0.5
            factors += 1

        return score / factors if factors > 0 else 0.0

    async def get_insights_summary(self) -> Dict[str, Any]:
        """Get summary of all insights"""

        active_insights = [i for i in self.insights if not i.resolved]

        return {
            "total_insights": len(active_insights),
            "by_severity": {
                "critical": len(
                    [
                        i
                        for i in active_insights
                        if i.severity == InsightSeverity.CRITICAL
                    ]
                ),
                "high": len(
                    [i for i in active_insights if i.severity == InsightSeverity.HIGH]
                ),
                "medium": len(
                    [i for i in active_insights if i.severity == InsightSeverity.MEDIUM]
                ),
                "low": len(
                    [i for i in active_insights if i.severity == InsightSeverity.LOW]
                ),
                "info": len(
                    [i for i in active_insights if i.severity == InsightSeverity.INFO]
                ),
            },
            "by_type": {
                insight_type.value: len(
                    [i for i in active_insights if i.type == insight_type]
                )
                for insight_type in InsightType
            },
            "recent_insights": [i.dict() for i in active_insights[:10]],
            "endpoint_health": {
                "healthy": len(
                    [h for h in self.endpoint_health.values() if h.health_score > 80]
                ),
                "warning": len(
                    [
                        h
                        for h in self.endpoint_health.values()
                        if 60 < h.health_score <= 80
                    ]
                ),
                "critical": len(
                    [h for h in self.endpoint_health.values() if h.health_score <= 60]
                ),
            },
            "version_usage": {
                v.version: {
                    "percentage": v.usage_percentage,
                    "deprecated": v.deprecated,
                }
                for v in self.version_usage.values()
            },
        }


# Global insights instance
api_insights = APIInsights()

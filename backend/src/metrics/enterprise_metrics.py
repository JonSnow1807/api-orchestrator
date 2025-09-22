#!/usr/bin/env python3
"""
Enterprise Performance Metrics Collection System
Advanced metrics collection for caching, tracing, API discovery, and audit systems
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import logging


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricCategory(Enum):
    CACHE = "cache"
    TRACING = "tracing"
    API_DISCOVERY = "api_discovery"
    AUDIT = "audit"
    SDK_GENERATION = "sdk_generation"
    LOAD_TESTING = "load_testing"
    GENERAL = "general"


@dataclass
class MetricPoint:
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class EnterpriseMetric:
    name: str
    category: MetricCategory
    metric_type: MetricType
    description: str
    unit: str
    points: deque = field(default_factory=lambda: deque(maxlen=10000))
    labels: Dict[str, str] = field(default_factory=dict)


class EnterpriseMetricsCollector:
    """
    Comprehensive metrics collection system for enterprise features
    Tracks performance, usage, and health metrics across all enterprise systems
    """

    def __init__(self, retention_hours: int = 24):
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, EnterpriseMetric] = {}
        self.retention_hours = retention_hours

        # Aggregated statistics cache
        self._stats_cache: Dict[str, Dict] = {}
        self._cache_ttl = 60  # Cache TTL in seconds
        self._last_cache_update: Dict[str, datetime] = {}

        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self):
        """Start the metrics collection system"""
        if self._is_running:
            return

        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_old_metrics())
        self.logger.info("📊 Enterprise Metrics Collector started")

    async def stop(self):
        """Stop the metrics collection system"""
        self._is_running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("📊 Enterprise Metrics Collector stopped")

    def record_counter(
        self,
        name: str,
        category: MetricCategory,
        value: float = 1.0,
        labels: Dict[str, str] = None,
        description: str = "",
    ):
        """Record a counter metric (always increasing)"""
        self._ensure_metric_exists(
            name, category, MetricType.COUNTER, description, "count"
        )
        self._add_point(name, value, labels or {})

    def record_gauge(
        self,
        name: str,
        category: MetricCategory,
        value: float,
        labels: Dict[str, str] = None,
        description: str = "",
        unit: str = "",
    ):
        """Record a gauge metric (can go up or down)"""
        self._ensure_metric_exists(name, category, MetricType.GAUGE, description, unit)
        self._add_point(name, value, labels or {})

    def record_histogram(
        self,
        name: str,
        category: MetricCategory,
        value: float,
        labels: Dict[str, str] = None,
        description: str = "",
        unit: str = "",
    ):
        """Record a histogram metric (for distributions)"""
        self._ensure_metric_exists(
            name, category, MetricType.HISTOGRAM, description, unit
        )
        self._add_point(name, value, labels or {})

    def start_timer(
        self,
        name: str,
        category: MetricCategory,
        labels: Dict[str, str] = None,
        description: str = "",
    ):
        """Start a timer metric"""
        return TimerContext(self, name, category, labels or {}, description)

    def _ensure_metric_exists(
        self,
        name: str,
        category: MetricCategory,
        metric_type: MetricType,
        description: str,
        unit: str,
    ):
        """Ensure a metric exists, create if not"""
        if name not in self.metrics:
            self.metrics[name] = EnterpriseMetric(
                name=name,
                category=category,
                metric_type=metric_type,
                description=description,
                unit=unit,
            )

    def _add_point(self, name: str, value: float, labels: Dict[str, str]):
        """Add a data point to a metric"""
        if name in self.metrics:
            point = MetricPoint(timestamp=datetime.now(), value=value, labels=labels)
            self.metrics[name].points.append(point)

            # Invalidate cache for this metric
            if name in self._stats_cache:
                del self._stats_cache[name]

    async def _cleanup_old_metrics(self):
        """Clean up old metric points to prevent memory growth"""
        while self._is_running:
            try:
                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

                for metric in self.metrics.values():
                    # Remove old points
                    while metric.points and metric.points[0].timestamp < cutoff_time:
                        metric.points.popleft()

                await asyncio.sleep(3600)  # Run cleanup every hour

            except Exception as e:
                self.logger.error(f"Error during metrics cleanup: {e}")
                await asyncio.sleep(3600)

    def get_metric_stats(
        self, name: str, time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get statistics for a metric within a time window"""

        # Check cache first
        cache_key = f"{name}_{time_window_minutes}"
        if (
            cache_key in self._stats_cache
            and cache_key in self._last_cache_update
            and (datetime.now() - self._last_cache_update[cache_key]).seconds
            < self._cache_ttl
        ):
            return self._stats_cache[cache_key]

        if name not in self.metrics:
            return {"error": f"Metric {name} not found"}

        metric = self.metrics[name]
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

        # Filter points within time window
        recent_points = [p for p in metric.points if p.timestamp >= cutoff_time]

        if not recent_points:
            return {
                "metric_name": name,
                "category": metric.category.value,
                "type": metric.metric_type.value,
                "time_window_minutes": time_window_minutes,
                "data_points": 0,
                "message": "No data points in time window",
            }

        values = [p.value for p in recent_points]

        stats = {
            "metric_name": name,
            "category": metric.category.value,
            "type": metric.metric_type.value,
            "description": metric.description,
            "unit": metric.unit,
            "time_window_minutes": time_window_minutes,
            "data_points": len(values),
            "first_timestamp": recent_points[0].timestamp.isoformat(),
            "last_timestamp": recent_points[-1].timestamp.isoformat(),
        }

        if metric.metric_type in [
            MetricType.GAUGE,
            MetricType.HISTOGRAM,
            MetricType.TIMER,
        ]:
            stats.update(
                {
                    "current_value": values[-1],
                    "min_value": min(values),
                    "max_value": max(values),
                    "avg_value": statistics.mean(values),
                    "median_value": statistics.median(values),
                }
            )

            if len(values) > 1:
                stats["std_dev"] = statistics.stdev(values)
                stats["p95"] = self._percentile(values, 0.95)
                stats["p99"] = self._percentile(values, 0.99)

        elif metric.metric_type == MetricType.COUNTER:
            stats.update(
                {
                    "total_value": sum(values),
                    "rate_per_minute": len(values) / time_window_minutes
                    if time_window_minutes > 0
                    else 0,
                    "last_value": values[-1],
                }
            )

        # Cache the result
        self._stats_cache[cache_key] = stats
        self._last_cache_update[cache_key] = datetime.now()

        return stats

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def get_category_summary(
        self, category: MetricCategory, time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get summary statistics for all metrics in a category"""
        category_metrics = {
            name: metric
            for name, metric in self.metrics.items()
            if metric.category == category
        }

        if not category_metrics:
            return {
                "category": category.value,
                "metrics_count": 0,
                "message": "No metrics found for category",
            }

        summary = {
            "category": category.value,
            "time_window_minutes": time_window_minutes,
            "metrics_count": len(category_metrics),
            "metrics": {},
        }

        for name in category_metrics:
            summary["metrics"][name] = self.get_metric_stats(name, time_window_minutes)

        return summary

    def get_all_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get summary of all metrics across all categories"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "time_window_minutes": time_window_minutes,
            "total_metrics": len(self.metrics),
            "categories": {},
        }

        # Group by category
        for category in MetricCategory:
            category_summary = self.get_category_summary(category, time_window_minutes)
            if category_summary["metrics_count"] > 0:
                summary["categories"][category.value] = category_summary

        return summary


class TimerContext:
    """Context manager for timing operations"""

    def __init__(
        self,
        collector: EnterpriseMetricsCollector,
        name: str,
        category: MetricCategory,
        labels: Dict[str, str],
        description: str,
    ):
        self.collector = collector
        self.name = name
        self.category = category
        self.labels = labels
        self.description = description
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector._ensure_metric_exists(
                self.name, self.category, MetricType.TIMER, self.description, "ms"
            )
            self.collector._add_point(self.name, duration_ms, self.labels)


# Enterprise-specific metric recording functions
class CacheMetrics:
    """Cache-specific metrics collection"""

    def __init__(self, collector: EnterpriseMetricsCollector):
        self.collector = collector

    def record_hit(self, cache_name: str):
        """Record a cache hit"""
        self.collector.record_counter(
            "cache_hits",
            MetricCategory.CACHE,
            1.0,
            {"cache_name": cache_name},
            "Number of cache hits",
        )

    def record_miss(self, cache_name: str):
        """Record a cache miss"""
        self.collector.record_counter(
            "cache_misses",
            MetricCategory.CACHE,
            1.0,
            {"cache_name": cache_name},
            "Number of cache misses",
        )

    def record_size(self, cache_name: str, size_bytes: int):
        """Record cache size"""
        self.collector.record_gauge(
            "cache_size",
            MetricCategory.CACHE,
            size_bytes,
            {"cache_name": cache_name},
            "Cache size in bytes",
            "bytes",
        )

    def record_operation_time(self, cache_name: str, operation: str):
        """Get timer for cache operations"""
        return self.collector.start_timer(
            "cache_operation_time",
            MetricCategory.CACHE,
            {"cache_name": cache_name, "operation": operation},
            "Time taken for cache operations",
        )


class TracingMetrics:
    """Distributed tracing metrics collection"""

    def __init__(self, collector: EnterpriseMetricsCollector):
        self.collector = collector

    def record_span_created(self, service_name: str):
        """Record span creation"""
        self.collector.record_counter(
            "spans_created",
            MetricCategory.TRACING,
            1.0,
            {"service": service_name},
            "Number of spans created",
        )

    def record_trace_duration(self, service_name: str, duration_ms: float):
        """Record trace duration"""
        self.collector.record_histogram(
            "trace_duration",
            MetricCategory.TRACING,
            duration_ms,
            {"service": service_name},
            "Trace duration in milliseconds",
            "ms",
        )

    def record_error_rate(self, service_name: str, error_count: int, total_count: int):
        """Record service error rate"""
        error_rate = (error_count / total_count * 100) if total_count > 0 else 0
        self.collector.record_gauge(
            "service_error_rate",
            MetricCategory.TRACING,
            error_rate,
            {"service": service_name},
            "Service error rate percentage",
            "%",
        )


class APIDiscoveryMetrics:
    """API Discovery metrics collection"""

    def __init__(self, collector: EnterpriseMetricsCollector):
        self.collector = collector

    def record_api_discovered(self, discovery_method: str):
        """Record API discovery"""
        self.collector.record_counter(
            "apis_discovered",
            MetricCategory.API_DISCOVERY,
            1.0,
            {"method": discovery_method},
            "Number of APIs discovered",
        )

    def record_discovery_time(self, discovery_method: str):
        """Get timer for discovery operations"""
        return self.collector.start_timer(
            "discovery_time",
            MetricCategory.API_DISCOVERY,
            {"method": discovery_method},
            "Time taken for API discovery",
        )

    def record_ml_confidence(self, model_name: str, confidence_score: float):
        """Record ML model confidence scores"""
        self.collector.record_histogram(
            "ml_confidence_score",
            MetricCategory.API_DISCOVERY,
            confidence_score,
            {"model": model_name},
            "ML model confidence scores",
            "score",
        )


# Global metrics collector instance
enterprise_metrics = EnterpriseMetricsCollector()

# Specialized metric recorders
cache_metrics = CacheMetrics(enterprise_metrics)
tracing_metrics = TracingMetrics(enterprise_metrics)
api_discovery_metrics = APIDiscoveryMetrics(enterprise_metrics)


# Convenience functions
async def start_metrics_collection():
    """Start the enterprise metrics collection"""
    await enterprise_metrics.start()


async def stop_metrics_collection():
    """Stop the enterprise metrics collection"""
    await enterprise_metrics.stop()


def get_metrics_summary(time_window_minutes: int = 60):
    """Get comprehensive metrics summary"""
    return enterprise_metrics.get_all_metrics_summary(time_window_minutes)


def get_category_metrics(category: str, time_window_minutes: int = 60):
    """Get metrics for a specific category"""
    try:
        cat_enum = MetricCategory(category)
        return enterprise_metrics.get_category_summary(cat_enum, time_window_minutes)
    except ValueError:
        return {"error": f"Invalid category: {category}"}


def get_metric_details(metric_name: str, time_window_minutes: int = 60):
    """Get details for a specific metric"""
    return enterprise_metrics.get_metric_stats(metric_name, time_window_minutes)

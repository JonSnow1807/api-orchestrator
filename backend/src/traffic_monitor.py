"""
Real-time API Traffic Monitoring - Advanced observability beyond Postman
Track, analyze, and visualize API traffic in real-time
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import time
import statistics
from enum import Enum

class MetricType(Enum):
    """Types of metrics tracked"""
    REQUESTS_PER_SECOND = "rps"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    BANDWIDTH = "bandwidth"
    STATUS_CODES = "status_codes"
    ENDPOINTS = "endpoints"
    GEOGRAPHIC = "geographic"
    USER_AGENTS = "user_agents"

@dataclass
class TrafficMetric:
    """Individual traffic metric"""
    timestamp: datetime
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    error_message: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    
    def to_dict(self):
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class TrafficStats:
    """Aggregated traffic statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0
    total_bandwidth_mb: float = 0
    requests_per_second: float = 0
    error_rate: float = 0
    p50_response_time: float = 0
    p95_response_time: float = 0
    p99_response_time: float = 0
    
    def to_dict(self):
        return asdict(self)

class TrafficMonitor:
    """Real-time API traffic monitoring system"""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.metrics: deque = deque(maxlen=max_history_size)
        self.active_connections: Set[str] = set()
        self.subscribers: Set[asyncio.Queue] = set()
        
        # Real-time counters
        self.endpoint_counts = defaultdict(int)
        self.status_code_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.user_agent_counts = defaultdict(int)
        
        # Time-series data (1-minute buckets)
        self.time_series_data = defaultdict(lambda: defaultdict(list))
        self.current_minute_metrics = []
        
        # Alerts configuration
        self.alert_thresholds = {
            'error_rate': 0.05,  # 5% error rate
            'response_time_p95': 1000,  # 1 second
            'requests_per_second': 1000,  # Max RPS
        }
        self.active_alerts = []
        
        # Start background tasks
        self.running = True
        asyncio.create_task(self._aggregate_metrics_task())
        asyncio.create_task(self._cleanup_old_data_task())
    
    async def record_metric(self, metric: TrafficMetric):
        """Record a new traffic metric"""
        # Add to metrics deque
        self.metrics.append(metric)
        self.current_minute_metrics.append(metric)
        
        # Update counters
        self.endpoint_counts[f"{metric.method} {metric.endpoint}"] += 1
        self.status_code_counts[metric.status_code] += 1
        
        if metric.error_message:
            self.error_counts[metric.error_message] += 1
        
        if metric.user_agent:
            self.user_agent_counts[metric.user_agent] += 1
        
        # Check for alerts
        await self._check_alerts(metric)
        
        # Notify subscribers
        await self._notify_subscribers({
            'type': 'metric',
            'data': metric.to_dict()
        })
    
    async def get_real_time_stats(self, time_window_seconds: int = 60) -> TrafficStats:
        """Get aggregated statistics for the specified time window"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window_seconds)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return TrafficStats()
        
        response_times = [m.response_time_ms for m in recent_metrics]
        successful = [m for m in recent_metrics if 200 <= m.status_code < 400]
        failed = [m for m in recent_metrics if m.status_code >= 400]
        
        total_bandwidth = sum(
            (m.request_size_bytes + m.response_size_bytes) / (1024 * 1024)
            for m in recent_metrics
        )
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[len(sorted_times) // 2] if sorted_times else 0
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        
        return TrafficStats(
            total_requests=len(recent_metrics),
            successful_requests=len(successful),
            failed_requests=len(failed),
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            total_bandwidth_mb=total_bandwidth,
            requests_per_second=len(recent_metrics) / time_window_seconds,
            error_rate=len(failed) / len(recent_metrics) if recent_metrics else 0,
            p50_response_time=p50,
            p95_response_time=p95,
            p99_response_time=p99
        )
    
    async def get_endpoint_stats(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get statistics for top endpoints"""
        endpoint_stats = []
        
        for endpoint, count in sorted(
            self.endpoint_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]:
            # Get metrics for this endpoint
            endpoint_metrics = [
                m for m in self.metrics
                if f"{m.method} {m.endpoint}" == endpoint
            ]
            
            if endpoint_metrics:
                response_times = [m.response_time_ms for m in endpoint_metrics]
                errors = [m for m in endpoint_metrics if m.status_code >= 400]
                
                endpoint_stats.append({
                    'endpoint': endpoint,
                    'count': count,
                    'avg_response_time': statistics.mean(response_times),
                    'error_rate': len(errors) / len(endpoint_metrics),
                    'methods': list(set(m.method for m in endpoint_metrics))
                })
        
        return endpoint_stats
    
    async def get_time_series_data(
        self,
        metric_type: MetricType,
        duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get time-series data for visualization"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        series_data = []
        
        for minute_key in sorted(self.time_series_data.keys()):
            minute_time = datetime.fromisoformat(minute_key)
            if minute_time > cutoff_time:
                data_point = {
                    'timestamp': minute_key,
                    'value': 0
                }
                
                if metric_type == MetricType.REQUESTS_PER_SECOND:
                    data_point['value'] = len(self.time_series_data[minute_key]['metrics']) / 60
                elif metric_type == MetricType.RESPONSE_TIME:
                    times = self.time_series_data[minute_key].get('response_times', [])
                    data_point['value'] = statistics.mean(times) if times else 0
                elif metric_type == MetricType.ERROR_RATE:
                    metrics = self.time_series_data[minute_key]['metrics']
                    errors = [m for m in metrics if m['status_code'] >= 400]
                    data_point['value'] = len(errors) / len(metrics) if metrics else 0
                elif metric_type == MetricType.BANDWIDTH:
                    data_point['value'] = self.time_series_data[minute_key].get('bandwidth', 0)
                
                series_data.append(data_point)
        
        return series_data
    
    async def get_status_code_distribution(self) -> Dict[str, int]:
        """Get distribution of status codes"""
        distribution = defaultdict(int)
        
        for code, count in self.status_code_counts.items():
            if code < 200:
                category = "1xx"
            elif code < 300:
                category = "2xx"
            elif code < 400:
                category = "3xx"
            elif code < 500:
                category = "4xx"
            else:
                category = "5xx"
            
            distribution[category] += count
        
        return dict(distribution)
    
    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to real-time traffic updates"""
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        
        # Send initial stats
        await queue.put({
            'type': 'initial',
            'stats': (await self.get_real_time_stats()).to_dict(),
            'endpoints': await self.get_endpoint_stats(),
            'status_codes': await self.get_status_code_distribution()
        })
        
        return queue
    
    async def unsubscribe(self, queue: asyncio.Queue):
        """Unsubscribe from traffic updates"""
        self.subscribers.discard(queue)
    
    async def _notify_subscribers(self, message: Dict[str, Any]):
        """Notify all subscribers of an update"""
        dead_queues = set()
        
        for queue in self.subscribers:
            try:
                await asyncio.wait_for(queue.put(message), timeout=1)
            except (asyncio.TimeoutError, asyncio.QueueFull):
                dead_queues.add(queue)
        
        # Remove dead queues
        self.subscribers -= dead_queues
    
    async def _check_alerts(self, metric: TrafficMetric):
        """Check if metric triggers any alerts"""
        # Check error rate
        recent_stats = await self.get_real_time_stats(60)
        
        alerts = []
        
        if recent_stats.error_rate > self.alert_thresholds['error_rate']:
            alerts.append({
                'type': 'error_rate',
                'severity': 'high',
                'message': f"Error rate {recent_stats.error_rate:.1%} exceeds threshold",
                'threshold': self.alert_thresholds['error_rate'],
                'current_value': recent_stats.error_rate
            })
        
        if recent_stats.p95_response_time > self.alert_thresholds['response_time_p95']:
            alerts.append({
                'type': 'response_time',
                'severity': 'medium',
                'message': f"P95 response time {recent_stats.p95_response_time:.0f}ms exceeds threshold",
                'threshold': self.alert_thresholds['response_time_p95'],
                'current_value': recent_stats.p95_response_time
            })
        
        if recent_stats.requests_per_second > self.alert_thresholds['requests_per_second']:
            alerts.append({
                'type': 'rate_limit',
                'severity': 'high',
                'message': f"Request rate {recent_stats.requests_per_second:.0f} RPS exceeds threshold",
                'threshold': self.alert_thresholds['requests_per_second'],
                'current_value': recent_stats.requests_per_second
            })
        
        # Notify subscribers of alerts
        for alert in alerts:
            alert['timestamp'] = datetime.now().isoformat()
            self.active_alerts.append(alert)
            await self._notify_subscribers({
                'type': 'alert',
                'alert': alert
            })
    
    async def _aggregate_metrics_task(self):
        """Background task to aggregate metrics every minute"""
        while self.running:
            await asyncio.sleep(60)  # Run every minute
            
            if self.current_minute_metrics:
                minute_key = datetime.now().replace(second=0, microsecond=0).isoformat()
                
                # Store aggregated data
                self.time_series_data[minute_key]['metrics'] = [
                    m.to_dict() for m in self.current_minute_metrics
                ]
                
                response_times = [m.response_time_ms for m in self.current_minute_metrics]
                if response_times:
                    self.time_series_data[minute_key]['response_times'] = response_times
                
                total_bandwidth = sum(
                    (m.request_size_bytes + m.response_size_bytes) / (1024 * 1024)
                    for m in self.current_minute_metrics
                )
                self.time_series_data[minute_key]['bandwidth'] = total_bandwidth
                
                # Clear current minute metrics
                self.current_minute_metrics = []
                
                # Send aggregated stats to subscribers
                stats = await self.get_real_time_stats()
                await self._notify_subscribers({
                    'type': 'stats_update',
                    'stats': stats.to_dict()
                })
    
    async def _cleanup_old_data_task(self):
        """Background task to cleanup old time-series data"""
        while self.running:
            await asyncio.sleep(3600)  # Run every hour
            
            # Keep only last 24 hours of time-series data
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            old_keys = [
                key for key in self.time_series_data.keys()
                if datetime.fromisoformat(key) < cutoff_time
            ]
            
            for key in old_keys:
                del self.time_series_data[key]
            
            # Clean up old alerts
            self.active_alerts = [
                alert for alert in self.active_alerts
                if datetime.fromisoformat(alert['timestamp']) > cutoff_time
            ]
    
    def stop(self):
        """Stop the traffic monitor"""
        self.running = False

# Global traffic monitor instance
traffic_monitor = TrafficMonitor()
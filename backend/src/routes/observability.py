"""
Observability and Distributed Tracing API Routes
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from src.database import get_db, User
from src.auth import get_current_user
from src.distributed_tracing_observability import (
    observability, get_trace_id, record_metric, add_trace_tag
)

router = APIRouter(prefix="/api/observability", tags=["Observability"])

class TraceQuery(BaseModel):
    trace_id: Optional[str] = None
    service_name: Optional[str] = None
    operation_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_only: bool = False
    min_duration_ms: Optional[float] = None
    tags: Optional[Dict[str, str]] = None

class MetricQuery(BaseModel):
    metric_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    aggregation: str = "avg"  # avg, sum, min, max, count

class HealthCheckRequest(BaseModel):
    name: str
    description: Optional[str] = None
    endpoint: Optional[str] = None
    timeout_seconds: int = 30

@router.get("/dashboard")
async def get_observability_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive observability dashboard"""
    return observability.get_observability_dashboard()

@router.get("/traces")
async def search_traces(
    trace_id: Optional[str] = Query(None, description="Specific trace ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    operation_name: Optional[str] = Query(None, description="Filter by operation name"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    error_only: bool = Query(False, description="Show only traces with errors"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of traces"),
    current_user: User = Depends(get_current_user)
):
    """Search and filter distributed traces"""

    if trace_id:
        # Get specific trace
        trace_summary = observability.tracer.get_trace_summary(trace_id)
        return {"traces": [trace_summary] if "error" not in trace_summary else []}

    # Filter traces from completed spans
    traces = {}

    for span in observability.tracer.completed_spans:
        # Apply filters
        if service_name and span.service_name != service_name:
            continue
        if operation_name and span.operation_name != operation_name:
            continue
        if error_only and span.status != "error":
            continue
        if start_time and span.start_time < start_time:
            continue
        if end_time and span.end_time and span.end_time > end_time:
            continue

        # Group by trace_id
        if span.trace_id not in traces:
            traces[span.trace_id] = {
                "trace_id": span.trace_id,
                "spans": [],
                "total_duration_ms": 0,
                "error_count": 0,
                "services": set(),
                "operations": set()
            }

        trace_data = traces[span.trace_id]
        trace_data["spans"].append({
            "span_id": span.span_id,
            "operation_name": span.operation_name,
            "service_name": span.service_name,
            "duration_ms": span.duration_ms,
            "status": span.status,
            "start_time": span.start_time.isoformat(),
            "tags": span.tags
        })

        if span.duration_ms:
            trace_data["total_duration_ms"] += span.duration_ms
        if span.status == "error":
            trace_data["error_count"] += 1

        trace_data["services"].add(span.service_name)
        trace_data["operations"].add(span.operation_name)

    # Convert sets to lists and limit results
    result_traces = []
    for trace_data in list(traces.values())[:limit]:
        trace_data["services"] = list(trace_data["services"])
        trace_data["operations"] = list(trace_data["operations"])
        trace_data["span_count"] = len(trace_data["spans"])
        result_traces.append(trace_data)

    return {
        "traces": result_traces,
        "total_found": len(traces),
        "returned": len(result_traces)
    }

@router.get("/traces/{trace_id}")
async def get_trace_details(
    trace_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information for a specific trace"""
    trace_summary = observability.tracer.get_trace_summary(trace_id)

    if "error" in trace_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace {trace_id} not found"
        )

    return trace_summary

@router.get("/traces/{trace_id}/timeline")
async def get_trace_timeline(
    trace_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get timeline visualization data for a trace"""
    spans = [span for span in observability.tracer.completed_spans if span.trace_id == trace_id]

    if not spans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace {trace_id} not found"
        )

    # Sort spans by start time
    spans.sort(key=lambda s: s.start_time)

    # Calculate timeline
    trace_start = spans[0].start_time
    timeline = []

    for span in spans:
        start_offset = (span.start_time - trace_start).total_seconds() * 1000
        duration = span.duration_ms or 0

        timeline.append({
            "span_id": span.span_id,
            "operation_name": span.operation_name,
            "service_name": span.service_name,
            "start_offset_ms": start_offset,
            "duration_ms": duration,
            "end_offset_ms": start_offset + duration,
            "status": span.status,
            "tags": span.tags,
            "parent_span_id": span.parent_span_id
        })

    total_duration = max(
        item["end_offset_ms"] for item in timeline if item["end_offset_ms"]
    ) if timeline else 0

    return {
        "trace_id": trace_id,
        "total_duration_ms": total_duration,
        "span_count": len(timeline),
        "timeline": timeline
    }

@router.get("/metrics")
async def get_metrics(
    metric_name: Optional[str] = Query(None, description="Specific metric name"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    current_user: User = Depends(get_current_user)
):
    """Get metrics data with optional filtering"""

    if metric_name:
        if metric_name not in observability.metrics_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metric {metric_name} not found"
            )

        metrics = observability.metrics_store[metric_name]
    else:
        # Get all metrics
        metrics = []
        for metric_list in observability.metrics_store.values():
            metrics.extend(metric_list)

    # Apply time filters
    if start_time or end_time:
        filtered_metrics = []
        for metric in metrics:
            metric_time = metric["timestamp"]
            if start_time and metric_time < start_time:
                continue
            if end_time and metric_time > end_time:
                continue
            filtered_metrics.append(metric)
        metrics = filtered_metrics

    return {
        "metrics": metrics,
        "count": len(metrics),
        "available_metrics": list(observability.metrics_store.keys())
    }

@router.post("/metrics")
async def record_custom_metric(
    metric_name: str = Query(..., description="Name of the metric"),
    value: float = Query(..., description="Metric value"),
    tags: Optional[Dict[str, str]] = None,
    current_user: User = Depends(get_current_user)
):
    """Record a custom metric value"""

    record_metric(metric_name, value, **(tags or {}))

    return {
        "message": f"Metric {metric_name} recorded successfully",
        "metric_name": metric_name,
        "value": value,
        "tags": tags or {},
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/service-map")
async def get_service_map(
    time_range_hours: int = Query(1, ge=1, le=24, description="Time range in hours"),
    current_user: User = Depends(get_current_user)
):
    """Get service dependency map"""

    cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)

    # Build service map from recent spans
    services = {}
    dependencies = []

    for span in observability.tracer.completed_spans:
        if span.end_time and span.end_time < cutoff_time:
            continue

        service_name = span.service_name

        if service_name not in services:
            services[service_name] = {
                "name": service_name,
                "request_count": 0,
                "error_count": 0,
                "avg_duration_ms": 0,
                "operations": set()
            }

        service = services[service_name]
        service["request_count"] += 1
        service["operations"].add(span.operation_name)

        if span.status == "error":
            service["error_count"] += 1

        if span.duration_ms:
            service["avg_duration_ms"] = (
                (service["avg_duration_ms"] * (service["request_count"] - 1) + span.duration_ms) /
                service["request_count"]
            )

    # Convert operations sets to lists
    for service in services.values():
        service["operations"] = list(service["operations"])
        service["error_rate"] = service["error_count"] / service["request_count"] if service["request_count"] > 0 else 0

    return {
        "services": list(services.values()),
        "dependencies": dependencies,
        "time_range_hours": time_range_hours,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def get_health_status(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive health status"""
    health_results = await observability.run_health_checks()

    return health_results

@router.post("/health/checks")
async def add_health_check(
    request: HealthCheckRequest,
    current_user: User = Depends(get_current_user)
):
    """Add a custom health check"""

    async def custom_health_check():
        """Custom health check implementation"""
        if request.endpoint:
            # HTTP endpoint check
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        request.endpoint,
                        timeout=aiohttp.ClientTimeout(total=request.timeout_seconds)
                    ) as response:
                        return response.status < 400
            except Exception:
                return False
        else:
            # Simple true check for testing
            return True

    observability.add_health_check(request.name, custom_health_check)

    return {
        "message": f"Health check '{request.name}' added successfully",
        "name": request.name,
        "description": request.description,
        "endpoint": request.endpoint
    }

@router.get("/sli")
async def get_service_level_indicators(
    current_user: User = Depends(get_current_user)
):
    """Get Service Level Indicators (SLI) metrics"""

    sli_metrics = observability.calculate_sli_metrics()

    # Calculate overall SLI score
    if sli_metrics:
        overall_sli = sum(sli_metrics.values()) / len(sli_metrics)
    else:
        overall_sli = 0

    return {
        "overall_sli_score": overall_sli,
        "sli_metrics": sli_metrics,
        "error_budget_remaining": observability.error_budget,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/performance-summary")
async def get_performance_summary(
    time_range_hours: int = Query(1, ge=1, le=24, description="Time range in hours"),
    current_user: User = Depends(get_current_user)
):
    """Get performance summary for the specified time range"""

    cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)

    # Analyze recent spans
    recent_spans = [
        span for span in observability.tracer.completed_spans
        if span.end_time and span.end_time > cutoff_time
    ]

    if not recent_spans:
        return {
            "message": "No data available for the specified time range",
            "time_range_hours": time_range_hours
        }

    # Calculate summary statistics
    total_requests = len(recent_spans)
    error_count = sum(1 for span in recent_spans if span.status == "error")
    durations = [span.duration_ms for span in recent_spans if span.duration_ms]

    avg_duration = sum(durations) / len(durations) if durations else 0
    p95_duration = sorted(durations)[int(len(durations) * 0.95)] if durations else 0
    p99_duration = sorted(durations)[int(len(durations) * 0.99)] if durations else 0

    # Service breakdown
    service_stats = {}
    for span in recent_spans:
        service = span.service_name
        if service not in service_stats:
            service_stats[service] = {
                "request_count": 0,
                "error_count": 0,
                "total_duration": 0
            }

        service_stats[service]["request_count"] += 1
        if span.status == "error":
            service_stats[service]["error_count"] += 1
        if span.duration_ms:
            service_stats[service]["total_duration"] += span.duration_ms

    # Calculate service averages
    for service, stats in service_stats.items():
        stats["avg_duration_ms"] = stats["total_duration"] / stats["request_count"]
        stats["error_rate"] = stats["error_count"] / stats["request_count"]

    return {
        "time_range_hours": time_range_hours,
        "summary": {
            "total_requests": total_requests,
            "error_count": error_count,
            "error_rate": error_count / total_requests,
            "avg_duration_ms": avg_duration,
            "p95_duration_ms": p95_duration,
            "p99_duration_ms": p99_duration,
            "throughput_rps": total_requests / (time_range_hours * 3600)
        },
        "service_breakdown": service_stats,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.get("/current-trace")
async def get_current_trace_info(
    current_user: User = Depends(get_current_user)
):
    """Get information about the current trace"""

    trace_id = get_trace_id()
    span_id = observability.tracer.get_current_span_id()

    if not trace_id:
        return {
            "message": "No active trace",
            "tracing_enabled": observability.tracer.initialized
        }

    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "tracing_enabled": observability.tracer.initialized,
        "service_name": observability.service_name
    }

@router.post("/trace-tag")
async def add_trace_tag_endpoint(
    key: str = Query(..., description="Tag key"),
    value: str = Query(..., description="Tag value"),
    current_user: User = Depends(get_current_user)
):
    """Add a tag to the current trace"""

    trace_id = get_trace_id()
    if not trace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active trace to tag"
        )

    add_trace_tag(key, value)

    return {
        "message": f"Tag added to trace {trace_id}",
        "trace_id": trace_id,
        "tag": {"key": key, "value": value}
    }
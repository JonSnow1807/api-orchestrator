"""
Traffic Monitor API Routes - Real-time observability
"""

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query,
    HTTPException,
)
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json

from ..traffic_monitor import traffic_monitor, TrafficMetric, MetricType, TrafficStats
from ..auth import get_current_user

router = APIRouter(prefix="/api/traffic", tags=["Traffic Monitor"])


@router.websocket("/ws")
async def traffic_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time traffic monitoring"""
    await websocket.accept()

    # Subscribe to traffic updates
    queue = await traffic_monitor.subscribe()

    try:
        while True:
            # Send updates to client
            try:
                message = await asyncio.wait_for(queue.get(), timeout=1)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})

            # Check for client messages (commands)
            try:
                client_message = await asyncio.wait_for(
                    websocket.receive_text(), timeout=0.1
                )

                # Handle client commands
                try:
                    command = json.loads(client_message)

                    if command.get("type") == "get_stats":
                        stats = await traffic_monitor.get_real_time_stats(
                            command.get("window", 60)
                        )
                        await websocket.send_json(
                            {"type": "stats", "data": stats.to_dict()}
                        )

                    elif command.get("type") == "get_endpoints":
                        endpoints = await traffic_monitor.get_endpoint_stats(
                            command.get("top_n", 10)
                        )
                        await websocket.send_json(
                            {"type": "endpoints", "data": endpoints}
                        )

                    elif command.get("type") == "get_time_series":
                        metric_type = MetricType(command.get("metric", "rps"))
                        duration = command.get("duration", 60)
                        series = await traffic_monitor.get_time_series_data(
                            metric_type, duration
                        )
                        await websocket.send_json(
                            {
                                "type": "time_series",
                                "metric": metric_type.value,
                                "data": series,
                            }
                        )

                except json.JSONDecodeError:
                    pass

            except asyncio.TimeoutError:
                pass

    except WebSocketDisconnect:
        await traffic_monitor.unsubscribe(queue)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await traffic_monitor.unsubscribe(queue)


@router.post("/record")
async def record_traffic_metric(
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    request_size_bytes: int = 0,
    response_size_bytes: int = 0,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    error_message: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Record a traffic metric"""
    metric = TrafficMetric(
        timestamp=datetime.now(),
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        request_size_bytes=request_size_bytes,
        response_size_bytes=response_size_bytes,
        client_ip=client_ip,
        user_agent=user_agent,
        error_message=error_message,
    )

    await traffic_monitor.record_metric(metric)

    return {"status": "recorded", "metric": metric.to_dict()}


@router.get("/stats")
async def get_traffic_stats(
    window_seconds: int = Query(60, description="Time window in seconds"),
    current_user: dict = Depends(get_current_user),
) -> TrafficStats:
    """Get aggregated traffic statistics"""
    stats = await traffic_monitor.get_real_time_stats(window_seconds)
    return stats


@router.get("/endpoints")
async def get_endpoint_stats(
    top_n: int = Query(10, description="Number of top endpoints to return"),
    current_user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get statistics for top endpoints"""
    return await traffic_monitor.get_endpoint_stats(top_n)


@router.get("/time-series/{metric_type}")
async def get_time_series(
    metric_type: str,
    duration_minutes: int = Query(60, description="Duration in minutes"),
    current_user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get time-series data for a specific metric"""
    try:
        metric = MetricType(metric_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric type. Must be one of: {[m.value for m in MetricType]}",
        )

    return await traffic_monitor.get_time_series_data(metric, duration_minutes)


@router.get("/status-codes")
async def get_status_code_distribution(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, int]:
    """Get distribution of HTTP status codes"""
    return await traffic_monitor.get_status_code_distribution()


@router.get("/alerts")
async def get_active_alerts(
    current_user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get currently active alerts"""
    return traffic_monitor.active_alerts


@router.put("/alerts/thresholds")
async def update_alert_thresholds(
    error_rate: Optional[float] = None,
    response_time_p95: Optional[float] = None,
    requests_per_second: Optional[float] = None,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update alert thresholds"""
    if error_rate is not None:
        traffic_monitor.alert_thresholds["error_rate"] = error_rate

    if response_time_p95 is not None:
        traffic_monitor.alert_thresholds["response_time_p95"] = response_time_p95

    if requests_per_second is not None:
        traffic_monitor.alert_thresholds["requests_per_second"] = requests_per_second

    return {"status": "updated", "thresholds": traffic_monitor.alert_thresholds}


@router.delete("/alerts")
async def clear_alerts(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Clear all active alerts"""
    count = len(traffic_monitor.active_alerts)
    traffic_monitor.active_alerts = []

    return {"status": "cleared", "alerts_cleared": count}


@router.get("/export")
async def export_traffic_data(
    format: str = Query("json", description="Export format (json, csv)"),
    window_seconds: int = Query(3600, description="Time window in seconds"),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Export traffic data for analysis"""
    from datetime import timedelta

    cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
    metrics = [
        m.to_dict() for m in traffic_monitor.metrics if m.timestamp > cutoff_time
    ]

    if format == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()
        if metrics:
            writer = csv.DictWriter(output, fieldnames=metrics[0].keys())
            writer.writeheader()
            writer.writerows(metrics)

        return {"format": "csv", "data": output.getvalue(), "rows": len(metrics)}
    else:
        return {"format": "json", "data": metrics, "count": len(metrics)}

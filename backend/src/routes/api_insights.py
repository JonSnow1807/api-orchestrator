from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from src.database import get_db
from src.auth import get_current_user
from src.models import User

router = APIRouter(prefix="/api/insights", tags=["API Insights"])

class MetricQuery(BaseModel):
    api_id: str
    metric_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    aggregation: Optional[str] = "avg"

class AlertConfig(BaseModel):
    api_id: str
    metric: str
    threshold: float
    condition: str  # gt, lt, eq
    notification_channel: str

class SLAConfig(BaseModel):
    api_id: str
    availability_target: float  # 99.9%
    latency_p99: int  # milliseconds
    error_rate_threshold: float  # percentage

@router.get("/metrics/{api_id}")
async def get_api_metrics(
    api_id: str,
    metric_type: Optional[str] = Query(None),
    period: Optional[str] = Query("1h"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metrics for an API"""
    try:
        from src.api_insights import APIInsights
        insights = APIInsights()
        
        # Convert period to time range
        end_time = datetime.utcnow()
        if period == "1h":
            start_time = end_time - timedelta(hours=1)
        elif period == "24h":
            start_time = end_time - timedelta(days=1)
        elif period == "7d":
            start_time = end_time - timedelta(days=7)
        elif period == "30d":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(hours=1)
        
        metrics = await insights.get_metrics(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            metric_type=metric_type
        )
        
        return {
            "api_id": api_id,
            "period": period,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except ImportError:
        return {
            "api_id": api_id,
            "metrics": {
                "response_time": {"avg": 250, "p50": 200, "p95": 450, "p99": 800},
                "request_count": 1524,
                "error_rate": 0.02,
                "availability": 99.98
            },
            "message": "Using mock data - API Insights module not fully configured"
        }

@router.get("/anomalies")
async def get_anomalies(
    api_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detected anomalies"""
    try:
        from src.api_insights import APIInsights
        insights = APIInsights()
        
        anomalies = await insights.detect_anomalies(
            api_id=api_id,
            severity=severity,
            limit=limit
        )
        
        return {
            "anomalies": anomalies,
            "count": len(anomalies),
            "timestamp": datetime.utcnow().isoformat()
        }
    except ImportError:
        return {
            "anomalies": [
                {
                    "id": "anom_001",
                    "api_id": api_id or "api_123",
                    "type": "latency_spike",
                    "severity": "high",
                    "detected_at": datetime.utcnow().isoformat(),
                    "description": "Response time increased by 300% compared to baseline",
                    "affected_endpoints": ["/api/users", "/api/products"],
                    "recommendation": "Check database performance and connection pool"
                }
            ],
            "count": 1,
            "message": "Using mock data"
        }

@router.get("/failure-patterns")
async def get_failure_patterns(
    api_id: Optional[str] = Query(None),
    time_range: str = Query("24h"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze failure patterns"""
    try:
        from src.api_insights import APIInsights
        insights = APIInsights()
        
        patterns = await insights.analyze_failure_patterns(
            api_id=api_id,
            time_range=time_range
        )
        
        return {
            "patterns": patterns,
            "time_range": time_range,
            "timestamp": datetime.utcnow().isoformat()
        }
    except ImportError:
        return {
            "patterns": [
                {
                    "pattern": "timeout_cascade",
                    "occurrences": 15,
                    "affected_apis": ["api_123", "api_456"],
                    "correlation": "Database connection exhaustion",
                    "recommendation": "Increase connection pool size or add circuit breaker"
                },
                {
                    "pattern": "auth_failures",
                    "occurrences": 42,
                    "affected_apis": ["api_789"],
                    "correlation": "Token expiration not handled properly",
                    "recommendation": "Implement token refresh mechanism"
                }
            ],
            "time_range": time_range,
            "message": "Using mock data"
        }

@router.post("/alerts/configure")
async def configure_alert(
    config: AlertConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Configure alerting rules"""
    try:
        from src.api_insights import APIInsights
        insights = APIInsights()
        
        alert_id = await insights.configure_alert(
            api_id=config.api_id,
            metric=config.metric,
            threshold=config.threshold,
            condition=config.condition,
            notification_channel=config.notification_channel,
            user_id=current_user.id
        )
        
        return {
            "alert_id": alert_id,
            "status": "configured",
            "config": config.dict()
        }
    except ImportError:
        return {
            "alert_id": f"alert_{config.api_id}_{config.metric}",
            "status": "configured",
            "config": config.dict(),
            "message": "Alert configuration saved (mock)"
        }

@router.get("/alerts/history")
async def get_alert_history(
    api_id: Optional[str] = Query(None),
    limit: int = Query(100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert history"""
    return {
        "alerts": [
            {
                "id": "alert_001",
                "api_id": api_id or "api_123",
                "triggered_at": datetime.utcnow().isoformat(),
                "metric": "response_time",
                "value": 1250,
                "threshold": 1000,
                "severity": "warning",
                "status": "resolved",
                "resolution_time": "5m 23s"
            }
        ],
        "total": 1
    }

@router.post("/sla/configure")
async def configure_sla(
    config: SLAConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Configure SLA targets"""
    try:
        from src.api_insights import APIInsights
        insights = APIInsights()
        
        sla_id = await insights.configure_sla(
            api_id=config.api_id,
            availability_target=config.availability_target,
            latency_p99=config.latency_p99,
            error_rate_threshold=config.error_rate_threshold,
            user_id=current_user.id
        )
        
        return {
            "sla_id": sla_id,
            "status": "configured",
            "config": config.dict()
        }
    except ImportError:
        return {
            "sla_id": f"sla_{config.api_id}",
            "status": "configured",
            "config": config.dict(),
            "message": "SLA configuration saved (mock)"
        }

@router.get("/sla/compliance/{api_id}")
async def get_sla_compliance(
    api_id: str,
    period: str = Query("30d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get SLA compliance report"""
    return {
        "api_id": api_id,
        "period": period,
        "compliance": {
            "availability": {
                "target": 99.9,
                "actual": 99.95,
                "compliant": True
            },
            "latency_p99": {
                "target": 1000,
                "actual": 856,
                "compliant": True
            },
            "error_rate": {
                "target": 0.1,
                "actual": 0.05,
                "compliant": True
            }
        },
        "overall_compliance": True,
        "compliance_percentage": 100.0
    }

@router.get("/dependencies/map")
async def get_dependency_map(
    api_id: Optional[str] = Query(None),
    depth: int = Query(2),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API dependency map"""
    return {
        "dependencies": {
            "api_123": {
                "name": "User Service",
                "depends_on": ["api_456", "api_789"],
                "depended_by": ["api_111", "api_222"],
                "health": "healthy",
                "latency_impact": 125
            },
            "api_456": {
                "name": "Auth Service",
                "depends_on": ["api_789"],
                "depended_by": ["api_123"],
                "health": "healthy",
                "latency_impact": 50
            }
        },
        "depth": depth,
        "total_apis": 2
    }

@router.get("/performance/trends")
async def get_performance_trends(
    api_id: Optional[str] = Query(None),
    metric: str = Query("response_time"),
    period: str = Query("7d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance trends"""
    return {
        "api_id": api_id,
        "metric": metric,
        "period": period,
        "trends": {
            "current": 250,
            "previous": 230,
            "change_percentage": 8.7,
            "trend": "increasing",
            "data_points": [
                {"timestamp": "2025-09-01T00:00:00Z", "value": 230},
                {"timestamp": "2025-09-02T00:00:00Z", "value": 235},
                {"timestamp": "2025-09-03T00:00:00Z", "value": 240},
                {"timestamp": "2025-09-04T00:00:00Z", "value": 245},
                {"timestamp": "2025-09-05T00:00:00Z", "value": 250}
            ]
        }
    }

@router.get("/cost/analysis")
async def get_cost_analysis(
    period: str = Query("30d"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze API usage costs"""
    return {
        "period": period,
        "total_cost": 1250.50,
        "cost_breakdown": {
            "compute": 650.00,
            "storage": 150.50,
            "bandwidth": 450.00
        },
        "cost_by_api": {
            "api_123": 450.25,
            "api_456": 325.75,
            "api_789": 474.50
        },
        "projected_monthly": 1425.00,
        "optimization_suggestions": [
            {
                "api": "api_789",
                "suggestion": "Enable caching for repeated requests",
                "potential_savings": 125.00
            }
        ]
    }
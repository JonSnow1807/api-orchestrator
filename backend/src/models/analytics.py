"""
Advanced Analytics Models for API Orchestrator
Real-time metrics, predictive analytics, and business intelligence
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    Text,
    BigInteger,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Dict, List, Any
from enum import Enum

from src.database import Base


class MetricType(Enum):
    """Types of metrics we track"""

    API_CALL = "api_call"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    USER_ACTIVITY = "user_activity"
    RESOURCE_USAGE = "resource_usage"
    COST_SAVING = "cost_saving"
    SECURITY_SCORE = "security_score"
    CODE_GENERATION = "code_generation"
    TEAM_COLLABORATION = "team_collaboration"


class APIMetrics(Base):
    """Real-time API metrics tracking"""

    __tablename__ = "api_metrics"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True)
    api_id = Column(Integer, ForeignKey("api_specs.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Metric details
    metric_type = Column(String(50), index=True)
    endpoint = Column(String(500))
    method = Column(String(10))

    # Performance metrics
    response_time_ms = Column(Integer)  # Response time in milliseconds
    status_code = Column(Integer)
    success = Column(Boolean, default=True)
    error_type = Column(String(100))

    # Size metrics
    request_size_bytes = Column(BigInteger)
    response_size_bytes = Column(BigInteger)

    # Cost metrics
    estimated_cost = Column(Float, default=0.0)  # In USD
    tokens_used = Column(Integer, default=0)  # For AI operations

    # Geographic data
    client_ip = Column(String(45))
    country = Column(String(2))
    region = Column(String(100))

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    workspace = relationship("Workspace")
    api_spec = relationship("APISpec")
    user = relationship("User")


class PerformanceSnapshot(Base):
    """Hourly/Daily performance snapshots for trend analysis"""

    __tablename__ = "performance_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True)
    api_id = Column(Integer, ForeignKey("api_specs.id"), nullable=True)

    # Time window
    period_start = Column(DateTime, index=True)
    period_end = Column(DateTime, index=True)
    period_type = Column(String(20))  # "hour", "day", "week", "month"

    # Aggregated metrics
    total_requests = Column(BigInteger, default=0)
    successful_requests = Column(BigInteger, default=0)
    failed_requests = Column(BigInteger, default=0)

    # Performance percentiles (in milliseconds)
    p50_response_time = Column(Float)
    p75_response_time = Column(Float)
    p90_response_time = Column(Float)
    p95_response_time = Column(Float)
    p99_response_time = Column(Float)
    avg_response_time = Column(Float)

    # Error metrics
    error_rate = Column(Float, default=0.0)  # Percentage
    error_breakdown = Column(JSON)  # {error_type: count}

    # Traffic patterns
    requests_per_minute = Column(Float)
    peak_rpm = Column(Float)
    unique_users = Column(Integer)

    # Business metrics
    total_cost = Column(Float, default=0.0)
    cost_saved = Column(Float, default=0.0)

    # Relationships
    workspace = relationship("Workspace")
    api_spec = relationship("APISpec")


class BusinessMetrics(Base):
    """Business value and ROI metrics"""

    __tablename__ = "business_metrics"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True)

    # Time period
    period_start = Column(DateTime, index=True)
    period_end = Column(DateTime, index=True)
    period_type = Column(String(20))  # "day", "week", "month", "quarter"

    # Development metrics
    apis_created = Column(Integer, default=0)
    apis_modified = Column(Integer, default=0)
    code_generated_lines = Column(BigInteger, default=0)
    tests_generated = Column(Integer, default=0)
    mock_servers_created = Column(Integer, default=0)

    # Team metrics
    active_users = Column(Integer, default=0)
    team_collaborations = Column(Integer, default=0)
    api_shares = Column(Integer, default=0)

    # Time savings (in hours)
    time_saved_discovery = Column(Float, default=0.0)
    time_saved_testing = Column(Float, default=0.0)
    time_saved_documentation = Column(Float, default=0.0)
    time_saved_code_gen = Column(Float, default=0.0)
    total_time_saved = Column(Float, default=0.0)

    # Cost metrics (in USD)
    development_cost_saved = Column(Float, default=0.0)
    infrastructure_cost_saved = Column(Float, default=0.0)
    total_cost_saved = Column(Float, default=0.0)

    # ROI calculation
    platform_cost = Column(Float, default=0.0)
    roi_percentage = Column(Float, default=0.0)

    # Quality metrics
    bugs_prevented = Column(Integer, default=0)
    security_issues_found = Column(Integer, default=0)
    compliance_violations_found = Column(Integer, default=0)

    # Relationships
    workspace = relationship("Workspace")


class UserActivityMetrics(Base):
    """Track user engagement and productivity"""

    __tablename__ = "user_activity_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True)

    # Activity tracking
    date = Column(DateTime, index=True)
    login_count = Column(Integer, default=0)
    active_minutes = Column(Integer, default=0)

    # Feature usage
    apis_tested = Column(Integer, default=0)
    code_generated = Column(Integer, default=0)
    mock_servers_used = Column(Integer, default=0)
    exports_created = Column(Integer, default=0)

    # Collaboration
    apis_shared = Column(Integer, default=0)
    comments_made = Column(Integer, default=0)
    invites_sent = Column(Integer, default=0)

    # Productivity score (0-100)
    productivity_score = Column(Float, default=0.0)

    # Relationships
    user = relationship("User")
    workspace = relationship("Workspace")


class PredictiveAnalytics(Base):
    """AI-powered predictive analytics and insights"""

    __tablename__ = "predictive_analytics"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True)

    # Predictions
    prediction_type = Column(String(50))  # "traffic", "cost", "errors", "growth"
    prediction_date = Column(DateTime, index=True)

    # Predicted values
    predicted_value = Column(Float)
    confidence_score = Column(Float)  # 0-100

    # Insights
    insight = Column(Text)  # AI-generated insight
    recommendations = Column(JSON)  # List of recommendations

    # Actual vs Predicted (for tracking accuracy)
    actual_value = Column(Float, nullable=True)
    prediction_accuracy = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String(50))

    # Relationships
    workspace = relationship("Workspace")


class CostAnalytics(Base):
    """Detailed cost tracking and savings analysis"""

    __tablename__ = "cost_analytics"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True)

    # Time period
    date = Column(DateTime, index=True)

    # Traditional costs (what it would cost without our platform)
    traditional_development_cost = Column(Float, default=0.0)
    traditional_testing_cost = Column(Float, default=0.0)
    traditional_documentation_cost = Column(Float, default=0.0)
    traditional_infrastructure_cost = Column(Float, default=0.0)

    # Platform costs
    platform_subscription_cost = Column(Float, default=0.0)
    platform_usage_cost = Column(Float, default=0.0)

    # Savings
    total_saved = Column(Float, default=0.0)
    percentage_saved = Column(Float, default=0.0)

    # Time to value
    implementation_hours_saved = Column(Float, default=0.0)

    # Breakdown by feature
    savings_breakdown = Column(JSON)  # {feature: amount_saved}

    # Relationships
    workspace = relationship("Workspace")


class SecurityMetrics(Base):
    """Security scanning and vulnerability metrics"""

    __tablename__ = "security_metrics"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True)
    api_id = Column(Integer, ForeignKey("api_specs.id"), index=True)

    # Security scan results
    scan_date = Column(DateTime, default=datetime.utcnow, index=True)
    security_score = Column(Float)  # 0-100

    # Vulnerability counts by severity
    critical_vulnerabilities = Column(Integer, default=0)
    high_vulnerabilities = Column(Integer, default=0)
    medium_vulnerabilities = Column(Integer, default=0)
    low_vulnerabilities = Column(Integer, default=0)

    # Specific issues
    authentication_issues = Column(Integer, default=0)
    authorization_issues = Column(Integer, default=0)
    injection_risks = Column(Integer, default=0)
    data_exposure_risks = Column(Integer, default=0)

    # Compliance
    gdpr_compliant = Column(Boolean, default=False)
    hipaa_compliant = Column(Boolean, default=False)
    soc2_compliant = Column(Boolean, default=False)
    pci_compliant = Column(Boolean, default=False)

    # Improvements
    issues_fixed_since_last_scan = Column(Integer, default=0)

    # Detailed report
    detailed_report = Column(JSON)

    # Relationships
    workspace = relationship("Workspace")
    api_spec = relationship("APISpec")


class AnalyticsService:
    """Service for analytics calculations and insights"""

    @staticmethod
    def calculate_roi(workspace_id: int, db) -> Dict[str, Any]:
        """Calculate ROI for a workspace"""
        # Get latest business metrics
        metrics = (
            db.query(BusinessMetrics)
            .filter(BusinessMetrics.workspace_id == workspace_id)
            .order_by(BusinessMetrics.period_end.desc())
            .first()
        )

        if not metrics:
            return {"roi": 0, "savings": 0, "message": "No data available"}

        roi = (
            (
                (metrics.total_cost_saved - metrics.platform_cost)
                / metrics.platform_cost
                * 100
            )
            if metrics.platform_cost > 0
            else 0
        )

        return {
            "roi_percentage": round(roi, 2),
            "total_savings": metrics.total_cost_saved,
            "platform_cost": metrics.platform_cost,
            "time_saved_hours": metrics.total_time_saved,
            "apis_created": metrics.apis_created,
            "tests_generated": metrics.tests_generated,
        }

    @staticmethod
    def get_performance_trends(workspace_id: int, days: int, db) -> List[Dict]:
        """Get performance trends over time"""
        start_date = datetime.utcnow() - timedelta(days=days)

        snapshots = (
            db.query(PerformanceSnapshot)
            .filter(
                PerformanceSnapshot.workspace_id == workspace_id,
                PerformanceSnapshot.period_start >= start_date,
                PerformanceSnapshot.period_type == "day",
            )
            .order_by(PerformanceSnapshot.period_start)
            .all()
        )

        return [
            {
                "date": s.period_start.isoformat(),
                "requests": s.total_requests,
                "error_rate": s.error_rate,
                "p50": s.p50_response_time,
                "p95": s.p95_response_time,
                "p99": s.p99_response_time,
            }
            for s in snapshots
        ]

    @staticmethod
    def generate_insights(workspace_id: int, db) -> List[str]:
        """Generate AI-powered insights"""
        insights = []

        # Get recent metrics
        recent_metrics = (
            db.query(APIMetrics)
            .filter(
                APIMetrics.workspace_id == workspace_id,
                APIMetrics.timestamp >= datetime.utcnow() - timedelta(days=7),
            )
            .all()
        )

        # Analyze patterns
        if recent_metrics:
            error_rate = (
                sum(1 for m in recent_metrics if not m.success)
                / len(recent_metrics)
                * 100
            )
            if error_rate > 5:
                insights.append(
                    f"⚠️ High error rate detected ({error_rate:.1f}%). Consider reviewing error logs."
                )

            avg_response = sum(
                m.response_time_ms for m in recent_metrics if m.response_time_ms
            ) / len(recent_metrics)
            if avg_response > 1000:
                insights.append(
                    f"🐌 Slow API responses averaging {avg_response:.0f}ms. Consider optimization."
                )

            # Cost analysis
            total_cost = sum(
                m.estimated_cost for m in recent_metrics if m.estimated_cost
            )
            if total_cost > 100:
                insights.append(
                    f"💰 High API costs detected (${total_cost:.2f} this week). Review usage patterns."
                )

        return insights

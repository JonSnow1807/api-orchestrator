"""
Enterprise Audit Logging System for API Orchestrator
Comprehensive audit trail for compliance, security, and governance
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    JSON,
    Boolean,
    Index,
    func,
)
from sqlalchemy.orm import Session
import uuid
import hashlib
import ipaddress
from geoip2 import database as geoip_db
from geoip2.errors import AddressNotFoundError

from src.database import Base
from src.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# AUDIT MODELS AND ENUMS
# =============================================================================


class AuditEventType(str, Enum):
    """Audit event types for categorization"""

    # Authentication & Authorization
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    PASSWORD_CHANGE = "auth.password_change"
    TOKEN_REFRESH = "auth.token_refresh"
    SSO_LOGIN = "auth.sso_login"

    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ACTIVATE = "user.activate"
    USER_DEACTIVATE = "user.deactivate"

    # API Operations
    API_CREATE = "api.create"
    API_UPDATE = "api.update"
    API_DELETE = "api.delete"
    API_TEST = "api.test"
    API_EXPORT = "api.export"
    API_IMPORT = "api.import"

    # Project Management
    PROJECT_CREATE = "project.create"
    PROJECT_UPDATE = "project.update"
    PROJECT_DELETE = "project.delete"
    PROJECT_SHARE = "project.share"
    PROJECT_EXPORT = "project.export"

    # Team & Workspace
    WORKSPACE_CREATE = "workspace.create"
    WORKSPACE_UPDATE = "workspace.update"
    WORKSPACE_DELETE = "workspace.delete"
    TEAM_MEMBER_ADD = "team.member_add"
    TEAM_MEMBER_REMOVE = "team.member_remove"
    ROLE_CHANGE = "team.role_change"

    # Security Events
    PERMISSION_DENIED = "security.permission_denied"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    DATA_BREACH_ATTEMPT = "security.data_breach_attempt"
    RATE_LIMIT_EXCEEDED = "security.rate_limit_exceeded"

    # System Operations
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_UPDATE = "system.update"

    # Compliance
    DATA_EXPORT = "compliance.data_export"
    DATA_DELETION = "compliance.data_deletion"
    GDPR_REQUEST = "compliance.gdpr_request"
    AUDIT_LOG_ACCESS = "compliance.audit_access"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditStatus(str, Enum):
    """Audit event status"""

    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class AuditContext:
    """Audit event context information"""

    user_id: Optional[int] = None
    user_email: Optional[str] = None
    session_id: Optional[str] = None
    workspace_id: Optional[int] = None
    project_id: Optional[int] = None
    api_id: Optional[int] = None
    team_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[Dict[str, str]] = None
    device_fingerprint: Optional[str] = None


class AuditLog(Base):
    """Audit log entry model"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )

    # Event Information
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSON)

    # Context Information
    user_id = Column(Integer, index=True)
    user_email = Column(String(255), index=True)
    session_id = Column(String(255), index=True)
    workspace_id = Column(Integer, index=True)
    project_id = Column(Integer, index=True)
    api_id = Column(Integer, index=True)
    team_id = Column(Integer, index=True)

    # Request Information
    ip_address = Column(String(45), index=True)  # IPv6 support
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_path = Column(String(500))
    request_query = Column(Text)
    request_headers = Column(JSON)
    request_body_hash = Column(String(64))  # SHA-256 hash for sensitive data

    # Response Information
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    response_size_bytes = Column(Integer)

    # Location Information
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    latitude = Column(String(20))
    longitude = Column(String(20))

    # Security Information
    device_fingerprint = Column(String(255))
    risk_score = Column(Integer, default=0)
    flags = Column(JSON)  # Security flags and annotations

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)
    retention_until = Column(DateTime, index=True)

    # Compliance
    gdpr_category = Column(String(50))
    compliance_tags = Column(JSON)

    __table_args__ = (
        Index("idx_audit_user_time", user_id, timestamp),
        Index("idx_audit_event_time", event_type, timestamp),
        Index("idx_audit_severity_time", severity, timestamp),
        Index("idx_audit_ip_time", ip_address, timestamp),
        Index("idx_audit_workspace_time", workspace_id, timestamp),
    )


class AuditAlert(Base):
    """Audit alert rules and triggers"""

    __tablename__ = "audit_alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Alert Conditions
    event_types = Column(JSON)  # List of event types to monitor
    severity_threshold = Column(String(20))
    user_pattern = Column(String(255))  # Regex pattern for user emails
    ip_pattern = Column(String(255))  # IP range or pattern
    frequency_threshold = Column(Integer)  # Events per time window
    time_window_minutes = Column(Integer, default=60)

    # Alert Actions
    webhook_url = Column(String(500))
    email_recipients = Column(JSON)
    slack_webhook = Column(String(500))

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# AUDIT MANAGER
# =============================================================================


class EnterpriseAuditManager:
    """Enterprise audit logging and monitoring system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.geoip_reader = self._init_geoip()
        self.alert_cache = {}

    def _init_geoip(self):
        """Initialize GeoIP database for location tracking"""
        try:
            # Try to load GeoLite2 database (requires maxminddb)
            return geoip_db.Reader("/usr/local/share/GeoIP/GeoLite2-City.mmdb")
        except Exception as e:
            self.logger.warning(f"GeoIP database not available: {e}")
            return None

    async def log_event(
        self,
        event_type: AuditEventType,
        message: str,
        context: AuditContext,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        status: AuditStatus = AuditStatus.SUCCESS,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
        db: Optional[Session] = None,
    ) -> str:
        """Log an audit event"""

        event_id = str(uuid.uuid4())

        # Extract location information
        location_info = {}
        if context.ip_address and self.geoip_reader:
            try:
                location = self.geoip_reader.city(context.ip_address)
                location_info = {
                    "country": location.country.iso_code,
                    "region": location.subdivisions.most_specific.name,
                    "city": location.city.name,
                    "latitude": str(location.location.latitude),
                    "longitude": str(location.location.longitude),
                }
            except (AddressNotFoundError, Exception):
                pass

        # Calculate risk score
        risk_score = self._calculate_risk_score(context, event_type, location_info)

        # Prepare request/response information
        request_info = {}
        response_info = {}

        if request:
            request_info = {
                "method": request.method,
                "path": str(request.url.path),
                "query": str(request.url.query) if request.url.query else None,
                "headers": dict(request.headers),
                "body_hash": self._hash_request_body(request)
                if hasattr(request, "body")
                else None,
            }

        if response:
            response_info = {
                "status": getattr(response, "status_code", None),
                "size_bytes": len(getattr(response, "body", b"")),
            }

        # Create audit log entry
        audit_entry = AuditLog(
            event_id=event_id,
            event_type=event_type.value,
            severity=severity.value,
            status=status.value,
            message=message,
            details=details or {},
            # Context
            user_id=context.user_id,
            user_email=context.user_email,
            session_id=context.session_id,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            api_id=context.api_id,
            team_id=context.team_id,
            # Request/Response
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            request_method=request_info.get("method"),
            request_path=request_info.get("path"),
            request_query=request_info.get("query"),
            request_headers=request_info.get("headers"),
            request_body_hash=request_info.get("body_hash"),
            response_status=response_info.get("status"),
            response_size_bytes=response_info.get("size_bytes"),
            # Location
            country=location_info.get("country"),
            region=location_info.get("region"),
            city=location_info.get("city"),
            latitude=location_info.get("latitude"),
            longitude=location_info.get("longitude"),
            # Security
            device_fingerprint=context.device_fingerprint,
            risk_score=risk_score,
            # Compliance
            retention_until=datetime.utcnow()
            + timedelta(days=settings.AUDIT_RETENTION_DAYS),
        )

        # Save to database
        if db:
            db.add(audit_entry)
            try:
                db.commit()
            except Exception as e:
                self.logger.error(f"Failed to save audit log: {e}")
                db.rollback()

        # Check for alerts
        await self._check_alerts(audit_entry, db)

        # Log to external systems (async)
        asyncio.create_task(self._log_to_external_systems(audit_entry))

        return event_id

    def _calculate_risk_score(
        self,
        context: AuditContext,
        event_type: AuditEventType,
        location_info: Dict[str, str],
    ) -> int:
        """Calculate risk score for the event (0-100)"""
        risk_score = 0

        # Base risk by event type
        high_risk_events = [
            AuditEventType.LOGIN_FAILED,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.DATA_BREACH_ATTEMPT,
        ]

        if event_type in high_risk_events:
            risk_score += 30
        elif event_type.value.startswith("auth."):
            risk_score += 10
        elif event_type.value.startswith("security."):
            risk_score += 20

        # IP address analysis
        if context.ip_address:
            try:
                ip = ipaddress.ip_address(context.ip_address)
                if ip.is_private:
                    risk_score -= 5  # Lower risk for internal IPs
                else:
                    risk_score += 5  # Higher risk for external IPs
            except ValueError:
                pass

        # Location analysis
        if location_info.get("country"):
            # Add risk for countries with higher threat profiles
            high_risk_countries = ["CN", "RU", "KP", "IR"]
            if location_info["country"] in high_risk_countries:
                risk_score += 15

        # Time-based analysis
        hour = datetime.utcnow().hour
        if hour < 6 or hour > 22:  # Outside business hours
            risk_score += 5

        return min(risk_score, 100)

    def _hash_request_body(self, request: Request) -> Optional[str]:
        """Create SHA-256 hash of request body for audit trail"""
        try:
            if hasattr(request, "body"):
                body_bytes = (
                    request.body
                    if isinstance(request.body, bytes)
                    else str(request.body).encode()
                )
                return hashlib.sha256(body_bytes).hexdigest()
        except Exception:
            pass
        return None

    async def _check_alerts(self, audit_entry: AuditLog, db: Optional[Session]):
        """Check if audit entry triggers any alerts"""
        if not db:
            return

        # Get active alert rules
        alerts = db.query(AuditAlert).filter(AuditAlert.is_active == True).all()

        for alert in alerts:
            if self._should_trigger_alert(alert, audit_entry, db):
                await self._trigger_alert(alert, audit_entry)

    def _should_trigger_alert(
        self, alert: AuditAlert, audit_entry: AuditLog, db: Session
    ) -> bool:
        """Check if alert conditions are met"""
        # Check event type
        if alert.event_types and audit_entry.event_type not in alert.event_types:
            return False

        # Check severity threshold
        severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        if severity_levels.get(audit_entry.severity, 0) < severity_levels.get(
            alert.severity_threshold, 0
        ):
            return False

        # Check frequency threshold
        if alert.frequency_threshold:
            time_window = datetime.utcnow() - timedelta(
                minutes=alert.time_window_minutes
            )
            recent_events = (
                db.query(AuditLog)
                .filter(
                    AuditLog.event_type == audit_entry.event_type,
                    AuditLog.timestamp >= time_window,
                    AuditLog.user_id == audit_entry.user_id,
                )
                .count()
            )

            if recent_events < alert.frequency_threshold:
                return False

        return True

    async def _trigger_alert(self, alert: AuditAlert, audit_entry: AuditLog):
        """Trigger alert notification"""
        alert_data = {
            "alert_name": alert.name,
            "event_type": audit_entry.event_type,
            "severity": audit_entry.severity,
            "user_email": audit_entry.user_email,
            "ip_address": audit_entry.ip_address,
            "timestamp": audit_entry.timestamp.isoformat(),
            "message": audit_entry.message,
            "risk_score": audit_entry.risk_score,
        }

        # Send webhook notification
        if alert.webhook_url:
            asyncio.create_task(self._send_webhook(alert.webhook_url, alert_data))

        # Send email notification
        if alert.email_recipients:
            asyncio.create_task(
                self._send_email_alert(alert.email_recipients, alert_data)
            )

        # Send Slack notification
        if alert.slack_webhook:
            asyncio.create_task(self._send_slack_alert(alert.slack_webhook, alert_data))

    async def _send_webhook(self, webhook_url: str, alert_data: Dict[str, Any]):
        """Send webhook notification"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=alert_data) as response:
                    if response.status != 200:
                        self.logger.warning(f"Webhook failed: {response.status}")
        except Exception as e:
            self.logger.error(f"Webhook error: {e}")

    async def _send_email_alert(
        self, recipients: List[str], alert_data: Dict[str, Any]
    ):
        """Send email alert"""
        # Implementation would depend on email service (SendGrid, SES, etc.)
        self.logger.info(
            f"Email alert sent to {recipients}: {alert_data['alert_name']}"
        )

    async def _send_slack_alert(self, webhook_url: str, alert_data: Dict[str, Any]):
        """Send Slack alert"""
        import aiohttp

        slack_message = {
            "text": f"🚨 Security Alert: {alert_data['alert_name']}",
            "attachments": [
                {
                    "color": "danger"
                    if alert_data["severity"] in ["high", "critical"]
                    else "warning",
                    "fields": [
                        {
                            "title": "Event Type",
                            "value": alert_data["event_type"],
                            "short": True,
                        },
                        {
                            "title": "Severity",
                            "value": alert_data["severity"],
                            "short": True,
                        },
                        {
                            "title": "User",
                            "value": alert_data["user_email"],
                            "short": True,
                        },
                        {
                            "title": "IP Address",
                            "value": alert_data["ip_address"],
                            "short": True,
                        },
                        {
                            "title": "Risk Score",
                            "value": str(alert_data["risk_score"]),
                            "short": True,
                        },
                        {
                            "title": "Time",
                            "value": alert_data["timestamp"],
                            "short": True,
                        },
                    ],
                }
            ],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=slack_message) as response:
                    if response.status != 200:
                        self.logger.warning(f"Slack webhook failed: {response.status}")
        except Exception as e:
            self.logger.error(f"Slack webhook error: {e}")

    async def _log_to_external_systems(self, audit_entry: AuditLog):
        """Log to external audit systems (SIEM, etc.)"""
        # Implementation for external systems like Splunk, ELK, etc.

    async def search_audit_logs(
        self,
        db: Session,
        user_id: Optional[int] = None,
        event_types: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[str] = None,
        ip_address: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Search audit logs with filters"""
        query = db.query(AuditLog)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if event_types:
            query = query.filter(AuditLog.event_type.in_(event_types))
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        if ip_address:
            query = query.filter(AuditLog.ip_address == ip_address)

        return (
            query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        )

    async def get_audit_statistics(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get audit log statistics"""
        query = db.query(AuditLog)

        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        # Event type distribution
        event_stats = (
            db.query(AuditLog.event_type, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.event_type)
            .all()
        )

        # Severity distribution
        severity_stats = (
            db.query(AuditLog.severity, func.count(AuditLog.id).label("count"))
            .group_by(AuditLog.severity)
            .all()
        )

        # Top IPs
        ip_stats = (
            db.query(AuditLog.ip_address, func.count(AuditLog.id).label("count"))
            .filter(AuditLog.ip_address.isnot(None))
            .group_by(AuditLog.ip_address)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
            .all()
        )

        return {
            "total_events": query.count(),
            "event_types": dict(event_stats),
            "severity_distribution": dict(severity_stats),
            "top_ips": dict(ip_stats),
        }


# =============================================================================
# AUDIT MIDDLEWARE
# =============================================================================


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically audit HTTP requests"""

    def __init__(self, app, audit_manager: EnterpriseAuditManager):
        super().__init__(app)
        self.audit_manager = audit_manager

    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()

        # Extract request information
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        response = await call_next(request)

        # Calculate response time
        int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Log API access (for sensitive endpoints)
        if self._should_audit_request(request):
            context = AuditContext(ip_address=ip_address, user_agent=user_agent)

            # Try to get user from request
            try:
                # This would need to be adapted based on your auth system
                user = getattr(request.state, "user", None)
                if user:
                    context.user_id = user.id
                    context.user_email = user.email
            except Exception:
                pass

            await self.audit_manager.log_event(
                event_type=AuditEventType.API_TEST,
                message=f"API request: {request.method} {request.url.path}",
                context=context,
                severity=AuditSeverity.LOW,
                request=request,
                response=response,
            )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (load balancer/proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _should_audit_request(self, request: Request) -> bool:
        """Determine if request should be audited"""
        # Audit API endpoints but skip health checks and static files
        path = request.url.path

        skip_paths = ["/health", "/metrics", "/static/", "/docs", "/redoc"]
        if any(path.startswith(skip) for skip in skip_paths):
            return False

        # Audit write operations and sensitive reads
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            return True

        # Audit sensitive GET endpoints
        sensitive_paths = ["/api/v1/projects/", "/api/v1/users/", "/api/v1/admin/"]
        if any(path.startswith(sensitive) for sensitive in sensitive_paths):
            return True

        return False


# =============================================================================
# AUDIT DECORATOR
# =============================================================================


def audit_action(
    event_type: AuditEventType,
    message: str,
    severity: AuditSeverity = AuditSeverity.MEDIUM,
    include_request: bool = False,
    include_response: bool = False,
):
    """Decorator to audit specific actions"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Extract context from function arguments
            context = AuditContext()
            request = None
            db = None

            # Try to extract common parameters
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    context.ip_address = audit_manager._get_client_ip(request)
                    context.user_agent = request.headers.get("user-agent", "")
                elif isinstance(arg, Session):
                    db = arg

            for key, value in kwargs.items():
                if key == "current_user" and hasattr(value, "id"):
                    context.user_id = value.id
                    context.user_email = value.email
                elif key == "db" and isinstance(value, Session):
                    db = value
                elif key == "request" and isinstance(value, Request):
                    request = value

            try:
                result = await func(*args, **kwargs)
                status = AuditStatus.SUCCESS
                details = {"result": "success"}
            except Exception as e:
                status = AuditStatus.ERROR
                details = {"error": str(e), "exception_type": type(e).__name__}
                raise
            finally:
                await audit_manager.log_event(
                    event_type=event_type,
                    message=message.format(**kwargs) if "{" in message else message,
                    context=context,
                    severity=severity,
                    status=status,
                    details=details,
                    request=request if include_request else None,
                    db=db,
                )

            return result

        def sync_wrapper(*args, **kwargs):
            return asyncio.run(async_wrapper(*args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

audit_manager = EnterpriseAuditManager()

# =============================================================================
# COMPLIANCE HELPERS
# =============================================================================


class ComplianceManager:
    """Compliance and data governance helpers"""

    @staticmethod
    async def export_user_audit_data(
        user_id: int,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Export all audit data for a user (GDPR compliance)"""
        query = db.query(AuditLog).filter(AuditLog.user_id == user_id)

        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        logs = query.all()

        return {
            "user_id": user_id,
            "export_date": datetime.utcnow().isoformat(),
            "total_records": len(logs),
            "audit_logs": [
                {
                    "event_id": log.event_id,
                    "event_type": log.event_type,
                    "timestamp": log.timestamp.isoformat(),
                    "message": log.message,
                    "ip_address": log.ip_address,
                    "location": f"{log.city}, {log.region}, {log.country}"
                    if log.city
                    else None,
                    "details": log.details,
                }
                for log in logs
            ],
        }

    @staticmethod
    async def anonymize_user_audit_data(user_id: int, db: Session):
        """Anonymize audit data for a deleted user"""
        db.query(AuditLog).filter(AuditLog.user_id == user_id).update(
            {"user_email": "anonymized@deleted.user", "user_id": None, "details": {}}
        )
        db.commit()

    @staticmethod
    async def cleanup_expired_logs(db: Session):
        """Clean up expired audit logs"""
        cutoff_date = datetime.utcnow()
        expired_logs = (
            db.query(AuditLog).filter(AuditLog.retention_until <= cutoff_date).delete()
        )
        db.commit()
        return expired_logs

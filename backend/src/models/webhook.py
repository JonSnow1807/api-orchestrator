from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from src.database import Base


class WebhookEvent(enum.Enum):
    """Events that can trigger webhooks"""

    API_DISCOVERED = "api_discovered"
    API_TESTED = "api_tested"
    SECURITY_ALERT = "security_alert"
    PERFORMANCE_ISSUE = "performance_issue"
    API_VERSION_CHANGED = "api_version_changed"
    MOCK_SERVER_STARTED = "mock_server_started"
    MOCK_SERVER_STOPPED = "mock_server_stopped"
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"
    ERROR_THRESHOLD_EXCEEDED = "error_threshold_exceeded"
    WORKSPACE_MEMBER_ADDED = "workspace_member_added"
    WORKSPACE_MEMBER_REMOVED = "workspace_member_removed"
    API_DOCUMENTATION_GENERATED = "api_documentation_generated"
    COMPLIANCE_CHECK_FAILED = "compliance_check_failed"


class WebhookStatus(enum.Enum):
    """Webhook delivery status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    SUSPENDED = "suspended"


class Webhook(Base):
    """Webhook configuration model"""

    __tablename__ = "webhooks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    url = Column(String(500), nullable=False)
    secret = Column(String(255))  # For HMAC signature verification
    events = Column(JSON, nullable=False)  # List of WebhookEvent values
    headers = Column(JSON)  # Custom headers to include
    status = Column(SQLEnum(WebhookStatus), default=WebhookStatus.ACTIVE)
    retry_count = Column(Integer, default=3)
    retry_delay = Column(Integer, default=60)  # seconds
    timeout = Column(Integer, default=30)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered_at = Column(DateTime)
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)

    # SSL/TLS settings
    verify_ssl = Column(Boolean, default=True)

    # Rate limiting
    rate_limit = Column(Integer, default=100)  # max calls per minute

    # Filtering
    filters = Column(JSON)  # Additional filters for events

    # Relationships
    workspace = relationship("Workspace", back_populates="webhooks")
    deliveries = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Webhook(id={self.id}, name='{self.name}', url='{self.url}')>"


class WebhookDelivery(Base):
    """Record of webhook delivery attempts"""

    __tablename__ = "webhook_deliveries"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False)
    event = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status_code = Column(Integer)
    response_body = Column(Text)
    response_headers = Column(JSON)
    attempt_count = Column(Integer, default=1)
    delivered = Column(Boolean, default=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    next_retry_at = Column(DateTime)
    duration_ms = Column(Integer)  # Response time in milliseconds

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")

    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, webhook_id={self.webhook_id}, delivered={self.delivered})>"

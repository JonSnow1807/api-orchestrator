"""
Database Models for API Orchestrator
Using SQLAlchemy for ORM with PostgreSQL/SQLite support
"""

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    Text,
    JSON,
    Float,
    Boolean,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
import os
from typing import Optional, List

# Database URL from environment or default to SQLite
# Use /app/data for Railway persistent storage
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Railway PostgreSQL URLs use 'postgres://' but SQLAlchemy needs 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# If no DATABASE_URL, use SQLite
if not DATABASE_URL:
    if os.path.exists("/app"):
        # Running on Railway without PostgreSQL
        DATABASE_URL = "sqlite:////app/data/api_orchestrator.db"
    else:
        # Local development
        DATABASE_URL = "sqlite:///./api_orchestrator.db"

# Log database type being used
import logging

logger = logging.getLogger(__name__)
logger.info(f"Using database: {DATABASE_URL.split('://')[0]}")

# Configure engine based on database type
if "postgresql" in DATABASE_URL:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("DB_ECHO", "False").lower() == "true",
    )
elif "sqlite" in DATABASE_URL:
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=os.getenv("DB_ECHO", "False").lower() == "true",
    )
else:
    # Default configuration for other databases
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=os.getenv("DB_ECHO", "False").lower() == "true",
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Database helper
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Get database session (synchronous version)"""
    return SessionLocal()


# Models


class Project(Base):
    """Project model - groups APIs together"""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # Add user association
    name = Column(
        String(255), index=True, nullable=False
    )  # Remove unique constraint, unique per user
    description = Column(Text)
    source_type = Column(String(50))  # directory, github, upload
    source_path = Column(String(500))
    github_url = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="projects")
    apis = relationship("API", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    mock_servers = relationship(
        "MockServer", back_populates="project", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "github_url": self.github_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "api_count": len(self.apis),
            "task_count": len(self.tasks),
        }


class API(Base):
    """API endpoint model"""

    __tablename__ = "apis"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    handler_name = Column(String(255))
    description = Column(Text)
    parameters = Column(JSON)  # Store as JSON
    response_schema = Column(JSON)
    auth_required = Column(Boolean, default=False)
    rate_limit = Column(Integer)
    discovered_at = Column(DateTime, default=func.now())

    # AI Analysis Results
    security_score = Column(Float)
    security_issues = Column(JSON)
    optimization_suggestions = Column(JSON)
    test_coverage = Column(Float)

    # Relationships
    project = relationship("Project", back_populates="apis")
    tests = relationship("Test", back_populates="api", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "path": self.path,
            "method": self.method,
            "handler_name": self.handler_name,
            "description": self.description,
            "parameters": self.parameters,
            "response_schema": self.response_schema,
            "auth_required": self.auth_required,
            "rate_limit": self.rate_limit,
            "security_score": self.security_score,
            "test_coverage": self.test_coverage,
            "discovered_at": self.discovered_at.isoformat()
            if self.discovered_at
            else None,
        }


class OpenAPISpec(Base):
    """OpenAPI Specification model"""

    __tablename__ = "openapi_specs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version = Column(String(20), default="3.0.0")
    spec_data = Column(JSON, nullable=False)  # Complete OpenAPI spec
    generated_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "version": self.version,
            "spec_data": self.spec_data,
            "generated_at": self.generated_at.isoformat()
            if self.generated_at
            else None,
        }


class Test(Base):
    """Test case model"""

    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False)
    name = Column(String(255), nullable=False)
    test_type = Column(String(50))  # unit, integration, security, performance
    framework = Column(String(50))  # pytest, jest, postman, locust
    code = Column(Text)
    description = Column(Text)
    severity = Column(String(20))  # critical, high, medium, low
    status = Column(String(20), default="pending")  # pending, passed, failed
    last_run = Column(DateTime)
    execution_time = Column(Float)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    api = relationship("API", back_populates="tests")

    def to_dict(self):
        return {
            "id": self.id,
            "api_id": self.api_id,
            "name": self.name,
            "test_type": self.test_type,
            "framework": self.framework,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "execution_time": self.execution_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Task(Base):
    """Orchestration task model"""

    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)  # UUID
    project_id = Column(Integer, ForeignKey("projects.id"))
    status = Column(
        String(20), default="pending"
    )  # pending, running, completed, failed
    stage = Column(String(50))  # discovery, spec_generation, test_generation, etc.
    progress = Column(Integer, default=0)  # 0-100
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    error_message = Column(Text)

    # Results
    apis_found = Column(Integer, default=0)
    specs_generated = Column(Integer, default=0)
    tests_created = Column(Integer, default=0)
    security_issues_found = Column(Integer, default=0)

    # Business Value
    hours_saved = Column(Float)
    money_saved = Column(Float)
    roi_percentage = Column(Float)

    # Relationships
    project = relationship("Project", back_populates="tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "status": self.status,
            "stage": self.stage,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "error_message": self.error_message,
            "results": {
                "apis_found": self.apis_found,
                "specs_generated": self.specs_generated,
                "tests_created": self.tests_created,
                "security_issues_found": self.security_issues_found,
            },
            "business_value": {
                "hours_saved": self.hours_saved,
                "money_saved": self.money_saved,
                "roi_percentage": self.roi_percentage,
            },
        }


class MockServer(Base):
    """Mock server configuration model"""

    __tablename__ = "mock_servers"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255))
    port = Column(Integer, default=8001)
    host = Column(String(50), default="0.0.0.0")
    status = Column(String(20), default="stopped")  # running, stopped
    docker_image = Column(String(255))
    config = Column(JSON)  # delay, error_rate, etc.
    created_at = Column(DateTime, default=func.now())
    last_started = Column(DateTime)

    # Relationships
    project = relationship("Project", back_populates="mock_servers")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "port": self.port,
            "host": self.host,
            "status": self.status,
            "url": f"http://{self.host}:{self.port}"
            if self.status == "running"
            else None,
            "docker_image": self.docker_image,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_started": self.last_started.isoformat()
            if self.last_started
            else None,
        }


class User(Base):
    """User model for authentication"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)
    password_changed_at = Column(DateTime)

    # Subscription
    subscription_tier = Column(
        String(50), default="free"
    )  # free, starter, professional, enterprise
    subscription_expires = Column(DateTime)
    api_calls_this_month = Column(Integer, default=0)
    api_calls_limit = Column(Integer, default=1000)  # Based on tier

    # Billing
    stripe_customer_id = Column(String(255), unique=True)
    stripe_subscription_id = Column(String(255))
    stripe_payment_method_id = Column(String(255))
    subscription_id = Column(String(255))
    subscription_item_id = Column(String(255))
    subscription_status = Column(
        String(50), default="active"
    )  # active, past_due, canceled, trialing
    subscription_end_date = Column(DateTime)
    trial_end_date = Column(DateTime)

    # Usage metrics
    ai_analyses_this_month = Column(Integer, default=0)
    mock_server_hours_this_month = Column(Float, default=0.0)
    exports_this_month = Column(Integer, default=0)

    # Profile
    full_name = Column(String(255))
    company_name = Column(String(255))
    phone_number = Column(String(50))
    country = Column(String(100))

    # API Keys
    api_key = Column(String(255), unique=True)
    api_key_created_at = Column(DateTime)

    # Enterprise SSO
    sso_provider = Column(String(100))  # SAML/OIDC provider ID
    sso_user_id = Column(String(255))  # Provider's user ID
    sso_attributes = Column(JSON)  # Additional SSO attributes
    enforce_sso = Column(Boolean, default=False)  # Require SSO login

    # Relationships
    projects = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    usage_events = relationship(
        "UsageEvent", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
            "subscription_tier": self.subscription_tier,
            "api_calls_remaining": self.api_calls_limit - self.api_calls_this_month,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UsageEvent(Base):
    """Track usage events for billing"""

    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(
        String(50), nullable=False
    )  # api_call, ai_analysis, mock_server_hour, export
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)
    total_price = Column(Float)
    event_metadata = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    billing_period = Column(String(20))  # YYYY-MM format

    # Relationships
    user = relationship("User", back_populates="usage_events")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "metadata": self.event_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIAnalysis(Base):
    """AI analysis results model"""

    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    analysis_type = Column(String(50))  # security, performance, documentation
    ai_model = Column(String(50))  # claude-3, gpt-4, etc.
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    cost = Column(Float)
    results = Column(JSON)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    project = relationship("Project")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "analysis_type": self.analysis_type,
            "ai_model": self.ai_model,
            "tokens_used": (self.prompt_tokens or 0) + (self.completion_tokens or 0),
            "cost": self.cost,
            "results": self.results,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Database initialization
class APIMonitor(Base):
    """API Monitor model - tracks scheduled API health checks"""

    __tablename__ = "api_monitors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))

    # Monitor details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    url = Column(String(2000), nullable=False)
    method = Column(String(10), default="GET")
    headers = Column(JSON)
    body = Column(Text)

    # Test assertions
    assertions = Column(JSON)  # List of test conditions
    expected_status = Column(Integer, default=200)
    expected_response_time_ms = Column(Integer, default=1000)

    # Schedule
    interval_minutes = Column(Integer, default=60)  # How often to check
    is_active = Column(Boolean, default=True)

    # Status
    last_check_at = Column(DateTime)
    last_status = Column(String(20))  # success, failure, error
    last_response_time_ms = Column(Integer)
    consecutive_failures = Column(Integer, default=0)
    uptime_percentage = Column(Float, default=100.0)

    # Notifications
    notify_on_failure = Column(Boolean, default=True)
    notification_email = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="monitors")
    project = relationship("Project", backref="monitors")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
            "body": self.body,
            "assertions": self.assertions,
            "expected_status": self.expected_status,
            "expected_response_time_ms": self.expected_response_time_ms,
            "interval_minutes": self.interval_minutes,
            "is_active": self.is_active,
            "last_check_at": self.last_check_at.isoformat()
            if self.last_check_at
            else None,
            "last_status": self.last_status,
            "last_response_time_ms": self.last_response_time_ms,
            "consecutive_failures": self.consecutive_failures,
            "uptime_percentage": self.uptime_percentage,
            "notify_on_failure": self.notify_on_failure,
            "notification_email": self.notification_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MonitorResult(Base):
    """Monitor result model - stores individual check results"""

    __tablename__ = "monitor_results"

    id = Column(Integer, primary_key=True, index=True)
    monitor_id = Column(Integer, ForeignKey("api_monitors.id"), nullable=False)

    # Result details
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)

    # Assertion results
    assertions_passed = Column(JSON)  # List of passed/failed assertions

    # Response snapshot
    response_headers = Column(JSON)
    response_body_sample = Column(Text)  # First 1000 chars

    # Timestamp
    checked_at = Column(DateTime, default=func.now())

    # Relationships
    monitor = relationship("APIMonitor", backref="results")

    def to_dict(self):
        return {
            "id": self.id,
            "monitor_id": self.monitor_id,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "success": self.success,
            "error_message": self.error_message,
            "assertions_passed": self.assertions_passed,
            "response_headers": self.response_headers,
            "response_body_sample": self.response_body_sample,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }


class RequestHistory(Base):
    """Request history model - tracks all API requests made through the platform"""

    __tablename__ = "request_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    collection_id = Column(String(36))  # Reference to collection if saved

    # Request details
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, etc.
    url = Column(String(2000), nullable=False)
    headers = Column(JSON)
    query_params = Column(JSON)
    body = Column(Text)
    body_type = Column(String(50))  # json, form-data, raw, etc.

    # Response details
    status_code = Column(Integer)
    response_headers = Column(JSON)
    response_body = Column(Text)
    response_time_ms = Column(Integer)  # Response time in milliseconds
    response_size_bytes = Column(Integer)

    # Metadata
    environment_id = Column(String(36))  # Environment used
    environment_variables = Column(JSON)  # Snapshot of variables used
    name = Column(String(255))  # Optional name for the request
    tags = Column(JSON)  # Tags for organization
    notes = Column(Text)  # User notes

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    executed_at = Column(DateTime, default=func.now())

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Relationships
    user = relationship("User", backref="request_history")
    project = relationship("Project", backref="request_history")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "collection_id": self.collection_id,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "query_params": self.query_params,
            "body": self.body,
            "body_type": self.body_type,
            "status_code": self.status_code,
            "response_headers": self.response_headers,
            "response_body": self.response_body,
            "response_time_ms": self.response_time_ms,
            "response_size_bytes": self.response_size_bytes,
            "environment_id": self.environment_id,
            "environment_variables": self.environment_variables,
            "name": self.name,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "success": self.success,
            "error_message": self.error_message,
        }


class Collection(Base):
    """API Collection model for organizing requests"""

    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    # Note: workspace_id would reference workspaces table which is in models/workspace.py
    # For now, we'll make it a simple Integer field without FK constraint
    workspace_id = Column(Integer, nullable=True)

    # Collection details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    auth_type = Column(String(50))  # bearer, basic, api-key, oauth2
    auth_config = Column(JSON)  # Authentication configuration

    # Collection structure (nested folders and requests)
    structure = Column(JSON)  # Hierarchical structure of folders and requests
    requests = Column(JSON)  # All requests in the collection

    # Pre-request and test scripts
    pre_request_script = Column(Text)
    test_script = Column(Text)

    # Variables
    variables = Column(JSON)  # Collection-level variables

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Import source
    import_source = Column(String(50))  # postman, insomnia, openapi, etc.
    original_format = Column(JSON)  # Original import data

    # Sharing
    is_public = Column(Boolean, default=False)
    share_token = Column(String(100), unique=True, nullable=True)

    # Relationships
    project = relationship("Project", backref="collections")
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_collections"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "auth_type": self.auth_type,
            "auth_config": self.auth_config,
            "structure": self.structure,
            "requests": self.requests,
            "variables": self.variables,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_public": self.is_public,
        }


class Environment(Base):
    """Environment variables for different deployment stages"""

    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    # Note: workspace_id would reference workspaces table which is in models/workspace.py
    # For now, we'll make it a simple Integer field without FK constraint
    workspace_id = Column(Integer, nullable=True)

    # Environment details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(7))  # Hex color for UI

    # Variables
    variables = Column(JSON)  # Key-value pairs
    initial_variables = Column(JSON)  # Initial values (can be reset)
    current_variables = Column(JSON)  # Current runtime values

    # Security
    secrets = Column(JSON)  # Encrypted sensitive variables
    is_default = Column(Boolean, default=False)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime)

    # Usage tracking
    usage_count = Column(Integer, default=0)

    # Relationships
    project = relationship("Project", backref="environments")
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_environments"
    )

    def to_dict(self, include_secrets=False):
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "variables": self.variables,
            "is_default": self.is_default,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat()
            if self.last_used_at
            else None,
            "usage_count": self.usage_count,
        }
        if include_secrets:
            data["secrets"] = self.secrets
        return data


def init_db():
    """Initialize database - create all tables"""
    # Import all models to ensure they're registered with SQLAlchemy
    # This is crucial for proper table creation order and foreign key resolution
    try:
        logger.info("✅ All models imported successfully")
    except ImportError as e:
        logger.warning(f"⚠️  Some models could not be imported: {e}")
        # Continue anyway to create available tables

    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")


def drop_db():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped!")


# CRUD Operations


class DatabaseManager:
    """Manager class for database operations"""

    @staticmethod
    def create_project(
        db: Session,
        name: str,
        description: str = None,
        source_type: str = "directory",
        source_path: str = None,
        user_id: int = None,
    ) -> Project:
        """Create a new project"""
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            source_type=source_type,
            source_path=source_path,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def create_api(
        db: Session, project_id: int, path: str, method: str, **kwargs
    ) -> API:
        """Create a new API endpoint"""
        api = API(project_id=project_id, path=path, method=method, **kwargs)
        db.add(api)
        db.commit()
        db.refresh(api)
        return api

    @staticmethod
    def create_task(db: Session, task_id: str, project_id: int = None) -> Task:
        """Create a new task"""
        task = Task(id=task_id, project_id=project_id, status="pending")
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(db: Session, task_id: str, **kwargs) -> Optional[Task]:
        """Update task status and results"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            for key, value in kwargs.items():
                setattr(task, key, value)
            db.commit()
            db.refresh(task)
        return task

    @staticmethod
    def save_ai_analysis(
        db: Session,
        project_id: int,
        analysis_type: str,
        results: dict,
        ai_model: str = "claude-3",
        cost: float = 0.0,
    ) -> AIAnalysis:
        """Save AI analysis results"""
        analysis = AIAnalysis(
            project_id=project_id,
            analysis_type=analysis_type,
            ai_model=ai_model,
            results=results,
            cost=cost,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional["User"]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional["User"]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(
        db: Session, email: str, password_hash: str, full_name: str = None
    ) -> "User":
        """Create a new user"""
        user = User(
            email=email,
            hashed_password=password_hash,
            full_name=full_name,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional["User"]:
        """Update user fields"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False

    @staticmethod
    def get_user_projects(db: Session, user_id: int) -> List[Project]:
        """Get all projects for a user"""
        return db.query(Project).filter(Project.user_id == user_id).all()

    @staticmethod
    def get_api_by_id(db: Session, api_id: int) -> Optional[API]:
        """Get API by ID"""
        return db.query(API).filter(API.id == api_id).first()

    @staticmethod
    def get_project_apis(db: Session, project_id: int) -> List[API]:
        """Get all APIs for a project"""
        return db.query(API).filter(API.project_id == project_id).all()

    @staticmethod
    def create_usage_event(
        db: Session, user_id: int, event_type: str, metadata: dict = None
    ) -> UsageEvent:
        """Create a usage event for tracking"""
        event = UsageEvent(
            user_id=user_id, event_type=event_type, metadata=metadata or {}
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_user_usage_stats(db: Session, user_id: int, days: int = 30) -> dict:
        """Get usage statistics for a user"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        events = (
            db.query(UsageEvent)
            .filter(UsageEvent.user_id == user_id, UsageEvent.timestamp >= cutoff_date)
            .all()
        )

        stats = {}
        for event in events:
            event_type = event.event_type
            stats[event_type] = stats.get(event_type, 0) + 1

        return {"total_events": len(events), "by_type": stats, "period_days": days}


if __name__ == "__main__":
    # Initialize database when run directly
    print("🗄️  Initializing API Orchestrator Database...")
    init_db()
    print("✅ Database ready!")
    print(f"📍 Database location: {DATABASE_URL}")

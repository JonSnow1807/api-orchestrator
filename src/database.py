"""
Database Models for API Orchestrator
Using SQLAlchemy for ORM with PostgreSQL/SQLite support
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
from datetime import datetime
import os
from typing import Optional
import json

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./api_orchestrator.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

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

# Models

class Project(Base):
    """Project model - groups APIs together"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Add user association
    name = Column(String(255), index=True, nullable=False)  # Remove unique constraint, unique per user
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
    mock_servers = relationship("MockServer", back_populates="project", cascade="all, delete-orphan")
    
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
            "task_count": len(self.tasks)
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
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None
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
            "generated_at": self.generated_at.isoformat() if self.generated_at else None
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
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Task(Base):
    """Orchestration task model"""
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True)  # UUID
    project_id = Column(Integer, ForeignKey("projects.id"))
    status = Column(String(20), default="pending")  # pending, running, completed, failed
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
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "results": {
                "apis_found": self.apis_found,
                "specs_generated": self.specs_generated,
                "tests_created": self.tests_created,
                "security_issues_found": self.security_issues_found
            },
            "business_value": {
                "hours_saved": self.hours_saved,
                "money_saved": self.money_saved,
                "roi_percentage": self.roi_percentage
            }
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
            "url": f"http://{self.host}:{self.port}" if self.status == "running" else None,
            "docker_image": self.docker_image,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_started": self.last_started.isoformat() if self.last_started else None
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
    
    # Subscription
    subscription_tier = Column(String(50), default="free")  # free, starter, growth, enterprise
    subscription_expires = Column(DateTime)
    api_calls_this_month = Column(Integer, default=0)
    api_calls_limit = Column(Integer, default=100)  # Based on tier
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
            "subscription_tier": self.subscription_tier,
            "api_calls_remaining": self.api_calls_limit - self.api_calls_this_month,
            "created_at": self.created_at.isoformat() if self.created_at else None
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
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Database initialization
def init_db():
    """Initialize database - create all tables"""
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
    def create_project(db: Session, name: str, description: str = None, 
                       source_type: str = "directory", source_path: str = None) -> Project:
        """Create a new project"""
        project = Project(
            name=name,
            description=description,
            source_type=source_type,
            source_path=source_path
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
    def create_api(db: Session, project_id: int, path: str, method: str, **kwargs) -> API:
        """Create a new API endpoint"""
        api = API(
            project_id=project_id,
            path=path,
            method=method,
            **kwargs
        )
        db.add(api)
        db.commit()
        db.refresh(api)
        return api
    
    @staticmethod
    def create_task(db: Session, task_id: str, project_id: int = None) -> Task:
        """Create a new task"""
        task = Task(
            id=task_id,
            project_id=project_id,
            status="pending"
        )
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
    def save_ai_analysis(db: Session, project_id: int, analysis_type: str, 
                         results: dict, ai_model: str = "claude-3", cost: float = 0.0) -> AIAnalysis:
        """Save AI analysis results"""
        analysis = AIAnalysis(
            project_id=project_id,
            analysis_type=analysis_type,
            ai_model=ai_model,
            results=results,
            cost=cost
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

if __name__ == "__main__":
    # Initialize database when run directly
    print("🗄️  Initializing API Orchestrator Database...")
    init_db()
    print("✅ Database ready!")
    print(f"📍 Database location: {DATABASE_URL}")

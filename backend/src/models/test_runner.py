"""
Test Runner Models for Test Execution and Results
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class TestResult(Base):
    """Test execution result model"""
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Execution details
    status = Column(String(20))  # passed, failed, error, skipped
    response_time_ms = Column(Float)
    assertions_passed = Column(Integer, default=0)
    assertions_failed = Column(Integer, default=0)
    
    # Request/Response data
    request_url = Column(String(500))
    request_method = Column(String(10))
    request_headers = Column(JSON)
    request_body = Column(Text)
    response_status = Column(Integer)
    response_headers = Column(JSON)
    response_body = Column(Text)
    
    # Assertion results
    assertion_results = Column(JSON)  # Detailed assertion results
    error_message = Column(Text)
    
    # Timing
    executed_at = Column(DateTime, default=func.now())
    duration_ms = Column(Float)
    
    # Relationships
    test = relationship("Test", backref="test_results")
    project = relationship("Project", backref="test_results")
    user = relationship("User", backref="test_results")
    
    def to_dict(self):
        return {
            "id": self.id,
            "test_id": self.test_id,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "assertions_passed": self.assertions_passed,
            "assertions_failed": self.assertions_failed,
            "assertion_results": self.assertion_results,
            "error_message": self.error_message,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None
        }

class TestSuite(Base):
    """Test suite model - collection of tests"""
    __tablename__ = "test_suites"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    test_ids = Column(JSON)  # List of test IDs in order
    environment_id = Column(Integer)  # Will link to environments when created
    setup_script = Column(Text)
    teardown_script = Column(Text)
    parallel_execution = Column(Boolean, default=False)
    stop_on_failure = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", backref="test_suites")
    suite_results = relationship("TestSuiteResult", back_populates="test_suite", cascade="all, delete-orphan")

class TestSuiteResult(Base):
    """Test suite execution result"""
    __tablename__ = "test_suite_results"
    
    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Summary
    total_tests = Column(Integer)
    passed = Column(Integer)
    failed = Column(Integer)
    errors = Column(Integer)
    skipped = Column(Integer)
    pass_rate = Column(Float)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Float)
    
    # Details
    test_results = Column(JSON)  # List of test result IDs
    environment_snapshot = Column(JSON)  # Environment variables used
    
    # Relationships
    test_suite = relationship("TestSuite", back_populates="suite_results")
    user = relationship("User", backref="suite_results")
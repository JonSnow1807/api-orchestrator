"""
AI Keys Models for Custom AI Provider Integration
Supports BYOK (Bring Your Own Key) for various AI providers
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from src.database import Base

class AIKey(Base):
    """Custom AI model keys for workspaces"""
    __tablename__ = "ai_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id', ondelete='CASCADE'))
    provider = Column(String(50), nullable=False)
    key_name = Column(String(100), nullable=False)
    encrypted_key = Column(Text, nullable=False)  # Encrypted API key
    key_hash = Column(String(64), nullable=False, unique=True)  # For duplicate detection
    endpoint_url = Column(String(500))
    deployment_name = Column(String(100))
    model_preferences = Column(JSON)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    usage_limit = Column(Integer)  # Monthly limit
    cost_limit = Column(Float)  # Monthly cost limit
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="ai_keys")
    creator = relationship("User", foreign_keys=[created_by], backref="created_ai_keys")
    usage_records = relationship("AIKeyUsage", back_populates="ai_key", cascade="all, delete-orphan")

class AIKeyUsage(Base):
    """Track usage of AI keys"""
    __tablename__ = "ai_key_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(Integer, ForeignKey('ai_keys.id', ondelete='CASCADE'))
    date = Column(DateTime, nullable=False, index=True)
    model = Column(String(100))
    requests = Column(Integer, default=0)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    errors = Column(Integer, default=0)
    avg_latency_ms = Column(Integer)
    
    # Relationships
    ai_key = relationship("AIKey", back_populates="usage_records")
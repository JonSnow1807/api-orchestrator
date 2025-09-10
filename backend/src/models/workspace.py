"""
Workspace and Team Collaboration Models
Enterprise-ready team collaboration system for API Orchestrator
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import enum
import secrets
from typing import Optional

from src.database import Base
# Forward declaration to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.ai_keys import AIKey

# Association tables for many-to-many relationships
workspace_members = Table(
    'workspace_members',
    Base.metadata,
    Column('workspace_id', Integer, ForeignKey('workspaces.id', ondelete='CASCADE')),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('role', String(50), default='developer'),
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('invited_by', Integer, ForeignKey('users.id')),
    UniqueConstraint('workspace_id', 'user_id', name='unique_workspace_member')
)

# Enum for member roles
class WorkspaceRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"

# Enum for resource types
class ResourceType(enum.Enum):
    PROJECT = "project"
    COLLECTION = "collection"
    API_SPEC = "api_spec"
    MOCK_SERVER = "mock_server"

class Workspace(Base):
    """Workspace/Organization model for team collaboration"""
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True)
    description = Column(Text)
    logo_url = Column(String(500))
    
    # Ownership and metadata
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Settings
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    
    # Subscription and limits
    subscription_tier = Column(String(50), default="free")
    max_members = Column(Integer, default=5)
    max_projects = Column(Integer, default=10)
    max_api_calls = Column(Integer, default=1000)
    
    # Usage tracking
    api_calls_this_month = Column(Integer, default=0)
    storage_used_mb = Column(Integer, default=0)
    
    # Relationships with explicit foreign keys to avoid ambiguity
    creator = relationship("User", 
                          foreign_keys=[created_by], 
                          backref="owned_workspaces",
                          overlaps="members,workspaces")
    members = relationship("User", 
                          secondary=workspace_members, 
                          primaryjoin="Workspace.id == workspace_members.c.workspace_id",
                          secondaryjoin="User.id == workspace_members.c.user_id",
                          backref="workspaces",
                          overlaps="creator,owned_workspaces")
    invitations = relationship("WorkspaceInvitation", back_populates="workspace", cascade="all, delete-orphan")
    # projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")  # Project model doesn't have workspace_id yet
    # collections = relationship("Collection", backref="workspace")  # Collection is in database.py without proper FK
    activity_logs = relationship("WorkspaceActivity", back_populates="workspace", cascade="all, delete-orphan")
    webhooks = relationship("WorkspaceWebhook", back_populates="workspace", cascade="all, delete-orphan")
    ai_keys = relationship("AIKey", back_populates="workspace", cascade="all, delete-orphan")
    
    def get_member_role(self, user_id: int) -> Optional[str]:
        """Get the role of a specific member in this workspace"""
        from sqlalchemy import select
        from src.database import SessionLocal
        
        db = SessionLocal()
        result = db.execute(
            select(workspace_members.c.role).where(
                workspace_members.c.workspace_id == self.id,
                workspace_members.c.user_id == user_id
            )
        ).first()
        db.close()
        
        return result[0] if result else None
    
    def add_member(self, user_id: int, role: str = "developer", invited_by: int = None):
        """Add a member to the workspace"""
        from src.database import SessionLocal
        
        db = SessionLocal()
        db.execute(
            workspace_members.insert().values(
                workspace_id=self.id,
                user_id=user_id,
                role=role,
                invited_by=invited_by,
                joined_at=datetime.utcnow()
            )
        )
        db.commit()
        db.close()

class WorkspaceInvitation(Base):
    """Invitations to join a workspace"""
    __tablename__ = "workspace_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id', ondelete='CASCADE'))
    
    # Invitation details
    email = Column(String(255), nullable=False)
    role = Column(String(50), default='developer')
    token = Column(String(255), unique=True, index=True)
    
    # Metadata
    invited_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    accepted_at = Column(DateTime)
    
    # Status
    is_accepted = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by], backref="sent_invitations")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Generate unique token
        self.token = secrets.token_urlsafe(32)
        # Set expiration to 7 days by default
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=7)
    
    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid"""
        return (
            not self.is_accepted and 
            not self.is_expired and 
            datetime.utcnow() < self.expires_at
        )

class WorkspaceActivity(Base):
    """Activity log for workspace actions"""
    __tablename__ = "workspace_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id', ondelete='CASCADE'))
    
    # Activity details
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)  # created, updated, deleted, shared, etc.
    resource_type = Column(String(50))  # project, collection, api_spec, etc.
    resource_id = Column(Integer)
    resource_name = Column(String(255))
    
    # Additional context
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="activity_logs")
    user = relationship("User", foreign_keys=[user_id], backref="workspace_activities")

class WorkspaceWebhook(Base):
    """Webhooks for workspace events"""
    __tablename__ = "workspace_webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id', ondelete='CASCADE'))
    
    # Webhook configuration
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSON, default=list)  # List of events to trigger on
    headers = Column(JSON, default=dict)  # Custom headers
    
    # Security
    secret = Column(String(255))  # For HMAC signature
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    failure_count = Column(Integer, default=0)
    
    # Metadata
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="webhooks")
    creator = relationship("User", foreign_keys=[created_by], backref="created_webhooks")

class ResourcePermission(Base):
    """Granular permissions for resources within a workspace"""
    __tablename__ = "resource_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id', ondelete='CASCADE'))
    
    # Resource identification
    resource_type = Column(Enum(ResourceType))
    resource_id = Column(Integer, nullable=False)
    
    # Permission target (user or role)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    role = Column(String(50), nullable=True)  # If null, applies to specific user
    
    # Permissions
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    
    # Metadata
    granted_by = Column(Integer, ForeignKey('users.id'))
    granted_at = Column(DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('workspace_id', 'resource_type', 'resource_id', 'user_id', 'role', 
                        name='unique_resource_permission'),
    )

# Update existing models to support workspaces
def update_existing_models():
    """
    This function should be called to update existing models
    to support workspace functionality
    """
    from src.database import Project, User
    
    # Add workspace_id to Project model
    if not hasattr(Project, 'workspace_id'):
        Project.workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=True)
        Project.workspace = relationship("Workspace", back_populates="projects")
        Project.visibility = Column(String(20), default="private")  # private, workspace, public
    
    # Add workspace_id to Collection model (if it exists)
    # Note: Collection model will be added later if needed
    
    # Add collaboration fields to User model
    if not hasattr(User, 'last_active_workspace_id'):
        User.last_active_workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=True)
        User.preferences = Column(JSON, default=dict)
        User.notification_settings = Column(JSON, default=dict)
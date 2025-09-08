"""
Team Collaboration Models for API Orchestrator
SQLAlchemy models for workspaces, team members, roles, permissions, and real-time collaboration
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json
import secrets
import uuid

from src.database import Base, User

# =============================================================================
# WORKSPACE AND TEAM MODELS
# =============================================================================

class Workspace(Base):
    """Workspace/Organization model for team collaboration"""
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    slug = Column(String(100), unique=True, nullable=False)
    
    # Owner and settings
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    max_members = Column(Integer, default=50)
    is_active = Column(Boolean, default=True)
    
    # Billing and subscription
    subscription_tier = Column(String(50), default='free')
    billing_email = Column(String(255))
    
    # Settings JSON structure:
    # {
    #   "default_visibility": "private",
    #   "allow_public_sharing": false,
    #   "require_approval": true,
    #   "enable_real_time": true,
    #   "notifications": {...}
    # }
    settings = Column(JSON, default=lambda: {})
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_workspaces")
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    invitations = relationship("WorkspaceInvitation", back_populates="workspace", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="workspace")
    collections = relationship("Collection", back_populates="workspace", cascade="all, delete-orphan")
    activity_logs = relationship("WorkspaceActivityLog", back_populates="workspace", cascade="all, delete-orphan")
    active_sessions = relationship("ActiveSession", back_populates="workspace", cascade="all, delete-orphan")
    roles = relationship("WorkspaceRole", back_populates="workspace", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_workspaces_owner', 'owner_id'),
        Index('idx_workspaces_slug', 'slug'),
        Index('idx_workspaces_active', 'is_active'),
    )
    
    def to_dict(self, include_stats: bool = False):
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "slug": self.slug,
            "owner_id": self.owner_id,
            "max_members": self.max_members,
            "is_active": self.is_active,
            "subscription_tier": self.subscription_tier,
            "billing_email": self.billing_email,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_stats:
            result["stats"] = {
                "member_count": len([m for m in self.members if m.status == 'active']),
                "project_count": len(self.projects),
                "collection_count": len(self.collections),
                "pending_invitations": len([i for i in self.invitations if i.status == 'pending'])
            }
        
        return result
    
    def get_member_by_user_id(self, user_id: int) -> Optional['WorkspaceMember']:
        """Get workspace member by user ID"""
        return next((m for m in self.members if m.user_id == user_id and m.status == 'active'), None)
    
    def is_member(self, user_id: int) -> bool:
        """Check if user is an active member of this workspace"""
        return self.get_member_by_user_id(user_id) is not None
    
    def get_user_role(self, user_id: int) -> Optional[str]:
        """Get user's role in this workspace"""
        member = self.get_member_by_user_id(user_id)
        return member.role if member else None

class WorkspaceMember(Base):
    """Workspace member model with roles and permissions"""
    __tablename__ = "workspace_members"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Role and permissions
    role = Column(String(20), nullable=False, default='viewer')  # owner, admin, developer, viewer
    permissions = Column(JSON, default=lambda: {})  # Custom permission overrides
    
    # Status
    status = Column(String(20), default='active')  # active, inactive, pending
    
    # Timestamps
    joined_at = Column(DateTime, default=func.now())
    last_active_at = Column(DateTime, default=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspace_memberships")
    
    # Indexes
    __table_args__ = (
        Index('idx_workspace_members_workspace', 'workspace_id'),
        Index('idx_workspace_members_user', 'user_id'),
        Index('idx_workspace_members_role', 'role'),
        Index('idx_workspace_members_status', 'status'),
        Index('idx_workspace_members_active', 'workspace_id', 'status'),
    )
    
    def to_dict(self, include_user: bool = True):
        result = {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "role": self.role,
            "permissions": self.permissions,
            "status": self.status,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None
        }
        
        if include_user and self.user:
            result["user"] = {
                "email": self.user.email,
                "username": self.user.username,
                "full_name": self.user.full_name,
                "last_login": self.user.last_login.isoformat() if self.user.last_login else None
            }
        
        return result
    
    def has_permission(self, resource_type: str, action: str) -> bool:
        """Check if member has specific permission"""
        # Get role-based permissions
        role_permissions = ROLE_PERMISSIONS.get(self.role, {})
        resource_permissions = role_permissions.get(resource_type, {})
        
        # Check custom permission overrides
        custom_permissions = self.permissions.get(resource_type, {})
        
        # Custom permissions override role permissions
        if action in custom_permissions:
            return custom_permissions[action]
        
        return resource_permissions.get(action, False)

class WorkspaceInvitation(Base):
    """Workspace invitation model"""
    __tablename__ = "workspace_invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Invitation details
    email = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='developer')
    message = Column(Text)
    
    # Token and expiration
    invitation_token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Status
    status = Column(String(20), default='pending')  # pending, accepted, expired, revoked
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    accepted_at = Column(DateTime)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_invitations_workspace', 'workspace_id'),
        Index('idx_invitations_email', 'email'),
        Index('idx_invitations_token', 'invitation_token'),
        Index('idx_invitations_status', 'status'),
        Index('idx_invitations_pending', 'workspace_id', 'status'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "invited_by_user_id": self.invited_by_user_id,
            "email": self.email,
            "role": self.role,
            "message": self.message,
            "invitation_token": self.invitation_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "workspace_name": self.workspace.name if self.workspace else None,
            "invited_by": self.invited_by.full_name if self.invited_by else None
        }
    
    def is_valid(self) -> bool:
        """Check if invitation is still valid"""
        return (self.status == 'pending' and 
                self.expires_at > datetime.utcnow())
    
    @staticmethod
    def generate_token() -> str:
        """Generate secure invitation token"""
        return f"inv_{secrets.token_urlsafe(32)}"

class WorkspaceRole(Base):
    """Custom roles and permissions for workspace"""
    __tablename__ = "workspace_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    
    # Role definition
    name = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    color = Column(String(7), default='#6B7280')  # Hex color
    
    # Permissions JSON structure - same as ROLE_PERMISSIONS
    permissions = Column(JSON, nullable=False, default=lambda: {})
    
    # System roles cannot be deleted
    is_system_role = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="roles")
    
    # Indexes
    __table_args__ = (
        Index('idx_roles_workspace', 'workspace_id'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "color": self.color,
            "permissions": self.permissions,
            "is_system_role": self.is_system_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# =============================================================================
# COLLECTION AND RESOURCE MODELS
# =============================================================================

class Collection(Base):
    """Request collection model for shared API collections"""
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Collection details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Organization
    folder_path = Column(String(500), default='/')
    tags = Column(JSON, default=lambda: [])
    
    # Sharing and permissions
    visibility = Column(String(20), default='private')  # private, workspace, public
    shared_with = Column(JSON, default=lambda: [])  # Array of {user_id, permission} objects
    
    # Collection data - structure:
    # [
    #   {
    #     "id": "req_123",
    #     "name": "Get Users",
    #     "method": "GET",
    #     "url": "{{base_url}}/users",
    #     "headers": {...},
    #     "body": {...},
    #     "tests": [...],
    #     "folder": "users"
    #   }
    # ]
    requests = Column(JSON, nullable=False, default=lambda: [])
    
    # Environment variables - structure:
    # [
    #   {
    #     "name": "production",
    #     "variables": {"base_url": "https://api.example.com", "api_key": "..."}
    #   }
    # ]
    environments = Column(JSON, default=lambda: [])
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="collections")
    created_by = relationship("User", back_populates="collections")
    
    # Indexes
    __table_args__ = (
        Index('idx_collections_workspace', 'workspace_id'),
        Index('idx_collections_user', 'created_by_user_id'),
        Index('idx_collections_visibility', 'visibility'),
    )
    
    def to_dict(self, include_requests: bool = True):
        result = {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "created_by_user_id": self.created_by_user_id,
            "name": self.name,
            "description": self.description,
            "folder_path": self.folder_path,
            "tags": self.tags,
            "visibility": self.visibility,
            "shared_with": self.shared_with,
            "environments": self.environments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "request_count": len(self.requests)
        }
        
        if include_requests:
            result["requests"] = self.requests
        
        return result
    
    def can_user_access(self, user_id: int, workspace_member: Optional[WorkspaceMember]) -> bool:
        """Check if user can access this collection"""
        # Owner can always access
        if self.created_by_user_id == user_id:
            return True
        
        # Public collections
        if self.visibility == 'public':
            return True
        
        # Workspace visibility - need to be workspace member
        if self.visibility == 'workspace' and workspace_member:
            return True
        
        # Check specific sharing permissions
        for share in self.shared_with:
            if share.get('user_id') == user_id:
                return True
        
        return False

# =============================================================================
# ACTIVITY AND COLLABORATION MODELS
# =============================================================================

class WorkspaceActivityLog(Base):
    """Activity log for workspace events"""
    __tablename__ = "workspace_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))  # Can be null for system events
    
    # Activity details
    action = Column(String(50), nullable=False)  # member_joined, project_created, etc.
    entity_type = Column(String(50))  # project, collection, member, etc.
    entity_id = Column(String(50))  # ID of affected entity
    
    # Activity data - structure varies by action type
    details = Column(JSON, default=lambda: {})
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_activity_workspace', 'workspace_id'),
        Index('idx_activity_user', 'user_id'),
        Index('idx_activity_action', 'action'),
        Index('idx_activity_created', 'created_at'),
        Index('idx_activity_recent', 'workspace_id', 'created_at'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_name": self.user.full_name if self.user else "System"
        }

class ActiveSession(Base):
    """Active user sessions for real-time collaboration"""
    __tablename__ = "active_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session details
    session_token = Column(String(255), unique=True, nullable=False)
    connection_id = Column(String(255))  # WebSocket connection ID
    
    # Current activity
    current_resource_type = Column(String(50))  # project, collection, api
    current_resource_id = Column(String(50))
    
    # Status
    status = Column(String(20), default='active')  # active, idle, away
    
    # Timestamps
    started_at = Column(DateTime, default=func.now())
    last_activity_at = Column(DateTime, default=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="active_sessions")
    user = relationship("User", back_populates="active_sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_sessions_workspace', 'workspace_id'),
        Index('idx_sessions_user', 'user_id'),
        Index('idx_sessions_token', 'session_token'),
        Index('idx_sessions_activity', 'last_activity_at'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "session_token": self.session_token,
            "connection_id": self.connection_id,
            "current_resource_type": self.current_resource_type,
            "current_resource_id": self.current_resource_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "user_name": self.user.full_name if self.user else None
        }
    
    @staticmethod
    def generate_token() -> str:
        """Generate secure session token"""
        return f"sess_{secrets.token_urlsafe(32)}"

class CollaborationEvent(Base):
    """Real-time collaboration events"""
    __tablename__ = "collaboration_events"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Event details
    event_type = Column(String(50), nullable=False)  # cursor_move, text_change, etc.
    resource_type = Column(String(50), nullable=False)  # project, collection, api
    resource_id = Column(String(50), nullable=False)
    
    # Event data - structure varies by event type
    event_data = Column(JSON, nullable=False, default=lambda: {})
    
    # Timestamp
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    workspace = relationship("Workspace")
    user = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_collab_workspace', 'workspace_id'),
        Index('idx_collab_resource', 'resource_type', 'resource_id'),
        Index('idx_collab_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "event_data": self.event_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_name": self.user.full_name if self.user else None
        }

# =============================================================================
# RESOURCE PERMISSIONS MODEL
# =============================================================================

class ResourcePermission(Base):
    """Granular resource permissions"""
    __tablename__ = "resource_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    
    # Resource identification
    resource_type = Column(String(50), nullable=False)  # project, collection, api
    resource_id = Column(String(50), nullable=False)
    
    # Permission target - either user_id OR role_name
    user_id = Column(Integer, ForeignKey("users.id"))
    role_name = Column(String(50))
    
    # Permissions
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    can_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    granted_by_user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    workspace = relationship("Workspace")
    user = relationship("User", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_permissions_workspace', 'workspace_id'),
        Index('idx_permissions_resource', 'resource_type', 'resource_id'),
        Index('idx_permissions_user', 'user_id'),
        Index('idx_permissions_role', 'role_name'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "role_name": self.role_name,
            "can_read": self.can_read,
            "can_write": self.can_write,
            "can_delete": self.can_delete,
            "can_share": self.can_share,
            "can_admin": self.can_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "granted_by_user_id": self.granted_by_user_id
        }

# =============================================================================
# USAGE STATS MODEL
# =============================================================================

class WorkspaceUsageStats(Base):
    """Workspace usage statistics for analytics"""
    __tablename__ = "workspace_usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    
    # Usage metrics
    total_projects = Column(Integer, default=0)
    total_apis = Column(Integer, default=0)
    total_collections = Column(Integer, default=0)
    total_requests_made = Column(Integer, default=0)
    
    # Member activity
    active_members_count = Column(Integer, default=0)
    total_members_count = Column(Integer, default=0)
    
    # Collaboration metrics
    total_shares = Column(Integer, default=0)
    total_collaboration_sessions = Column(Integer, default=0)
    
    # Billing period
    billing_period = Column(String(7), nullable=False)  # YYYY-MM
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    workspace = relationship("Workspace")
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_workspace', 'workspace_id'),
        Index('idx_usage_period', 'billing_period'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "total_projects": self.total_projects,
            "total_apis": self.total_apis,
            "total_collections": self.total_collections,
            "total_requests_made": self.total_requests_made,
            "active_members_count": self.active_members_count,
            "total_members_count": self.total_members_count,
            "total_shares": self.total_shares,
            "total_collaboration_sessions": self.total_collaboration_sessions,
            "billing_period": self.billing_period,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# =============================================================================
# ROLE-BASED PERMISSIONS DEFINITION
# =============================================================================

ROLE_PERMISSIONS = {
    "owner": {
        "workspace": {
            "read": True, "write": True, "delete": True, "billing": True
        },
        "members": {
            "invite": True, "remove": True, "manage_roles": True
        },
        "projects": {
            "create": True, "read": True, "write": True, "delete": True, "share": True
        },
        "collections": {
            "create": True, "read": True, "write": True, "delete": True, "share": True
        },
        "settings": {
            "manage": True
        }
    },
    "admin": {
        "workspace": {
            "read": True, "write": True, "delete": False, "billing": False
        },
        "members": {
            "invite": True, "remove": False, "manage_roles": True
        },
        "projects": {
            "create": True, "read": True, "write": True, "delete": True, "share": True
        },
        "collections": {
            "create": True, "read": True, "write": True, "delete": True, "share": True
        },
        "settings": {
            "manage": False
        }
    },
    "developer": {
        "workspace": {
            "read": True, "write": False, "delete": False, "billing": False
        },
        "members": {
            "invite": False, "remove": False, "manage_roles": False
        },
        "projects": {
            "create": True, "read": True, "write": True, "delete": False, "share": True
        },
        "collections": {
            "create": True, "read": True, "write": True, "delete": False, "share": True
        },
        "settings": {
            "manage": False
        }
    },
    "viewer": {
        "workspace": {
            "read": True, "write": False, "delete": False, "billing": False
        },
        "members": {
            "invite": False, "remove": False, "manage_roles": False
        },
        "projects": {
            "create": False, "read": True, "write": False, "delete": False, "share": False
        },
        "collections": {
            "create": False, "read": True, "write": False, "delete": False, "share": False
        },
        "settings": {
            "manage": False
        }
    }
}

# =============================================================================
# UPDATE EXISTING MODELS WITH WORKSPACE RELATIONSHIPS
# =============================================================================

# Add these relationships to existing User model in database.py:
"""
# Add to User model:
owned_workspaces = relationship("Workspace", back_populates="owner", cascade="all, delete-orphan")
workspace_memberships = relationship("WorkspaceMember", back_populates="user", cascade="all, delete-orphan")
collections = relationship("Collection", back_populates="created_by", cascade="all, delete-orphan")
activity_logs = relationship("WorkspaceActivityLog", back_populates="user")
active_sessions = relationship("ActiveSession", back_populates="user", cascade="all, delete-orphan")
"""

# Add these fields to existing Project model in database.py:
"""
# Add to Project model:
workspace_id = Column(Integer, ForeignKey("workspaces.id"))
visibility = Column(String(20), default='private')  # private, workspace, public
shared_with = Column(JSON, default=lambda: [])

# Add relationship:
workspace = relationship("Workspace", back_populates="projects")
"""
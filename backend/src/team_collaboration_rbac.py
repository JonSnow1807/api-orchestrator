"""
Role-Based Access Control (RBAC) System for Team Collaboration
Handles permissions, role checking, and access control for workspace resources
"""

from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from functools import wraps
import logging

from src.team_collaboration_models import (
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
    ResourcePermission,
    ROLE_PERMISSIONS,
)
from src.database import User, Project

logger = logging.getLogger(__name__)

# =============================================================================
# PERMISSION CHECKER CLASS
# =============================================================================


class PermissionChecker:
    """Central permission checking service for workspace resources"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_workspace_role(self, user_id: int, workspace_id: int) -> Optional[str]:
        """Get user's role in a workspace"""
        member = (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.status == "active",
            )
            .first()
        )

        return member.role if member else None

    def is_workspace_member(self, user_id: int, workspace_id: int) -> bool:
        """Check if user is an active member of workspace"""
        return self.get_user_workspace_role(user_id, workspace_id) is not None

    def is_workspace_owner(self, user_id: int, workspace_id: int) -> bool:
        """Check if user is the workspace owner"""
        workspace = (
            self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        )

        return workspace and workspace.owner_id == user_id

    def has_workspace_permission(
        self, user_id: int, workspace_id: int, resource_type: str, action: str
    ) -> bool:
        """
        Check if user has specific permission in workspace

        Args:
            user_id: User ID
            workspace_id: Workspace ID
            resource_type: Type of resource (workspace, members, projects, collections, settings)
            action: Action to perform (read, write, delete, etc.)
        """
        # Get user's role in workspace
        role = self.get_user_workspace_role(user_id, workspace_id)
        if not role:
            return False

        # Check role-based permissions
        role_permissions = ROLE_PERMISSIONS.get(role, {})
        resource_permissions = role_permissions.get(resource_type, {})

        # Get member for custom permission overrides
        member = (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.status == "active",
            )
            .first()
        )

        if member and member.permissions:
            # Check custom permission overrides
            custom_permissions = member.permissions.get(resource_type, {})
            if action in custom_permissions:
                return custom_permissions[action]

        return resource_permissions.get(action, False)

    def has_resource_permission(
        self,
        user_id: int,
        workspace_id: int,
        resource_type: str,
        resource_id: str,
        action: str,
    ) -> bool:
        """
        Check if user has permission on specific resource

        Args:
            user_id: User ID
            workspace_id: Workspace ID
            resource_type: Type of resource (project, collection, api)
            resource_id: Specific resource ID
            action: Action (read, write, delete, share, admin)
        """
        # First check if user is workspace member
        if not self.is_workspace_member(user_id, workspace_id):
            return False

        # Check resource-specific permissions
        resource_permission = (
            self.db.query(ResourcePermission)
            .filter(
                ResourcePermission.workspace_id == workspace_id,
                ResourcePermission.resource_type == resource_type,
                ResourcePermission.resource_id == resource_id,
                ResourcePermission.user_id == user_id,
            )
            .first()
        )

        if resource_permission:
            # Check specific permission
            if action == "read":
                return resource_permission.can_read
            elif action == "write":
                return resource_permission.can_write
            elif action == "delete":
                return resource_permission.can_delete
            elif action == "share":
                return resource_permission.can_share
            elif action == "admin":
                return resource_permission.can_admin

        # Fall back to workspace role permissions
        return self.has_workspace_permission(
            user_id, workspace_id, f"{resource_type}s", action
        )

    def can_access_project(self, user_id: int, project_id: int) -> bool:
        """Check if user can access a specific project"""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        # Project owner can always access
        if project.user_id == user_id:
            return True

        # If project has workspace, check workspace permissions
        if project.workspace_id:
            return self.has_resource_permission(
                user_id, project.workspace_id, "project", str(project_id), "read"
            )

        # Check project-specific sharing
        if hasattr(project, "shared_with") and project.shared_with:
            for share in project.shared_with:
                if share.get("user_id") == user_id:
                    return True

        # Public projects
        if hasattr(project, "visibility") and project.visibility == "public":
            return True

        return False

    def get_accessible_workspaces(self, user_id: int) -> List[Workspace]:
        """Get all workspaces user has access to"""
        # Get workspaces where user is a member
        member_workspaces = (
            self.db.query(Workspace)
            .join(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.status == "active",
                Workspace.is_active == True,
            )
            .all()
        )

        # Get workspaces user owns
        owned_workspaces = (
            self.db.query(Workspace)
            .filter(Workspace.owner_id == user_id, Workspace.is_active == True)
            .all()
        )

        # Combine and deduplicate
        workspace_ids = set()
        all_workspaces = []

        for workspace in owned_workspaces + member_workspaces:
            if workspace.id not in workspace_ids:
                workspace_ids.add(workspace.id)
                all_workspaces.append(workspace)

        return all_workspaces

    def get_user_permissions_summary(
        self, user_id: int, workspace_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive permissions summary for user in workspace"""
        role = self.get_user_workspace_role(user_id, workspace_id)
        if not role:
            return {}

        # Get role-based permissions
        base_permissions = ROLE_PERMISSIONS.get(role, {})

        # Get member for custom overrides
        member = (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.status == "active",
            )
            .first()
        )

        # Apply custom permission overrides
        final_permissions = base_permissions.copy()
        if member and member.permissions:
            for resource_type, permissions in member.permissions.items():
                if resource_type in final_permissions:
                    final_permissions[resource_type].update(permissions)
                else:
                    final_permissions[resource_type] = permissions

        return {
            "role": role,
            "permissions": final_permissions,
            "is_owner": self.is_workspace_owner(user_id, workspace_id),
        }


# =============================================================================
# PERMISSION DECORATORS
# =============================================================================


def require_workspace_permission(resource_type: str, action: str):
    """Decorator to check workspace permissions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract parameters - this works with FastAPI dependency injection
            db: Session = None
            current_user: User = None
            workspace_id: int = None

            # Find parameters in kwargs or args
            for key, value in kwargs.items():
                if key == "db" and hasattr(value, "query"):
                    db = value
                elif key == "current_user" and hasattr(value, "id"):
                    current_user = value
                elif key == "workspace_id" and isinstance(value, int):
                    workspace_id = value

            if not db or not current_user or workspace_id is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required parameters for permission check",
                )

            # Check permission
            permission_checker = PermissionChecker(db)
            if not permission_checker.has_workspace_permission(
                current_user.id, workspace_id, resource_type, action
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {resource_type}.{action}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_workspace_membership(func):
    """Decorator to check workspace membership"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        db: Session = None
        current_user: User = None
        workspace_id: int = None

        # Extract parameters
        for key, value in kwargs.items():
            if key == "db" and hasattr(value, "query"):
                db = value
            elif key == "current_user" and hasattr(value, "id"):
                current_user = value
            elif key == "workspace_id" and isinstance(value, int):
                workspace_id = value

        if not db or not current_user or workspace_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Missing required parameters for membership check",
            )

        # Check membership
        permission_checker = PermissionChecker(db)
        if not permission_checker.is_workspace_member(current_user.id, workspace_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this workspace",
            )

        return await func(*args, **kwargs)

    return wrapper


def require_resource_permission(resource_type: str, action: str):
    """Decorator to check resource-specific permissions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db: Session = None
            current_user: User = None
            workspace_id: int = None
            resource_id: Union[str, int] = None

            # Extract parameters
            for key, value in kwargs.items():
                if key == "db" and hasattr(value, "query"):
                    db = value
                elif key == "current_user" and hasattr(value, "id"):
                    current_user = value
                elif key == "workspace_id" and isinstance(value, int):
                    workspace_id = value
                elif key in ["project_id", "collection_id", "api_id", "resource_id"]:
                    resource_id = str(value)

            if (
                not db
                or not current_user
                or workspace_id is None
                or resource_id is None
            ):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required parameters for resource permission check",
                )

            # Check permission
            permission_checker = PermissionChecker(db)
            if not permission_checker.has_resource_permission(
                current_user.id, workspace_id, resource_type, resource_id, action
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions on {resource_type}: {action}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# ROLE MANAGEMENT SERVICE
# =============================================================================


class RoleManager:
    """Service for managing workspace roles and permissions"""

    def __init__(self, db: Session):
        self.db = db

    def create_custom_role(
        self,
        workspace_id: int,
        name: str,
        display_name: str,
        description: str,
        permissions: Dict[str, Any],
        color: str = "#6B7280",
    ) -> WorkspaceRole:
        """Create a custom role for workspace"""
        # Check if role name already exists
        existing = (
            self.db.query(WorkspaceRole)
            .filter(
                WorkspaceRole.workspace_id == workspace_id, WorkspaceRole.name == name
            )
            .first()
        )

        if existing:
            raise ValueError(f"Role '{name}' already exists in this workspace")

        role = WorkspaceRole(
            workspace_id=workspace_id,
            name=name,
            display_name=display_name,
            description=description,
            permissions=permissions,
            color=color,
            is_system_role=False,
        )

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        return role

    def update_role_permissions(
        self, role_id: int, permissions: Dict[str, Any]
    ) -> WorkspaceRole:
        """Update role permissions"""
        role = self.db.query(WorkspaceRole).filter(WorkspaceRole.id == role_id).first()
        if not role:
            raise ValueError("Role not found")

        if role.is_system_role:
            raise ValueError("Cannot modify system roles")

        role.permissions = permissions
        self.db.commit()
        self.db.refresh(role)

        return role

    def delete_role(self, role_id: int) -> bool:
        """Delete a custom role"""
        role = self.db.query(WorkspaceRole).filter(WorkspaceRole.id == role_id).first()
        if not role:
            return False

        if role.is_system_role:
            raise ValueError("Cannot delete system roles")

        # Check if role is in use
        members_with_role = (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == role.workspace_id,
                WorkspaceMember.role == role.name,
            )
            .count()
        )

        if members_with_role > 0:
            raise ValueError("Cannot delete role that is assigned to members")

        self.db.delete(role)
        self.db.commit()

        return True

    def assign_role(
        self, user_id: int, workspace_id: int, role_name: str
    ) -> WorkspaceMember:
        """Assign role to workspace member"""
        member = (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.workspace_id == workspace_id,
            )
            .first()
        )

        if not member:
            raise ValueError("User is not a member of this workspace")

        # Validate role exists
        valid_roles = ["owner", "admin", "developer", "viewer"]
        custom_roles = (
            self.db.query(WorkspaceRole)
            .filter(WorkspaceRole.workspace_id == workspace_id)
            .all()
        )

        valid_roles.extend([role.name for role in custom_roles])

        if role_name not in valid_roles:
            raise ValueError(f"Invalid role: {role_name}")

        member.role = role_name
        self.db.commit()
        self.db.refresh(member)

        return member

    def get_workspace_roles(self, workspace_id: int) -> List[Dict[str, Any]]:
        """Get all available roles for workspace"""
        # System roles
        system_roles = []
        for role_name, permissions in ROLE_PERMISSIONS.items():
            system_roles.append(
                {
                    "name": role_name,
                    "display_name": role_name.title(),
                    "description": f"System {role_name} role",
                    "permissions": permissions,
                    "is_system_role": True,
                    "color": {
                        "owner": "#EF4444",
                        "admin": "#F59E0B",
                        "developer": "#10B981",
                        "viewer": "#6B7280",
                    }.get(role_name, "#6B7280"),
                }
            )

        # Custom roles
        custom_roles = (
            self.db.query(WorkspaceRole)
            .filter(WorkspaceRole.workspace_id == workspace_id)
            .all()
        )

        return system_roles + [role.to_dict() for role in custom_roles]


# =============================================================================
# RESOURCE SHARING SERVICE
# =============================================================================


class SharingManager:
    """Service for managing resource sharing permissions"""

    def __init__(self, db: Session):
        self.db = db

    def share_resource(
        self,
        workspace_id: int,
        resource_type: str,
        resource_id: str,
        target_user_id: int,
        permissions: Dict[str, bool],
        granted_by_user_id: int,
    ) -> ResourcePermission:
        """Share a resource with specific user"""
        # Check if permission already exists
        existing = (
            self.db.query(ResourcePermission)
            .filter(
                ResourcePermission.workspace_id == workspace_id,
                ResourcePermission.resource_type == resource_type,
                ResourcePermission.resource_id == resource_id,
                ResourcePermission.user_id == target_user_id,
            )
            .first()
        )

        if existing:
            # Update existing permissions
            existing.can_read = permissions.get("read", existing.can_read)
            existing.can_write = permissions.get("write", existing.can_write)
            existing.can_delete = permissions.get("delete", existing.can_delete)
            existing.can_share = permissions.get("share", existing.can_share)
            existing.can_admin = permissions.get("admin", existing.can_admin)
            existing.granted_by_user_id = granted_by_user_id

            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Create new permission
        permission = ResourcePermission(
            workspace_id=workspace_id,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=target_user_id,
            can_read=permissions.get("read", True),
            can_write=permissions.get("write", False),
            can_delete=permissions.get("delete", False),
            can_share=permissions.get("share", False),
            can_admin=permissions.get("admin", False),
            granted_by_user_id=granted_by_user_id,
        )

        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)

        return permission

    def revoke_resource_access(
        self,
        workspace_id: int,
        resource_type: str,
        resource_id: str,
        target_user_id: int,
    ) -> bool:
        """Revoke user's access to resource"""
        permission = (
            self.db.query(ResourcePermission)
            .filter(
                ResourcePermission.workspace_id == workspace_id,
                ResourcePermission.resource_type == resource_type,
                ResourcePermission.resource_id == resource_id,
                ResourcePermission.user_id == target_user_id,
            )
            .first()
        )

        if permission:
            self.db.delete(permission)
            self.db.commit()
            return True

        return False

    def get_resource_permissions(
        self, workspace_id: int, resource_type: str, resource_id: str
    ) -> List[ResourcePermission]:
        """Get all permissions for a specific resource"""
        return (
            self.db.query(ResourcePermission)
            .filter(
                ResourcePermission.workspace_id == workspace_id,
                ResourcePermission.resource_type == resource_type,
                ResourcePermission.resource_id == resource_id,
            )
            .all()
        )

    def get_user_shared_resources(
        self, user_id: int, workspace_id: int
    ) -> List[Dict[str, Any]]:
        """Get all resources shared with user"""
        permissions = (
            self.db.query(ResourcePermission)
            .filter(
                ResourcePermission.workspace_id == workspace_id,
                ResourcePermission.user_id == user_id,
            )
            .all()
        )

        resources = []
        for perm in permissions:
            resources.append(
                {
                    "resource_type": perm.resource_type,
                    "resource_id": perm.resource_id,
                    "permissions": {
                        "read": perm.can_read,
                        "write": perm.can_write,
                        "delete": perm.can_delete,
                        "share": perm.can_share,
                        "admin": perm.can_admin,
                    },
                    "granted_at": perm.created_at.isoformat()
                    if perm.created_at
                    else None,
                }
            )

        return resources


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def check_workspace_access(db: Session, user_id: int, workspace_id: int) -> Workspace:
    """Check workspace access and return workspace or raise exception"""
    checker = PermissionChecker(db)

    if not checker.is_workspace_member(user_id, workspace_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Not a member of this workspace",
        )

    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id, Workspace.is_active == True)
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )

    return workspace


def validate_role_permissions(permissions: Dict[str, Any]) -> bool:
    """Validate role permissions structure"""
    required_resources = ["workspace", "members", "projects", "collections", "settings"]

    for resource in required_resources:
        if resource not in permissions:
            return False

        if not isinstance(permissions[resource], dict):
            return False

    return True

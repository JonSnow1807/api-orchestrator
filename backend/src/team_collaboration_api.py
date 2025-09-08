"""
Team Collaboration API Endpoints
Comprehensive REST API for workspace and team management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, validator
import secrets
import re

from src.database import get_db, User
from src.auth import get_current_active_user
from src.team_collaboration_models import (
    Workspace, WorkspaceMember, WorkspaceInvitation, Collection,
    WorkspaceActivityLog, ActiveSession, WorkspaceRole, ResourcePermission,
    WorkspaceUsageStats, ROLE_PERMISSIONS
)
from src.team_collaboration_rbac import (
    PermissionChecker, RoleManager, SharingManager,
    require_workspace_permission, require_workspace_membership,
    require_resource_permission, check_workspace_access
)
from src.email_service import EmailService

# Create router
router = APIRouter(prefix="/api/v1/workspaces", tags=["Team Collaboration"])

# =============================================================================
# PYDANTIC MODELS (REQUEST/RESPONSE)
# =============================================================================

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    max_members: int = 50
    settings: Dict[str, Any] = {}
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Workspace name must be at least 2 characters')
        if len(v) > 255:
            raise ValueError('Workspace name must be less than 255 characters')
        return v.strip()
    
    @validator('slug')
    def validate_slug(cls, v):
        if v:
            # Auto-generate slug if not provided
            slug = re.sub(r'[^a-zA-Z0-9-]', '-', v.lower().strip())
            slug = re.sub(r'-+', '-', slug).strip('-')
            if len(slug) < 2:
                raise ValueError('Slug must be at least 2 characters')
            if len(slug) > 100:
                raise ValueError('Slug must be less than 100 characters')
            return slug
        return v

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_members: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    slug: str
    owner_id: int
    max_members: int
    is_active: bool
    subscription_tier: str
    settings: Dict[str, Any]
    created_at: str
    updated_at: str
    stats: Optional[Dict[str, Any]] = None
    user_role: Optional[str] = None
    user_permissions: Optional[Dict[str, Any]] = None

class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = 'developer'
    message: Optional[str] = None
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['admin', 'developer', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v

class InvitationResponse(BaseModel):
    id: int
    workspace_id: int
    email: str
    role: str
    message: Optional[str]
    status: str
    expires_at: str
    created_at: str
    workspace_name: str
    invited_by: Optional[str]

class MemberUpdate(BaseModel):
    role: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None

class MemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    status: str
    joined_at: str
    last_active_at: str
    user: Dict[str, Any]

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    folder_path: str = '/'
    tags: List[str] = []
    visibility: str = 'private'
    requests: List[Dict[str, Any]] = []
    environments: List[Dict[str, Any]] = []
    
    @validator('visibility')
    def validate_visibility(cls, v):
        if v not in ['private', 'workspace', 'public']:
            raise ValueError('Visibility must be private, workspace, or public')
        return v

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    folder_path: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None
    requests: Optional[List[Dict[str, Any]]] = None
    environments: Optional[List[Dict[str, Any]]] = None

class ShareResourceRequest(BaseModel):
    user_email: str
    permissions: Dict[str, bool]

class RoleCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    color: str = '#6B7280'
    permissions: Dict[str, Any]

# =============================================================================
# WORKSPACE ENDPOINTS
# =============================================================================

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new workspace"""
    # Generate slug if not provided
    if not workspace.slug:
        workspace.slug = re.sub(r'[^a-zA-Z0-9-]', '-', workspace.name.lower().strip())
        workspace.slug = re.sub(r'-+', '-', workspace.slug).strip('-')
    
    # Check if slug is unique
    existing = db.query(Workspace).filter(Workspace.slug == workspace.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workspace slug '{workspace.slug}' already exists"
        )
    
    # Create workspace
    db_workspace = Workspace(
        name=workspace.name,
        description=workspace.description,
        slug=workspace.slug,
        owner_id=current_user.id,
        max_members=workspace.max_members,
        settings=workspace.settings
    )
    
    db.add(db_workspace)
    db.commit()
    db.refresh(db_workspace)
    
    # Add owner as member
    owner_member = WorkspaceMember(
        workspace_id=db_workspace.id,
        user_id=current_user.id,
        role='owner',
        status='active'
    )
    db.add(owner_member)
    
    # Log activity
    activity = WorkspaceActivityLog(
        workspace_id=db_workspace.id,
        user_id=current_user.id,
        action='workspace_created',
        entity_type='workspace',
        entity_id=str(db_workspace.id),
        details={"name": db_workspace.name}
    )
    db.add(activity)
    
    db.commit()
    
    # Return workspace with user role
    response = WorkspaceResponse(**db_workspace.to_dict(include_stats=True))
    response.user_role = 'owner'
    response.user_permissions = ROLE_PERMISSIONS['owner']
    
    return response

@router.get("/", response_model=List[WorkspaceResponse])
async def get_workspaces(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all workspaces user has access to"""
    checker = PermissionChecker(db)
    workspaces = checker.get_accessible_workspaces(current_user.id)
    
    response = []
    for workspace in workspaces:
        workspace_data = WorkspaceResponse(**workspace.to_dict(include_stats=True))
        workspace_data.user_role = checker.get_user_workspace_role(current_user.id, workspace.id)
        workspace_data.user_permissions = checker.get_user_permissions_summary(
            current_user.id, workspace.id
        ).get('permissions', {})
        response.append(workspace_data)
    
    return response

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
@require_workspace_membership
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get workspace details"""
    workspace = check_workspace_access(db, current_user.id, workspace_id)
    
    checker = PermissionChecker(db)
    response = WorkspaceResponse(**workspace.to_dict(include_stats=True))
    response.user_role = checker.get_user_workspace_role(current_user.id, workspace_id)
    response.user_permissions = checker.get_user_permissions_summary(
        current_user.id, workspace_id
    ).get('permissions', {})
    
    return response

@router.put("/{workspace_id}", response_model=WorkspaceResponse)
@require_workspace_permission("workspace", "write")
async def update_workspace(
    workspace_id: int,
    workspace_update: WorkspaceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update workspace"""
    workspace = check_workspace_access(db, current_user.id, workspace_id)
    
    # Update fields
    if workspace_update.name:
        workspace.name = workspace_update.name
    if workspace_update.description is not None:
        workspace.description = workspace_update.description
    if workspace_update.max_members:
        workspace.max_members = workspace_update.max_members
    if workspace_update.settings:
        workspace.settings.update(workspace_update.settings)
    
    db.commit()
    db.refresh(workspace)
    
    # Log activity
    activity = WorkspaceActivityLog(
        workspace_id=workspace_id,
        user_id=current_user.id,
        action='workspace_updated',
        entity_type='workspace',
        entity_id=str(workspace_id),
        details=workspace_update.dict(exclude_none=True)
    )
    db.add(activity)
    db.commit()
    
    checker = PermissionChecker(db)
    response = WorkspaceResponse(**workspace.to_dict(include_stats=True))
    response.user_role = checker.get_user_workspace_role(current_user.id, workspace_id)
    response.user_permissions = checker.get_user_permissions_summary(
        current_user.id, workspace_id
    ).get('permissions', {})
    
    return response

@router.delete("/{workspace_id}")
@require_workspace_permission("workspace", "delete")
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete workspace (only owner can delete)"""
    workspace = check_workspace_access(db, current_user.id, workspace_id)
    
    # Only owner can delete
    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owner can delete workspace"
        )
    
    # Soft delete
    workspace.is_active = False
    db.commit()
    
    return {"message": "Workspace deleted successfully"}

# =============================================================================
# MEMBER MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/{workspace_id}/members", response_model=List[MemberResponse])
@require_workspace_membership
async def get_workspace_members(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all workspace members"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    members = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.status == 'active'
    ).all()
    
    return [MemberResponse(**member.to_dict()) for member in members]

@router.put("/{workspace_id}/members/{user_id}", response_model=MemberResponse)
@require_workspace_permission("members", "manage_roles")
async def update_member(
    workspace_id: int,
    user_id: int,
    member_update: MemberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update workspace member role/permissions"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
        WorkspaceMember.status == 'active'
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Cannot modify owner role
    if member.role == 'owner':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify workspace owner"
        )
    
    # Update member
    if member_update.role:
        member.role = member_update.role
    if member_update.permissions:
        member.permissions = member_update.permissions
    
    db.commit()
    db.refresh(member)
    
    # Log activity
    activity = WorkspaceActivityLog(
        workspace_id=workspace_id,
        user_id=current_user.id,
        action='member_updated',
        entity_type='member',
        entity_id=str(member.id),
        details={"target_user": user_id, "changes": member_update.dict(exclude_none=True)}
    )
    db.add(activity)
    db.commit()
    
    return MemberResponse(**member.to_dict())

@router.delete("/{workspace_id}/members/{user_id}")
@require_workspace_permission("members", "remove")
async def remove_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove member from workspace"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
        WorkspaceMember.status == 'active'
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Cannot remove owner
    if member.role == 'owner':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove workspace owner"
        )
    
    # Remove member (soft delete)
    member.status = 'inactive'
    db.commit()
    
    # Log activity
    activity = WorkspaceActivityLog(
        workspace_id=workspace_id,
        user_id=current_user.id,
        action='member_removed',
        entity_type='member',
        entity_id=str(member.id),
        details={"target_user": user_id}
    )
    db.add(activity)
    db.commit()
    
    return {"message": "Member removed successfully"}

# =============================================================================
# INVITATION ENDPOINTS
# =============================================================================

@router.post("/{workspace_id}/invitations", response_model=InvitationResponse)
@require_workspace_permission("members", "invite")
async def create_invitation(
    workspace_id: int,
    invitation: InvitationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Invite user to workspace"""
    workspace = check_workspace_access(db, current_user.id, workspace_id)
    
    # Check if user is already a member
    existing_member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user.has(User.email == invitation.email),
        WorkspaceMember.status == 'active'
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace"
        )
    
    # Check if there's already a pending invitation
    existing_invitation = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.workspace_id == workspace_id,
        WorkspaceInvitation.email == invitation.email,
        WorkspaceInvitation.status == 'pending'
    ).first()
    
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already a pending invitation for this email"
        )
    
    # Create invitation
    db_invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        invited_by_user_id=current_user.id,
        email=invitation.email,
        role=invitation.role,
        message=invitation.message,
        invitation_token=WorkspaceInvitation.generate_token(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.add(db_invitation)
    db.commit()
    db.refresh(db_invitation)
    
    # Send invitation email
    background_tasks.add_task(
        send_invitation_email,
        invitation.email,
        workspace.name,
        current_user.full_name or current_user.email,
        db_invitation.invitation_token,
        invitation.role
    )
    
    # Log activity
    activity = WorkspaceActivityLog(
        workspace_id=workspace_id,
        user_id=current_user.id,
        action='member_invited',
        entity_type='invitation',
        entity_id=str(db_invitation.id),
        details={"email": invitation.email, "role": invitation.role}
    )
    db.add(activity)
    db.commit()
    
    return InvitationResponse(**db_invitation.to_dict())

@router.get("/{workspace_id}/invitations", response_model=List[InvitationResponse])
@require_workspace_permission("members", "invite")
async def get_invitations(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all workspace invitations"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    invitations = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.workspace_id == workspace_id
    ).order_by(WorkspaceInvitation.created_at.desc()).all()
    
    return [InvitationResponse(**inv.to_dict()) for inv in invitations]

@router.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Accept workspace invitation"""
    invitation = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.invitation_token == token
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    if not invitation.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation is expired or invalid"
        )
    
    # Check email matches
    if invitation.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation email doesn't match your account"
        )
    
    # Check if already a member
    existing_member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == invitation.workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    
    if existing_member and existing_member.status == 'active':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this workspace"
        )
    
    # Add as member
    if existing_member:
        existing_member.status = 'active'
        existing_member.role = invitation.role
    else:
        member = WorkspaceMember(
            workspace_id=invitation.workspace_id,
            user_id=current_user.id,
            role=invitation.role,
            status='active'
        )
        db.add(member)
    
    # Update invitation
    invitation.status = 'accepted'
    invitation.accepted_at = datetime.utcnow()
    
    db.commit()
    
    # Log activity
    activity = WorkspaceActivityLog(
        workspace_id=invitation.workspace_id,
        user_id=current_user.id,
        action='invitation_accepted',
        entity_type='invitation',
        entity_id=str(invitation.id),
        details={"role": invitation.role}
    )
    db.add(activity)
    db.commit()
    
    return {"message": "Invitation accepted successfully"}

@router.delete("/{workspace_id}/invitations/{invitation_id}")
@require_workspace_permission("members", "invite")
async def revoke_invitation(
    workspace_id: int,
    invitation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke workspace invitation"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    invitation = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.id == invitation_id,
        WorkspaceInvitation.workspace_id == workspace_id
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    invitation.status = 'revoked'
    db.commit()
    
    return {"message": "Invitation revoked successfully"}

# =============================================================================
# COLLECTION ENDPOINTS
# =============================================================================

@router.post("/{workspace_id}/collections", response_model=Dict[str, Any])
@require_workspace_permission("collections", "create")
async def create_collection(
    workspace_id: int,
    collection: CollectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new collection"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    db_collection = Collection(
        workspace_id=workspace_id,
        created_by_user_id=current_user.id,
        name=collection.name,
        description=collection.description,
        folder_path=collection.folder_path,
        tags=collection.tags,
        visibility=collection.visibility,
        requests=collection.requests,
        environments=collection.environments
    )
    
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    
    # Log activity
    activity = WorkspaceActivityLog(
        workspace_id=workspace_id,
        user_id=current_user.id,
        action='collection_created',
        entity_type='collection',
        entity_id=str(db_collection.id),
        details={"name": collection.name, "visibility": collection.visibility}
    )
    db.add(activity)
    db.commit()
    
    return db_collection.to_dict()

@router.get("/{workspace_id}/collections", response_model=List[Dict[str, Any]])
@require_workspace_membership
async def get_collections(
    workspace_id: int,
    include_requests: bool = Query(False, description="Include request data"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all accessible collections in workspace"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    # Get workspace member info
    checker = PermissionChecker(db)
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
        WorkspaceMember.status == 'active'
    ).first()
    
    # Get collections
    collections = db.query(Collection).filter(
        Collection.workspace_id == workspace_id
    ).all()
    
    # Filter by access
    accessible_collections = []
    for collection in collections:
        if collection.can_user_access(current_user.id, member):
            accessible_collections.append(collection.to_dict(include_requests=include_requests))
    
    return accessible_collections

# =============================================================================
# ACTIVITY LOG ENDPOINTS
# =============================================================================

@router.get("/{workspace_id}/activity", response_model=List[Dict[str, Any]])
@require_workspace_membership
async def get_activity_log(
    workspace_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get workspace activity log"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    activities = db.query(WorkspaceActivityLog).filter(
        WorkspaceActivityLog.workspace_id == workspace_id
    ).order_by(
        WorkspaceActivityLog.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return [activity.to_dict() for activity in activities]

# =============================================================================
# ROLE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/{workspace_id}/roles")
@require_workspace_membership
async def get_workspace_roles(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all available roles for workspace"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    role_manager = RoleManager(db)
    return role_manager.get_workspace_roles(workspace_id)

@router.post("/{workspace_id}/roles")
@require_workspace_permission("settings", "manage")
async def create_custom_role(
    workspace_id: int,
    role: RoleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create custom role for workspace"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    role_manager = RoleManager(db)
    try:
        db_role = role_manager.create_custom_role(
            workspace_id=workspace_id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            permissions=role.permissions,
            color=role.color
        )
        return db_role.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def send_invitation_email(email: str, workspace_name: str, invited_by: str, 
                               token: str, role: str):
    """Send invitation email (background task)"""
    try:
        email_service = EmailService()
        await email_service.send_workspace_invitation(
            to_email=email,
            workspace_name=workspace_name,
            invited_by=invited_by,
            invitation_token=token,
            role=role
        )
    except Exception as e:
        logger.error(f"Failed to send invitation email: {e}")

# =============================================================================
# SHARING AND PERMISSIONS ENDPOINTS
# =============================================================================

@router.post("/{workspace_id}/share/{resource_type}/{resource_id}")
@require_workspace_permission("projects", "share")  # Adjust based on resource type
async def share_resource(
    workspace_id: int,
    resource_type: str,
    resource_id: str,
    share_request: ShareResourceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Share a resource with another user"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    # Find target user
    target_user = db.query(User).filter(User.email == share_request.user_email).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if target user is workspace member
    checker = PermissionChecker(db)
    if not checker.is_workspace_member(target_user.id, workspace_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a workspace member to share resources"
        )
    
    # Share resource
    sharing_manager = SharingManager(db)
    permission = sharing_manager.share_resource(
        workspace_id=workspace_id,
        resource_type=resource_type,
        resource_id=resource_id,
        target_user_id=target_user.id,
        permissions=share_request.permissions,
        granted_by_user_id=current_user.id
    )
    
    # Log activity
    activity = WorkspaceActivityLog(
        workspace_id=workspace_id,
        user_id=current_user.id,
        action='resource_shared',
        entity_type=resource_type,
        entity_id=resource_id,
        details={
            "target_user": target_user.id,
            "permissions": share_request.permissions
        }
    )
    db.add(activity)
    db.commit()
    
    return permission.to_dict()

@router.get("/{workspace_id}/my-permissions")
@require_workspace_membership
async def get_my_permissions(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's permissions in workspace"""
    check_workspace_access(db, current_user.id, workspace_id)
    
    checker = PermissionChecker(db)
    permissions = checker.get_user_permissions_summary(current_user.id, workspace_id)
    
    sharing_manager = SharingManager(db)
    shared_resources = sharing_manager.get_user_shared_resources(current_user.id, workspace_id)
    
    return {
        "workspace_permissions": permissions,
        "shared_resources": shared_resources
    }
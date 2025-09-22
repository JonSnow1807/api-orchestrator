"""
Workspace and Team Collaboration API Endpoints
Enterprise-ready team management for API Orchestrator
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, select, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
import re

from src.database import get_db, User
from src.auth import get_current_active_user
from src.models.workspace import (
    Workspace,
    WorkspaceInvitation,
    WorkspaceActivity,
    WorkspaceRole,
    workspace_members,
)
from src.email_service import send_invitation_email

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


# Pydantic models for requests/responses
class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    logo_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    member_count: int
    role: str
    subscription_tier: str

    class Config:
        orm_mode = True


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = Field(default="developer", regex="^(admin|developer|viewer)$")
    message: Optional[str] = None


class MemberUpdate(BaseModel):
    role: str = Field(..., regex="^(admin|developer|viewer)$")


class WebhookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: str
    events: List[str]
    headers: Optional[Dict[str, str]] = {}
    secret: Optional[str] = None


# Helper functions
def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from workspace name"""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug[:50]  # Limit length


def check_workspace_permission(
    workspace: Workspace,
    user: User,
    required_role: WorkspaceRole = WorkspaceRole.VIEWER,
    db: Session = None,
) -> bool:
    """Check if user has required permission in workspace"""
    user_role = workspace.get_member_role(user.id)
    if not user_role:
        return False

    role_hierarchy = {
        WorkspaceRole.OWNER.value: 4,
        WorkspaceRole.ADMIN.value: 3,
        WorkspaceRole.DEVELOPER.value: 2,
        WorkspaceRole.VIEWER.value: 1,
    }

    required_level = role_hierarchy.get(required_role.value, 1)
    user_level = role_hierarchy.get(user_role, 0)

    return user_level >= required_level


def log_activity(
    db: Session,
    workspace_id: int,
    user_id: int,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    resource_name: Optional[str] = None,
    details: Optional[Dict] = None,
):
    """Log activity in workspace"""
    activity = WorkspaceActivity(
        workspace_id=workspace_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        details=details,
    )
    db.add(activity)
    db.commit()


# API Endpoints


@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new workspace"""
    # Check user's workspace limit based on subscription
    existing_workspaces = (
        db.query(Workspace).filter(Workspace.created_by == current_user.id).count()
    )

    max_workspaces = 3 if current_user.subscription_tier == "free" else 10
    if existing_workspaces >= max_workspaces:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Workspace limit reached. Upgrade to create more workspaces.",
        )

    # Generate unique slug
    base_slug = generate_slug(workspace_data.name)
    slug = base_slug
    counter = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create workspace
    workspace = Workspace(
        name=workspace_data.name,
        slug=slug,
        description=workspace_data.description,
        logo_url=workspace_data.logo_url,
        created_by=current_user.id,
        subscription_tier=current_user.subscription_tier,
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    # Add creator as owner
    workspace.add_member(current_user.id, WorkspaceRole.OWNER.value)

    # Log activity
    log_activity(
        db,
        workspace.id,
        current_user.id,
        "workspace_created",
        details={"workspace_name": workspace.name},
    )

    return WorkspaceResponse(
        **workspace.__dict__, member_count=1, role=WorkspaceRole.OWNER.value
    )


@router.get("/", response_model=List[WorkspaceResponse])
async def get_my_workspaces(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get all workspaces the user is a member of"""
    # Query workspaces with member count
    workspaces = (
        db.query(Workspace)
        .join(workspace_members, Workspace.id == workspace_members.c.workspace_id)
        .filter(
            workspace_members.c.user_id == current_user.id, Workspace.is_active == True
        )
        .all()
    )

    result = []
    for workspace in workspaces:
        member_count = (
            db.query(func.count(workspace_members.c.user_id))
            .filter(workspace_members.c.workspace_id == workspace.id)
            .scalar()
        )

        role = workspace.get_member_role(current_user.id)

        result.append(
            WorkspaceResponse(
                **workspace.__dict__, member_count=member_count, role=role
            )
        )

    return result


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get workspace details"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission
    if not check_workspace_permission(workspace, current_user, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied")

    member_count = (
        db.query(func.count(workspace_members.c.user_id))
        .filter(workspace_members.c.workspace_id == workspace.id)
        .scalar()
    )

    role = workspace.get_member_role(current_user.id)

    return WorkspaceResponse(**workspace.__dict__, member_count=member_count, role=role)


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    update_data: WorkspaceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update workspace details"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission (only admin or owner)
    if not check_workspace_permission(workspace, current_user, WorkspaceRole.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Update fields
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(workspace, field, value)

    workspace.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(workspace)

    # Log activity
    log_activity(
        db,
        workspace.id,
        current_user.id,
        "workspace_updated",
        details={"updated_fields": list(update_data.dict(exclude_unset=True).keys())},
    )

    member_count = (
        db.query(func.count(workspace_members.c.user_id))
        .filter(workspace_members.c.workspace_id == workspace.id)
        .scalar()
    )

    role = workspace.get_member_role(current_user.id)

    return WorkspaceResponse(**workspace.__dict__, member_count=member_count, role=role)


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a workspace (owner only)"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission (only owner)
    if not check_workspace_permission(workspace, current_user, WorkspaceRole.OWNER):
        raise HTTPException(status_code=403, detail="Owner access required")

    # Soft delete
    workspace.is_active = False
    db.commit()

    return {"message": "Workspace deleted successfully"}


# Member management endpoints


@router.get("/{workspace_id}/members")
async def get_workspace_members(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all members of a workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission
    if not check_workspace_permission(workspace, current_user, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied")

    # Get members with their roles
    members = db.execute(
        select(User, workspace_members.c.role, workspace_members.c.joined_at)
        .join(workspace_members, User.id == workspace_members.c.user_id)
        .where(workspace_members.c.workspace_id == workspace_id)
    ).all()

    return [
        {
            "id": member[0].id,
            "email": member[0].email,
            "username": member[0].username,
            "role": member[1],
            "joined_at": member[2],
        }
        for member in members
    ]


@router.post("/{workspace_id}/invitations")
async def invite_member(
    workspace_id: int,
    invite_data: MemberInvite,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Invite a new member to workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission (admin or owner)
    if not check_workspace_permission(workspace, current_user, WorkspaceRole.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check if user already exists and is a member
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        existing_member = db.execute(
            select(workspace_members.c.user_id).where(
                and_(
                    workspace_members.c.workspace_id == workspace_id,
                    workspace_members.c.user_id == existing_user.id,
                )
            )
        ).first()

        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member")

    # Check for existing pending invitation
    existing_invite = (
        db.query(WorkspaceInvitation)
        .filter(
            and_(
                WorkspaceInvitation.workspace_id == workspace_id,
                WorkspaceInvitation.email == invite_data.email,
                WorkspaceInvitation.is_accepted == False,
                WorkspaceInvitation.expires_at > datetime.utcnow(),
            )
        )
        .first()
    )

    if existing_invite:
        raise HTTPException(status_code=400, detail="Invitation already sent")

    # Create invitation
    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        email=invite_data.email,
        role=invite_data.role,
        invited_by=current_user.id,
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Send invitation email in background
    background_tasks.add_task(
        send_invitation_email,
        invite_data.email,
        workspace.name,
        current_user.username,
        invitation.token,
        invite_data.message,
    )

    # Log activity
    log_activity(
        db,
        workspace_id,
        current_user.id,
        "member_invited",
        details={"email": invite_data.email, "role": invite_data.role},
    )

    return {"message": "Invitation sent successfully", "invitation_id": invitation.id}


@router.post("/{workspace_id}/invitations/{token}/accept")
async def accept_invitation(
    workspace_id: int,
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Accept a workspace invitation"""
    invitation = (
        db.query(WorkspaceInvitation)
        .filter(
            and_(
                WorkspaceInvitation.workspace_id == workspace_id,
                WorkspaceInvitation.token == token,
            )
        )
        .first()
    )

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if not invitation.is_valid:
        raise HTTPException(status_code=400, detail="Invitation is no longer valid")

    if invitation.email != current_user.email:
        raise HTTPException(
            status_code=403, detail="Invitation is for a different email"
        )

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Add user to workspace
    workspace.add_member(current_user.id, invitation.role, invitation.invited_by)

    # Mark invitation as accepted
    invitation.is_accepted = True
    invitation.accepted_at = datetime.utcnow()
    db.commit()

    # Log activity
    log_activity(
        db,
        workspace_id,
        current_user.id,
        "invitation_accepted",
        details={"role": invitation.role},
    )

    return {"message": "Successfully joined workspace", "workspace_id": workspace_id}


@router.put("/{workspace_id}/members/{user_id}")
async def update_member_role(
    workspace_id: int,
    user_id: int,
    update_data: MemberUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a member's role"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission (admin or owner)
    if not check_workspace_permission(workspace, current_user, WorkspaceRole.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Can't change owner's role
    if workspace.created_by == user_id:
        raise HTTPException(status_code=400, detail="Cannot change owner's role")

    # Update role
    db.execute(
        workspace_members.update()
        .where(
            and_(
                workspace_members.c.workspace_id == workspace_id,
                workspace_members.c.user_id == user_id,
            )
        )
        .values(role=update_data.role)
    )
    db.commit()

    # Log activity
    log_activity(
        db,
        workspace_id,
        current_user.id,
        "member_role_updated",
        details={"user_id": user_id, "new_role": update_data.role},
    )

    return {"message": "Role updated successfully"}


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove a member from workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission (admin or owner, or user removing themselves)
    if user_id != current_user.id:
        if not check_workspace_permission(workspace, current_user, WorkspaceRole.ADMIN):
            raise HTTPException(status_code=403, detail="Admin access required")

    # Can't remove owner
    if workspace.created_by == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove workspace owner")

    # Remove member
    db.execute(
        workspace_members.delete().where(
            and_(
                workspace_members.c.workspace_id == workspace_id,
                workspace_members.c.user_id == user_id,
            )
        )
    )
    db.commit()

    # Log activity
    log_activity(
        db,
        workspace_id,
        current_user.id,
        "member_removed",
        details={"user_id": user_id},
    )

    return {"message": "Member removed successfully"}


# Activity and analytics endpoints


@router.get("/{workspace_id}/activity")
async def get_workspace_activity(
    workspace_id: int,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get workspace activity log"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission
    if not check_workspace_permission(workspace, current_user, WorkspaceRole.VIEWER):
        raise HTTPException(status_code=403, detail="Access denied")

    activities = (
        db.query(WorkspaceActivity)
        .filter(WorkspaceActivity.workspace_id == workspace_id)
        .order_by(WorkspaceActivity.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": activity.id,
            "user_id": activity.user_id,
            "action": activity.action,
            "resource_type": activity.resource_type,
            "resource_name": activity.resource_name,
            "details": activity.details,
            "created_at": activity.created_at,
        }
        for activity in activities
    ]


@router.get("/{workspace_id}/analytics")
async def get_workspace_analytics(
    workspace_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get workspace usage analytics"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check permission (admin or owner)
    if not check_workspace_permission(workspace, current_user, WorkspaceRole.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Calculate analytics
    member_count = (
        db.query(func.count(workspace_members.c.user_id))
        .filter(workspace_members.c.workspace_id == workspace_id)
        .scalar()
    )

    # Project count (if Project model exists)
    project_count = 0
    try:
        from src.models.workspace import Project

        project_count = (
            db.query(func.count())
            .select_from(Project)
            .filter(Project.workspace_id == workspace_id)
            .scalar()
        )
    except ImportError:
        pass  # Project model not available

    # Activity stats for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_activities = (
        db.query(
            WorkspaceActivity.action, func.count(WorkspaceActivity.id).label("count")
        )
        .filter(
            and_(
                WorkspaceActivity.workspace_id == workspace_id,
                WorkspaceActivity.created_at >= thirty_days_ago,
            )
        )
        .group_by(WorkspaceActivity.action)
        .all()
    )

    return {
        "workspace_id": workspace_id,
        "member_count": member_count,
        "project_count": project_count,
        "api_calls_this_month": workspace.api_calls_this_month,
        "storage_used_mb": workspace.storage_used_mb,
        "subscription_tier": workspace.subscription_tier,
        "recent_activity": {
            activity.action: activity.count for activity in recent_activities
        },
    }

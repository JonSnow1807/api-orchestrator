"""
Partner Workspace API Routes
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

from ..partner_workspaces import (
    partner_workspace_manager,
    PartnerRole,
    AccessLevel,
    ShareType,
)
from ..auth import get_current_user
from ..models.workspace import Workspace
from ..database import get_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/partner-workspaces", tags=["Partner Workspaces"])


class CreatePartnerWorkspaceRequest(BaseModel):
    name: str
    description: str
    share_type: ShareType
    access_level: AccessLevel = AccessLevel.INVITE_ONLY
    shared_collections: List[str] = []
    shared_apis: List[str] = []
    require_nda: bool = False
    watermark_enabled: bool = True
    expires_in_days: Optional[int] = None
    ip_whitelist: List[str] = []
    allowed_domains: List[str] = []


class InvitePartnerRequest(BaseModel):
    email: EmailStr
    company: str
    role: PartnerRole
    message: Optional[str] = None
    expires_in_days: int = 7


class AcceptInviteRequest(BaseModel):
    token: str


@router.post("/create")
async def create_partner_workspace(
    request: CreatePartnerWorkspaceRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Create a new partner workspace for external collaboration"""

    try:
        # Get user's workspace
        workspace = db.query(Workspace).filter_by(owner_id=current_user["id"]).first()

        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # Check subscription limits
        # TODO: Add subscription checks

        # Create partner workspace
        partner_workspace = await partner_workspace_manager.create_partner_workspace(
            name=request.name,
            description=request.description,
            owner_workspace_id=workspace.id,
            owner_user_id=current_user["id"],
            share_type=request.share_type,
            access_level=request.access_level,
            shared_collections=request.shared_collections,
            shared_apis=request.shared_apis,
            require_nda=request.require_nda,
            watermark_enabled=request.watermark_enabled,
            expires_at=datetime.now() + timedelta(days=request.expires_in_days)
            if request.expires_in_days
            else None,
            ip_whitelist=request.ip_whitelist,
            allowed_domains=request.allowed_domains,
        )

        # Generate share links
        share_links = {
            "public_url": f"https://streamapi.dev/share/{partner_workspace.id}",
            "custom_domain": partner_workspace.custom_domain,
            "embed_script": f'<script src="https://streamapi.dev/embed/{partner_workspace.id}.js"></script>',
        }

        return {
            "success": True,
            "workspace": partner_workspace.dict(),
            "share_links": share_links,
            "message": "Partner workspace created successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workspace_id}/invite")
async def invite_partner(
    workspace_id: str,
    request: InvitePartnerRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Invite a partner to collaborate"""

    try:
        # Verify ownership
        workspace = partner_workspace_manager.workspaces.get(workspace_id)
        if not workspace or workspace.owner_user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create invitation
        invite = await partner_workspace_manager.invite_partner(
            workspace_id=workspace_id,
            email=request.email,
            company=request.company,
            role=request.role,
            message=request.message,
            expires_in_days=request.expires_in_days,
        )

        # Send invitation email (in background)
        background_tasks.add_task(
            send_partner_invitation_email,
            email=request.email,
            company=request.company,
            workspace_name=workspace.name,
            invite_link=f"https://streamapi.dev/partner/accept/{invite.token}",
            message=request.message,
        )

        return {
            "success": True,
            "invite": {
                "id": invite.id,
                "email": invite.email,
                "company": invite.company,
                "role": invite.role.value,
                "expires_at": invite.expires_at.isoformat(),
                "invite_link": f"https://streamapi.dev/partner/accept/{invite.token}",
            },
            "message": f"Invitation sent to {request.email}",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accept-invite")
async def accept_invite(request: AcceptInviteRequest, req: Request) -> Dict[str, Any]:
    """Accept a partner invitation"""

    try:
        # Get IP and user agent
        ip_address = req.client.host
        user_agent = req.headers.get("User-Agent", "Unknown")

        # Accept invitation
        access = await partner_workspace_manager.accept_invite(
            token=request.token, ip_address=ip_address, user_agent=user_agent
        )

        # Get workspace details
        workspace_id = partner_workspace_manager.access_tokens[access.access_token]
        workspace = partner_workspace_manager.workspaces[workspace_id]

        return {
            "success": True,
            "access": {
                "partner_id": access.partner_id,
                "workspace_name": workspace.name,
                "role": access.role.value,
                "permissions": access.permissions,
                "access_token": access.access_token,
                "expires_at": access.expires_at.isoformat()
                if access.expires_at
                else None,
                "workspace_url": f"https://streamapi.dev/partner/workspace/{workspace_id}",
            },
            "message": "Invitation accepted successfully",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workspace_id}")
async def get_partner_workspace(
    workspace_id: str,
    access_token: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get partner workspace details"""

    workspace = partner_workspace_manager.workspaces.get(workspace_id)

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check access
    has_access = False
    is_owner = False
    role = None

    if current_user and workspace.owner_user_id == current_user["id"]:
        has_access = True
        is_owner = True
    elif access_token:
        # Validate partner access
        if access_token in partner_workspace_manager.access_tokens:
            ws_id = partner_workspace_manager.access_tokens[access_token]
            if ws_id == workspace_id:
                has_access = True
                # Find partner role
                for partner in workspace.partners:
                    if partner.access_token == access_token:
                        role = partner.role.value
                        break
    elif workspace.access_level == AccessLevel.PUBLIC:
        has_access = True
        role = "viewer"

    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")

    # Prepare response based on access level
    response = {
        "id": workspace.id,
        "name": workspace.name,
        "description": workspace.description,
        "share_type": workspace.share_type.value,
        "access_level": workspace.access_level.value,
        "is_owner": is_owner,
        "role": role,
        "created_at": workspace.created_at.isoformat(),
    }

    if is_owner:
        # Owner gets full details
        response.update(
            {
                "partners": [
                    {
                        "partner_id": p.partner_id,
                        "email": p.email,
                        "company": p.company,
                        "role": p.role.value,
                        "last_accessed": p.last_accessed.isoformat()
                        if p.last_accessed
                        else None,
                    }
                    for p in workspace.partners
                ],
                "pending_invites": workspace.pending_invites,
                "total_api_calls": workspace.total_api_calls,
                "unique_visitors": workspace.unique_visitors,
                "shared_collections": workspace.shared_collections,
                "shared_apis": workspace.shared_apis,
            }
        )
    else:
        # Partners get limited details
        response.update(
            {
                "shared_collections": workspace.shared_collections,
                "shared_apis": workspace.shared_apis,
                "watermark_enabled": workspace.watermark_enabled,
                "download_disabled": workspace.download_disabled,
            }
        )

    return response


@router.get("/{workspace_id}/activity")
async def get_activity_report(
    workspace_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    partner_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get activity report for partner workspace"""

    try:
        # Verify ownership
        workspace = partner_workspace_manager.workspaces.get(workspace_id)
        if not workspace or workspace.owner_user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Generate report
        report = await partner_workspace_manager.get_activity_report(
            workspace_id=workspace_id,
            start_date=start_date,
            end_date=end_date,
            partner_id=partner_id,
        )

        return {"success": True, "report": report}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workspace_id}/partners/{partner_id}")
async def revoke_partner_access(
    workspace_id: str,
    partner_id: str,
    reason: str = Query(...),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Revoke partner access"""

    try:
        # Verify ownership
        workspace = partner_workspace_manager.workspaces.get(workspace_id)
        if not workspace or workspace.owner_user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Revoke access
        await partner_workspace_manager.revoke_access(
            workspace_id=workspace_id, partner_id=partner_id, reason=reason
        )

        return {"success": True, "message": f"Access revoked for partner {partner_id}"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-workspaces")
async def get_my_partner_workspaces(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all partner workspaces owned by the user"""

    workspaces = [
        {
            "id": ws.id,
            "name": ws.name,
            "description": ws.description,
            "share_type": ws.share_type.value,
            "access_level": ws.access_level.value,
            "partners_count": len(ws.partners),
            "total_api_calls": ws.total_api_calls,
            "created_at": ws.created_at.isoformat(),
            "last_activity": ws.last_activity.isoformat() if ws.last_activity else None,
        }
        for ws in partner_workspace_manager.workspaces.values()
        if ws.owner_user_id == current_user["id"]
    ]

    return {"success": True, "workspaces": workspaces, "total": len(workspaces)}


@router.put("/{workspace_id}/settings")
async def update_partner_workspace_settings(
    workspace_id: str,
    settings: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update partner workspace settings"""

    try:
        # Verify ownership
        workspace = partner_workspace_manager.workspaces.get(workspace_id)
        if not workspace or workspace.owner_user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update settings
        updateable_fields = [
            "name",
            "description",
            "require_nda",
            "watermark_enabled",
            "download_disabled",
            "copy_disabled",
            "ip_whitelist",
            "allowed_domains",
            "max_partners",
            "branding",
            "welcome_message",
        ]

        for field, value in settings.items():
            if field in updateable_fields and hasattr(workspace, field):
                setattr(workspace, field, value)

        workspace.updated_at = datetime.now()

        return {
            "success": True,
            "message": "Settings updated successfully",
            "workspace": workspace.dict(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Background task for sending invitation emails
async def send_partner_invitation_email(
    email: str,
    company: str,
    workspace_name: str,
    invite_link: str,
    message: Optional[str] = None,
):
    """Send partner invitation email"""
    # TODO: Integrate with email service
    print(f"Sending invitation to {email} from {company}")
    print(f"Workspace: {workspace_name}")
    print(f"Invite link: {invite_link}")
    if message:
        print(f"Message: {message}")

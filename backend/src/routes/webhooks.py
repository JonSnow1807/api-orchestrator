"""Webhook Management API Routes"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import hmac
import hashlib
import json
import httpx
import asyncio
from pydantic import BaseModel, HttpUrl, Field

from src.database import get_db, User
from src.auth import get_current_user
from src.models.workspace import WorkspaceWebhook, Workspace, WorkspaceActivity

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# Pydantic models
class WebhookCreate(BaseModel):
    workspace_id: int
    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    events: List[str] = Field(default_factory=list)
    headers: Optional[Dict[str, str]] = None
    secret: Optional[str] = None
    is_active: bool = True


class WebhookUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    secret: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    url: str
    events: List[str]
    headers: Dict[str, str]
    is_active: bool
    last_triggered: Optional[datetime]
    failure_count: int
    created_at: datetime
    updated_at: datetime


class WebhookTestPayload(BaseModel):
    event: str = "test"
    data: Dict[str, Any] = Field(default_factory=dict)


class WebhookDeliveryResponse(BaseModel):
    webhook_id: int
    event: str
    delivered: bool
    status_code: Optional[int]
    response_time_ms: Optional[int]
    error_message: Optional[str]
    timestamp: datetime


# Available webhook events
WEBHOOK_EVENTS = [
    "api.discovered",
    "api.tested",
    "api.version.changed",
    "security.alert",
    "security.vulnerability.found",
    "performance.issue",
    "mock.server.started",
    "mock.server.stopped",
    "ai.analysis.complete",
    "error.threshold.exceeded",
    "workspace.member.added",
    "workspace.member.removed",
    "project.created",
    "project.updated",
    "project.deleted",
    "compliance.check.failed",
    "test.suite.completed",
    "api.documentation.generated",
]


def verify_workspace_access(
    workspace_id: int, user: User, db: Session, required_role: str = "developer"
):
    """Verify user has access to workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Check if user is a member of the workspace
    user_role = workspace.get_member_role(user.id)
    if not user_role:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    # Check role hierarchy
    role_hierarchy = {"owner": 4, "admin": 3, "developer": 2, "viewer": 1}
    if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
        raise HTTPException(
            status_code=403, detail=f"Requires {required_role} role or higher"
        )

    return workspace


def generate_signature(secret: str, payload: bytes) -> str:
    """Generate HMAC signature for webhook payload"""
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


async def deliver_webhook(webhook: WorkspaceWebhook, event: str, data: Dict[str, Any]):
    """Deliver webhook with retry logic"""
    payload = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "workspace_id": webhook.workspace_id,
        "data": data,
    }

    payload_bytes = json.dumps(payload).encode("utf-8")

    headers = webhook.headers or {}
    headers["Content-Type"] = "application/json"
    headers["X-Webhook-Event"] = event
    headers["X-Webhook-ID"] = str(webhook.id)

    # Add signature if secret is configured
    if webhook.secret:
        signature = generate_signature(webhook.secret, payload_bytes)
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    # Retry logic
    max_retries = 3
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                start_time = datetime.utcnow()
                response = await client.post(
                    webhook.url, content=payload_bytes, headers=headers
                )
                duration_ms = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                if response.status_code < 300:
                    # Success
                    webhook.last_triggered = datetime.utcnow()
                    webhook.failure_count = 0
                    return {
                        "delivered": True,
                        "status_code": response.status_code,
                        "response_time_ms": duration_ms,
                    }
                elif attempt < max_retries - 1:
                    # Retry on non-success status codes
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    # Final attempt failed
                    webhook.failure_count += 1
                    if webhook.failure_count >= 10:
                        webhook.is_active = (
                            False  # Disable after 10 consecutive failures
                        )
                    return {
                        "delivered": False,
                        "status_code": response.status_code,
                        "response_time_ms": duration_ms,
                        "error_message": f"HTTP {response.status_code}",
                    }
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
            else:
                webhook.failure_count += 1
                if webhook.failure_count >= 10:
                    webhook.is_active = False
                return {"delivered": False, "error_message": str(e)}


@router.post("", response_model=WebhookResponse)
async def create_webhook(
    webhook_data: WebhookCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new webhook for a workspace"""
    # Verify workspace access (requires admin role)
    workspace = verify_workspace_access(
        webhook_data.workspace_id, current_user, db, "admin"
    )

    # Validate events
    invalid_events = [e for e in webhook_data.events if e not in WEBHOOK_EVENTS]
    if invalid_events:
        raise HTTPException(status_code=400, detail=f"Invalid events: {invalid_events}")

    # Create webhook
    webhook = WorkspaceWebhook(
        workspace_id=webhook_data.workspace_id,
        name=webhook_data.name,
        url=str(webhook_data.url),
        events=webhook_data.events,
        headers=webhook_data.headers or {},
        secret=webhook_data.secret,
        is_active=webhook_data.is_active,
        created_by=current_user.id,
    )

    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    # Log activity
    activity = WorkspaceActivity(
        workspace_id=workspace.id,
        user_id=current_user.id,
        action="webhook.created",
        resource_type="webhook",
        resource_id=webhook.id,
        resource_name=webhook.name,
        details={"url": webhook.url, "events": webhook.events},
    )
    db.add(activity)
    db.commit()

    # Send test webhook if active
    if webhook.is_active:
        background_tasks.add_task(
            deliver_webhook,
            webhook,
            "webhook.created",
            {"webhook_id": webhook.id, "name": webhook.name},
        )

    return webhook


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    workspace_id: int = Query(..., description="Workspace ID"),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all webhooks for a workspace"""
    # Verify workspace access
    verify_workspace_access(workspace_id, current_user, db, "developer")

    query = db.query(WorkspaceWebhook).filter(
        WorkspaceWebhook.workspace_id == workspace_id
    )

    if is_active is not None:
        query = query.filter(WorkspaceWebhook.is_active == is_active)

    webhooks = query.all()
    return webhooks


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific webhook"""
    webhook = (
        db.query(WorkspaceWebhook).filter(WorkspaceWebhook.id == webhook_id).first()
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Verify workspace access
    verify_workspace_access(webhook.workspace_id, current_user, db, "developer")

    return webhook


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_update: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a webhook"""
    webhook = (
        db.query(WorkspaceWebhook).filter(WorkspaceWebhook.id == webhook_id).first()
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Verify workspace access (requires admin role)
    verify_workspace_access(webhook.workspace_id, current_user, db, "admin")

    # Update fields
    update_data = webhook_update.dict(exclude_unset=True)

    if "events" in update_data:
        invalid_events = [e for e in update_data["events"] if e not in WEBHOOK_EVENTS]
        if invalid_events:
            raise HTTPException(
                status_code=400, detail=f"Invalid events: {invalid_events}"
            )

    for field, value in update_data.items():
        if field == "url" and value:
            value = str(value)
        setattr(webhook, field, value)

    webhook.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(webhook)

    # Log activity
    activity = WorkspaceActivity(
        workspace_id=webhook.workspace_id,
        user_id=current_user.id,
        action="webhook.updated",
        resource_type="webhook",
        resource_id=webhook.id,
        resource_name=webhook.name,
        details={"updates": update_data},
    )
    db.add(activity)
    db.commit()

    return webhook


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a webhook"""
    webhook = (
        db.query(WorkspaceWebhook).filter(WorkspaceWebhook.id == webhook_id).first()
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Verify workspace access (requires admin role)
    verify_workspace_access(webhook.workspace_id, current_user, db, "admin")

    # Log activity before deletion
    activity = WorkspaceActivity(
        workspace_id=webhook.workspace_id,
        user_id=current_user.id,
        action="webhook.deleted",
        resource_type="webhook",
        resource_id=webhook.id,
        resource_name=webhook.name,
    )
    db.add(activity)

    db.delete(webhook)
    db.commit()

    return {"message": "Webhook deleted successfully"}


@router.post("/{webhook_id}/test", response_model=WebhookDeliveryResponse)
async def test_webhook(
    webhook_id: int,
    test_payload: WebhookTestPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test a webhook by sending a test payload"""
    webhook = (
        db.query(WorkspaceWebhook).filter(WorkspaceWebhook.id == webhook_id).first()
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Verify workspace access
    verify_workspace_access(webhook.workspace_id, current_user, db, "developer")

    if not webhook.is_active:
        raise HTTPException(status_code=400, detail="Webhook is not active")

    # Deliver webhook immediately (not in background)
    result = await deliver_webhook(
        webhook,
        test_payload.event,
        test_payload.data or {"test": True, "timestamp": datetime.utcnow().isoformat()},
    )

    # Update webhook in database
    db.commit()

    return WebhookDeliveryResponse(
        webhook_id=webhook_id,
        event=test_payload.event,
        delivered=result.get("delivered", False),
        status_code=result.get("status_code"),
        response_time_ms=result.get("response_time_ms"),
        error_message=result.get("error_message"),
        timestamp=datetime.utcnow(),
    )


@router.get("/events/list")
async def list_available_events(current_user: User = Depends(get_current_user)):
    """List all available webhook events"""
    return {
        "events": [
            {
                "name": event,
                "description": event.replace(".", " ").replace("_", " ").title(),
            }
            for event in WEBHOOK_EVENTS
        ]
    }


# Helper function to trigger webhooks from other parts of the application
async def trigger_webhooks(
    db: Session, workspace_id: int, event: str, data: Dict[str, Any]
):
    """Trigger all active webhooks for a workspace and event"""
    webhooks = (
        db.query(WorkspaceWebhook)
        .filter(
            WorkspaceWebhook.workspace_id == workspace_id,
            WorkspaceWebhook.is_active == True,
        )
        .all()
    )

    tasks = []
    for webhook in webhooks:
        if event in webhook.events or "*" in webhook.events:
            tasks.append(deliver_webhook(webhook, event, data))

    if tasks:
        await asyncio.gather(*tasks)

    # Commit any changes made to webhooks (e.g., failure counts)
    db.commit()

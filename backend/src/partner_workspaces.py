"""
Partner Workspaces - External collaboration beyond Postman
Share APIs securely with clients, partners, and vendors
"""

import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
import secrets
from dataclasses import dataclass


class PartnerRole(Enum):
    """Roles for partner workspace members"""

    VIEWER = "viewer"  # Can only view APIs and documentation
    TESTER = "tester"  # Can run tests but not modify
    DEVELOPER = "developer"  # Can modify and test APIs
    ADMIN = "admin"  # Full access including member management


class AccessLevel(Enum):
    """Access control levels"""

    PUBLIC = "public"  # Anyone with link can access
    RESTRICTED = "restricted"  # Requires authentication
    INVITE_ONLY = "invite_only"  # Requires explicit invitation
    IP_RESTRICTED = "ip_restricted"  # IP whitelist based


class ShareType(Enum):
    """Types of sharing"""

    FULL_WORKSPACE = "full_workspace"
    COLLECTION = "collection"
    SINGLE_API = "single_api"
    DOCUMENTATION = "documentation"
    MOCK_SERVER = "mock_server"


@dataclass
class PartnerAccess:
    """Partner access configuration"""

    partner_id: str
    email: str
    company: str
    role: PartnerRole
    access_level: AccessLevel
    permissions: List[str]
    expires_at: Optional[datetime]
    ip_whitelist: Optional[List[str]]
    api_rate_limit: Optional[int]
    created_at: datetime
    last_accessed: Optional[datetime]
    access_token: str


class PartnerWorkspace(BaseModel):
    """Partner workspace model"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    owner_workspace_id: str
    owner_user_id: str
    share_type: ShareType
    access_level: AccessLevel

    # Shared resources
    shared_collections: List[str] = []
    shared_apis: List[str] = []
    shared_environments: List[str] = []
    shared_mock_servers: List[str] = []

    # Partner management
    partners: List[PartnerAccess] = []
    pending_invites: List[Dict[str, Any]] = []

    # Security settings
    require_nda: bool = False
    nda_document_url: Optional[str] = None
    watermark_enabled: bool = True
    download_disabled: bool = False
    copy_disabled: bool = True

    # Access control
    expires_at: Optional[datetime] = None
    max_partners: int = 10
    ip_whitelist: List[str] = []
    allowed_domains: List[str] = []

    # Audit and compliance
    audit_log_enabled: bool = True
    data_retention_days: int = 90
    compliance_tags: List[str] = []  # GDPR, HIPAA, etc.

    # Customization
    branding: Dict[str, Any] = Field(default_factory=dict)
    custom_domain: Optional[str] = None
    welcome_message: Optional[str] = None

    # Analytics
    total_api_calls: int = 0
    unique_visitors: int = 0
    last_activity: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PartnerInvite(BaseModel):
    """Partner invitation model"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    email: EmailStr
    company: str
    role: PartnerRole
    message: Optional[str] = None
    expires_at: datetime
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    accepted: bool = False
    accepted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ActivityLog(BaseModel):
    """Partner activity log"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    partner_id: str
    action: str  # view, test, download, modify, etc.
    resource_type: str  # api, collection, environment, etc.
    resource_id: str
    resource_name: str
    ip_address: str
    user_agent: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)


class PartnerWorkspaceManager:
    """Manage partner workspaces and collaboration"""

    def __init__(self):
        self.workspaces: Dict[str, PartnerWorkspace] = {}
        self.invites: Dict[str, PartnerInvite] = {}
        self.activity_logs: List[ActivityLog] = []
        self.access_tokens: Dict[str, str] = {}  # token -> workspace_id

    async def create_partner_workspace(
        self,
        name: str,
        description: str,
        owner_workspace_id: str,
        owner_user_id: str,
        share_type: ShareType,
        access_level: AccessLevel = AccessLevel.INVITE_ONLY,
        **kwargs,
    ) -> PartnerWorkspace:
        """Create a new partner workspace"""

        workspace = PartnerWorkspace(
            name=name,
            description=description,
            owner_workspace_id=owner_workspace_id,
            owner_user_id=owner_user_id,
            share_type=share_type,
            access_level=access_level,
            **kwargs,
        )

        # Generate unique share link
        workspace.custom_domain = f"share-{workspace.id[:8]}.streamapi.dev"

        self.workspaces[workspace.id] = workspace

        # Log creation
        await self._log_activity(
            workspace_id=workspace.id,
            partner_id=owner_user_id,
            action="create_workspace",
            resource_type="workspace",
            resource_id=workspace.id,
            resource_name=workspace.name,
            ip_address="system",
            user_agent="system",
        )

        return workspace

    async def invite_partner(
        self,
        workspace_id: str,
        email: str,
        company: str,
        role: PartnerRole,
        message: Optional[str] = None,
        expires_in_days: int = 7,
    ) -> PartnerInvite:
        """Invite a partner to collaborate"""

        if workspace_id not in self.workspaces:
            raise ValueError(f"Workspace {workspace_id} not found")

        workspace = self.workspaces[workspace_id]

        # Check limits
        if len(workspace.partners) >= workspace.max_partners:
            raise ValueError(
                f"Maximum partner limit ({workspace.max_partners}) reached"
            )

        # Check domain restrictions
        if workspace.allowed_domains:
            domain = email.split("@")[1]
            if domain not in workspace.allowed_domains:
                raise ValueError(f"Email domain {domain} not allowed")

        # Create invite
        invite = PartnerInvite(
            workspace_id=workspace_id,
            email=email,
            company=company,
            role=role,
            message=message,
            expires_at=datetime.now() + timedelta(days=expires_in_days),
        )

        self.invites[invite.token] = invite
        workspace.pending_invites.append(
            {
                "email": email,
                "company": company,
                "role": role.value,
                "expires_at": invite.expires_at.isoformat(),
                "token": invite.token,
            }
        )

        # Generate invite link
        invite_link = f"https://streamapi.dev/partner/accept/{invite.token}"

        # Log invite
        await self._log_activity(
            workspace_id=workspace_id,
            partner_id="system",
            action="invite_partner",
            resource_type="invite",
            resource_id=invite.id,
            resource_name=email,
            ip_address="system",
            user_agent="system",
            details={"company": company, "role": role.value},
        )

        return invite

    async def accept_invite(
        self, token: str, ip_address: str, user_agent: str
    ) -> PartnerAccess:
        """Accept a partner invitation"""

        if token not in self.invites:
            raise ValueError("Invalid or expired invitation token")

        invite = self.invites[token]

        if invite.accepted:
            raise ValueError("Invitation already accepted")

        if datetime.now() > invite.expires_at:
            raise ValueError("Invitation has expired")

        workspace = self.workspaces[invite.workspace_id]

        # Create partner access
        access = PartnerAccess(
            partner_id=str(uuid.uuid4()),
            email=invite.email,
            company=invite.company,
            role=invite.role,
            access_level=workspace.access_level,
            permissions=self._get_role_permissions(invite.role),
            expires_at=workspace.expires_at,
            ip_whitelist=workspace.ip_whitelist
            if workspace.access_level == AccessLevel.IP_RESTRICTED
            else None,
            api_rate_limit=1000 if invite.role == PartnerRole.VIEWER else 5000,
            created_at=datetime.now(),
            last_accessed=None,
            access_token=secrets.token_urlsafe(32),
        )

        # Add to workspace
        workspace.partners.append(access)
        self.access_tokens[access.access_token] = workspace.id

        # Mark invite as accepted
        invite.accepted = True
        invite.accepted_at = datetime.now()

        # Remove from pending
        workspace.pending_invites = [
            i for i in workspace.pending_invites if i["token"] != token
        ]

        # Log acceptance
        await self._log_activity(
            workspace_id=workspace.id,
            partner_id=access.partner_id,
            action="accept_invite",
            resource_type="invite",
            resource_id=invite.id,
            resource_name=invite.email,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return access

    async def validate_access(
        self,
        access_token: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str,
    ) -> bool:
        """Validate partner access to a resource"""

        if access_token not in self.access_tokens:
            return False

        workspace_id = self.access_tokens[access_token]
        workspace = self.workspaces.get(workspace_id)

        if not workspace:
            return False

        # Find partner
        partner = None
        for p in workspace.partners:
            if p.access_token == access_token:
                partner = p
                break

        if not partner:
            return False

        # Check expiration
        if partner.expires_at and datetime.now() > partner.expires_at:
            return False

        # Check IP whitelist
        if partner.ip_whitelist and ip_address not in partner.ip_whitelist:
            return False

        # Check permissions
        permission_key = f"{resource_type}:{action}"
        if permission_key not in partner.permissions:
            return False

        # Check resource access
        if (
            resource_type == "collection"
            and resource_id not in workspace.shared_collections
        ):
            return False
        elif resource_type == "api" and resource_id not in workspace.shared_apis:
            return False

        # Update last accessed
        partner.last_accessed = datetime.now()

        return True

    async def track_api_usage(
        self,
        workspace_id: str,
        partner_id: str,
        api_id: str,
        method: str,
        endpoint: str,
        response_time_ms: float,
        status_code: int,
        ip_address: str,
        user_agent: str,
    ):
        """Track partner API usage"""

        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return

        # Update counters
        workspace.total_api_calls += 1
        workspace.last_activity = datetime.now()

        # Log activity
        await self._log_activity(
            workspace_id=workspace_id,
            partner_id=partner_id,
            action="api_call",
            resource_type="api",
            resource_id=api_id,
            resource_name=f"{method} {endpoint}",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "method": method,
                "endpoint": endpoint,
                "response_time_ms": response_time_ms,
                "status_code": status_code,
            },
        )

    async def revoke_access(self, workspace_id: str, partner_id: str, reason: str):
        """Revoke partner access"""

        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        # Find and remove partner
        partner_removed = None
        for i, partner in enumerate(workspace.partners):
            if partner.partner_id == partner_id:
                partner_removed = workspace.partners.pop(i)
                break

        if not partner_removed:
            raise ValueError(f"Partner {partner_id} not found")

        # Remove access token
        if partner_removed.access_token in self.access_tokens:
            del self.access_tokens[partner_removed.access_token]

        # Log revocation
        await self._log_activity(
            workspace_id=workspace_id,
            partner_id="system",
            action="revoke_access",
            resource_type="partner",
            resource_id=partner_id,
            resource_name=partner_removed.email,
            ip_address="system",
            user_agent="system",
            details={"reason": reason},
        )

    async def get_activity_report(
        self,
        workspace_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        partner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate activity report for partner workspace"""

        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        # Filter logs
        logs = [log for log in self.activity_logs if log.workspace_id == workspace_id]

        if start_date:
            logs = [log for log in logs if log.timestamp >= start_date]

        if end_date:
            logs = [log for log in logs if log.timestamp <= end_date]

        if partner_id:
            logs = [log for log in logs if log.partner_id == partner_id]

        # Generate report
        report = {
            "workspace_name": workspace.name,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "total_activities": len(logs),
            "unique_partners": len(set(log.partner_id for log in logs)),
            "api_calls": len([log for log in logs if log.action == "api_call"]),
            "downloads": len([log for log in logs if log.action == "download"]),
            "modifications": len(
                [log for log in logs if log.action in ["modify", "create", "delete"]]
            ),
            "by_partner": {},
            "by_resource": {},
            "timeline": [],
        }

        # Group by partner
        for partner in workspace.partners:
            partner_logs = [log for log in logs if log.partner_id == partner.partner_id]
            report["by_partner"][partner.email] = {
                "company": partner.company,
                "role": partner.role.value,
                "total_activities": len(partner_logs),
                "last_activity": max(
                    [log.timestamp for log in partner_logs]
                ).isoformat()
                if partner_logs
                else None,
            }

        # Group by resource
        for log in logs:
            key = f"{log.resource_type}:{log.resource_name}"
            if key not in report["by_resource"]:
                report["by_resource"][key] = 0
            report["by_resource"][key] += 1

        # Timeline
        for log in sorted(logs, key=lambda x: x.timestamp, reverse=True)[:100]:
            report["timeline"].append(
                {
                    "timestamp": log.timestamp.isoformat(),
                    "partner": next(
                        (
                            p.email
                            for p in workspace.partners
                            if p.partner_id == log.partner_id
                        ),
                        "Unknown",
                    ),
                    "action": log.action,
                    "resource": f"{log.resource_type}:{log.resource_name}",
                    "ip_address": log.ip_address,
                }
            )

        return report

    def _get_role_permissions(self, role: PartnerRole) -> List[str]:
        """Get permissions for a role"""
        permissions = {
            PartnerRole.VIEWER: [
                "collection:view",
                "api:view",
                "documentation:view",
                "environment:view",
            ],
            PartnerRole.TESTER: [
                "collection:view",
                "collection:run",
                "api:view",
                "api:test",
                "documentation:view",
                "environment:view",
                "mock_server:use",
            ],
            PartnerRole.DEVELOPER: [
                "collection:view",
                "collection:run",
                "collection:modify",
                "api:view",
                "api:test",
                "api:modify",
                "documentation:view",
                "documentation:modify",
                "environment:view",
                "environment:modify",
                "mock_server:use",
                "mock_server:modify",
            ],
            PartnerRole.ADMIN: [
                "collection:*",
                "api:*",
                "documentation:*",
                "environment:*",
                "mock_server:*",
                "partner:view",
                "partner:invite",
                "partner:revoke",
                "settings:view",
                "settings:modify",
            ],
        }

        return permissions.get(role, [])

    async def _log_activity(
        self,
        workspace_id: str,
        partner_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        resource_name: str,
        ip_address: str,
        user_agent: str,
        details: Dict[str, Any] = None,
    ):
        """Log partner activity"""

        log = ActivityLog(
            workspace_id=workspace_id,
            partner_id=partner_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )

        self.activity_logs.append(log)

        # Cleanup old logs based on retention policy
        workspace = self.workspaces.get(workspace_id)
        if workspace and workspace.data_retention_days:
            cutoff_date = datetime.now() - timedelta(days=workspace.data_retention_days)
            self.activity_logs = [
                log
                for log in self.activity_logs
                if log.timestamp > cutoff_date or log.workspace_id != workspace_id
            ]


# Global manager instance
partner_workspace_manager = PartnerWorkspaceManager()

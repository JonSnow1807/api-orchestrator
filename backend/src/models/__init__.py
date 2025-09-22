"""Models package"""
# Import models in correct order to avoid circular dependencies

# Import core models from database.py
from src.database import (
    User,
    Project,
    API,
    OpenAPISpec,
    Test,
    Task,
    MockServer,
    UsageEvent,
    AIAnalysis,
    APIMonitor,
    MonitorResult,
    RequestHistory,
    Collection,
    Environment,
)

# Import extended models
try:
    from src.models.ai_keys import AIKey, AIKeyUsage
except ImportError:
    AIKey = None
    AIKeyUsage = None

try:
    from src.models.workspace import (
        Workspace,
        WorkspaceInvitation,
        WorkspaceActivity,
        WorkspaceWebhook,
        ResourcePermission,
        WorkspaceRole,
        ResourceType,
    )
except ImportError:
    Workspace = None
    WorkspaceInvitation = None
    WorkspaceActivity = None
    WorkspaceWebhook = None
    ResourcePermission = None
    WorkspaceRole = None
    ResourceType = None

__all__ = [
    # Core models
    "User",
    "Project",
    "API",
    "OpenAPISpec",
    "Test",
    "Task",
    "MockServer",
    "UsageEvent",
    "AIAnalysis",
    "APIMonitor",
    "MonitorResult",
    "RequestHistory",
    "Collection",
    "Environment",
    # Extended models
    "AIKey",
    "AIKeyUsage",
    "Workspace",
    "WorkspaceInvitation",
    "WorkspaceActivity",
    "WorkspaceWebhook",
    "ResourcePermission",
    "WorkspaceRole",
    "ResourceType",
]

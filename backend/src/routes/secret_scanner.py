"""
Secret Scanner API Routes
"""

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Query,
    UploadFile,
    File,
    BackgroundTasks,
)
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..secret_scanner import secret_scanner, SecretType, SecretSeverity, VaultProvider
from ..auth import get_current_user
from ..models.workspace import Workspace
from ..database import get_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/secret-scanner", tags=["Secret Scanner"])


class ScanRequest(BaseModel):
    content: str
    file_path: Optional[str] = "unknown"


class VaultConfigRequest(BaseModel):
    provider: VaultProvider
    connection_string: str
    auth_method: str
    credentials: Dict[str, Any]
    namespace: Optional[str] = None
    mount_point: str = "secret"
    auto_rotate: bool = False
    rotation_interval_days: int = 90


class CustomPatternRequest(BaseModel):
    name: str
    pattern: str
    type: SecretType = SecretType.CUSTOM
    severity: SecretSeverity = SecretSeverity.MEDIUM
    description: str = ""
    entropy_threshold: float = 3.5
    min_length: int = 10


class RemediateRequest(BaseModel):
    secret_id: str
    action: str  # ignore, vault, rotate, remove
    vault_provider: Optional[VaultProvider] = None


@router.post("/scan/content")
async def scan_content(
    request: ScanRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Scan content for exposed secrets"""

    try:
        # Get user's workspace
        workspace = db.query(Workspace).filter_by(owner_id=current_user["id"]).first()

        if not workspace:
            workspace_id = "default"
        else:
            workspace_id = workspace.id

        # Perform scan
        result = await secret_scanner.scan_content(
            content=request.content,
            file_path=request.file_path,
            workspace_id=workspace_id,
        )

        return {
            "success": True,
            "scan_result": result.dict(),
            "summary": {
                "total_secrets": result.total_secrets_found,
                "critical": result.secrets_by_severity.get("critical", 0),
                "high": result.secrets_by_severity.get("high", 0),
                "medium": result.secrets_by_severity.get("medium", 0),
                "low": result.secrets_by_severity.get("low", 0),
            },
            "recommendations": result.recommendations,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/workspace")
async def scan_workspace(
    workspace_path: str,
    file_patterns: Optional[List[str]] = Query(None),
    exclude_patterns: Optional[List[str]] = Query(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Scan entire workspace for secrets"""

    try:
        # Get user's workspace
        workspace = db.query(Workspace).filter_by(owner_id=current_user["id"]).first()

        if not workspace:
            workspace_id = "default"
        else:
            workspace_id = workspace.id

        # Start scan in background
        scan_id = f"scan_{workspace_id}_{datetime.now().timestamp()}"

        background_tasks.add_task(
            secret_scanner.scan_workspace,
            workspace_path=workspace_path,
            workspace_id=workspace_id,
            file_patterns=file_patterns,
            exclude_patterns=exclude_patterns,
        )

        return {
            "success": True,
            "scan_id": scan_id,
            "message": "Workspace scan started in background",
            "status_url": f"/api/secret-scanner/scan/{scan_id}/status",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/file")
async def scan_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Scan uploaded file for secrets"""

    try:
        # Get user's workspace
        workspace = db.query(Workspace).filter_by(owner_id=current_user["id"]).first()

        if not workspace:
            workspace_id = "default"
        else:
            workspace_id = workspace.id

        # Read file content
        content = await file.read()
        content_str = content.decode("utf-8", errors="ignore")

        # Perform scan
        result = await secret_scanner.scan_content(
            content=content_str, file_path=file.filename, workspace_id=workspace_id
        )

        return {
            "success": True,
            "filename": file.filename,
            "scan_result": result.dict(),
            "summary": {
                "total_secrets": result.total_secrets_found,
                "by_severity": result.secrets_by_severity,
                "by_type": result.secrets_by_type,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan/history")
async def get_scan_history(
    limit: int = Query(10, le=100),
    workspace_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get scan history"""

    history = secret_scanner.scan_history

    if workspace_id:
        history = [s for s in history if s.workspace_id == workspace_id]

    # Sort by date and limit
    history = sorted(history, key=lambda x: x.started_at, reverse=True)[:limit]

    return {
        "success": True,
        "history": [h.dict() for h in history],
        "total": len(history),
    }


@router.post("/vault/configure")
async def configure_vault(
    request: VaultConfigRequest, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Configure vault integration"""

    try:
        config = await secret_scanner.configure_vault(
            provider=request.provider,
            connection_string=request.connection_string,
            auth_method=request.auth_method,
            credentials=request.credentials,
            namespace=request.namespace,
            mount_point=request.mount_point,
            auto_rotate=request.auto_rotate,
            rotation_interval_days=request.rotation_interval_days,
        )

        return {
            "success": True,
            "message": f"Vault {request.provider.value} configured successfully",
            "config": {
                "provider": config.provider.value,
                "auth_method": config.auth_method,
                "auto_rotate": config.auto_rotate,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vault/store")
async def store_secret(
    secret_name: str,
    secret_value: str,
    provider: VaultProvider,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Store secret in vault"""

    try:
        result = await secret_scanner.store_secret_in_vault(
            secret_name=secret_name,
            secret_value=secret_value,
            provider=provider,
            metadata=metadata,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vault/retrieve/{secret_name}")
async def retrieve_secret(
    secret_name: str,
    provider: VaultProvider,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve secret from vault"""

    try:
        secret_value = await secret_scanner.retrieve_secret_from_vault(
            secret_name=secret_name, provider=provider
        )

        if secret_value:
            return {
                "success": True,
                "secret_name": secret_name,
                "masked_value": secret_scanner._mask_secret(secret_value),
            }
        else:
            return {"success": False, "message": "Secret not found"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/custom")
async def add_custom_pattern(
    request: CustomPatternRequest, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Add custom secret detection pattern"""

    try:
        await secret_scanner.add_custom_pattern(
            name=request.name,
            pattern=request.pattern,
            type=request.type,
            severity=request.severity,
            description=request.description,
            entropy_threshold=request.entropy_threshold,
        )

        return {
            "success": True,
            "message": f"Custom pattern '{request.name}' added successfully",
            "total_patterns": len(secret_scanner.patterns)
            + len(secret_scanner.custom_patterns),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def get_patterns(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all secret detection patterns"""

    all_patterns = []

    for pattern in secret_scanner.patterns:
        all_patterns.append(
            {
                "name": pattern.name,
                "type": pattern.type.value,
                "severity": pattern.severity.value,
                "description": pattern.description,
                "custom": False,
            }
        )

    for pattern in secret_scanner.custom_patterns:
        all_patterns.append(
            {
                "name": pattern.name,
                "type": pattern.type.value,
                "severity": pattern.severity.value,
                "description": pattern.description,
                "custom": True,
            }
        )

    return {
        "success": True,
        "patterns": all_patterns,
        "total": len(all_patterns),
        "default_patterns": len(secret_scanner.patterns),
        "custom_patterns": len(secret_scanner.custom_patterns),
    }


@router.post("/remediate")
async def remediate_secret(
    request: RemediateRequest, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Remediate detected secret"""

    # Find the secret in scan history
    detected_secret = None
    for scan in secret_scanner.scan_history:
        for secret in scan.detected_secrets:
            if secret.id == request.secret_id:
                detected_secret = secret
                break
        if detected_secret:
            break

    if not detected_secret:
        raise HTTPException(status_code=404, detail="Secret not found")

    try:
        result = await secret_scanner.remediate_secret(
            detected_secret=detected_secret,
            action=request.action,
            vault_provider=request.vault_provider,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_scanner_stats(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get secret scanner statistics"""

    total_scans = len(secret_scanner.scan_history)
    total_secrets = sum(s.total_secrets_found for s in secret_scanner.scan_history)

    severity_stats = {}
    type_stats = {}

    for scan in secret_scanner.scan_history:
        for sev, count in scan.secrets_by_severity.items():
            severity_stats[sev] = severity_stats.get(sev, 0) + count

        for typ, count in scan.secrets_by_type.items():
            type_stats[typ] = type_stats.get(typ, 0) + count

    return {
        "success": True,
        "stats": {
            "total_scans": total_scans,
            "total_secrets_detected": total_secrets,
            "by_severity": severity_stats,
            "by_type": type_stats,
            "vault_providers_configured": len(secret_scanner.vault_configs),
            "custom_patterns": len(secret_scanner.custom_patterns),
            "whitelisted_secrets": len(secret_scanner.whitelist),
        },
    }

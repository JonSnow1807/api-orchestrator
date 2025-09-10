"""Custom AI Model Keys (BYOK) Management API"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field
import hashlib
import json
from cryptography.fernet import Fernet
import base64
import os

from src.database import get_db, User, Base
from src.auth import get_current_user
from src.models.workspace import Workspace, WorkspaceActivity

router = APIRouter(prefix="/api/ai-keys", tags=["ai-keys"])

# Get or generate encryption key
ENCRYPTION_KEY = os.getenv('AI_KEY_ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # Generate a new key if not provided (should be set in production)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"Warning: Generated new encryption key. Set AI_KEY_ENCRYPTION_KEY env var in production.")

cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

# Supported AI providers
AI_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "text-embedding-ada-002"],
        "key_format": "sk-...",
        "docs_url": "https://platform.openai.com/api-keys"
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2.1"],
        "key_format": "sk-ant-...",
        "docs_url": "https://console.anthropic.com/settings/keys"
    },
    "google": {
        "name": "Google Gemini",
        "models": ["gemini-pro", "gemini-pro-vision", "gemini-ultra"],
        "key_format": "AIza...",
        "docs_url": "https://makersuite.google.com/app/apikey"
    },
    "cohere": {
        "name": "Cohere",
        "models": ["command", "command-nightly", "command-light", "embed-english-v3.0"],
        "key_format": "...",
        "docs_url": "https://dashboard.cohere.ai/api-keys"
    },
    "huggingface": {
        "name": "Hugging Face",
        "models": ["meta-llama/Llama-2-70b", "mistralai/Mistral-7B", "custom"],
        "key_format": "hf_...",
        "docs_url": "https://huggingface.co/settings/tokens"
    },
    "azure": {
        "name": "Azure OpenAI",
        "models": ["gpt-4", "gpt-35-turbo", "text-embedding-ada-002"],
        "key_format": "endpoint|key|deployment",
        "docs_url": "https://portal.azure.com/#blade/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/OpenAI"
    },
    "replicate": {
        "name": "Replicate",
        "models": ["meta/llama-2-70b-chat", "stability-ai/sdxl", "custom"],
        "key_format": "r8_...",
        "docs_url": "https://replicate.com/account/api-tokens"
    },
    "custom": {
        "name": "Custom/Self-Hosted",
        "models": ["custom"],
        "key_format": "custom",
        "docs_url": ""
    }
}

class AIKeyCreate(BaseModel):
    """Create a new AI key"""
    workspace_id: int
    provider: str = Field(..., description="AI provider (openai, anthropic, etc.)")
    key_name: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=1)
    endpoint_url: Optional[str] = None  # For custom/Azure endpoints
    deployment_name: Optional[str] = None  # For Azure deployments
    model_preferences: Optional[Dict[str, str]] = None  # Model selection preferences
    is_default: bool = False
    usage_limit: Optional[int] = None  # Monthly usage limit in requests
    cost_limit: Optional[float] = None  # Monthly cost limit in USD

class AIKeyUpdate(BaseModel):
    """Update an AI key"""
    key_name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = Field(None, min_length=1)
    endpoint_url: Optional[str] = None
    deployment_name: Optional[str] = None
    model_preferences: Optional[Dict[str, str]] = None
    is_default: Optional[bool] = None
    usage_limit: Optional[int] = None
    cost_limit: Optional[float] = None
    is_active: Optional[bool] = None

class AIKeyResponse(BaseModel):
    """AI key response"""
    id: int
    workspace_id: int
    provider: str
    provider_name: str
    key_name: str
    key_preview: str  # Last 4 characters only
    endpoint_url: Optional[str]
    deployment_name: Optional[str]
    model_preferences: Optional[Dict[str, str]]
    is_default: bool
    is_active: bool
    usage_limit: Optional[int]
    cost_limit: Optional[float]
    usage_this_month: int
    cost_this_month: float
    last_used: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class AIKeyUsageResponse(BaseModel):
    """AI key usage statistics"""
    key_id: int
    key_name: str
    provider: str
    total_requests: int
    total_tokens: int
    total_cost: float
    requests_this_month: int
    tokens_this_month: int
    cost_this_month: float
    daily_usage: List[Dict]  # Last 30 days
    model_breakdown: Dict[str, int]  # Requests per model

# Import models from the separate module
from src.models.ai_keys import AIKey, AIKeyUsage

def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key"""
    return cipher_suite.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    return cipher_suite.decrypt(encrypted_key.encode()).decode()

def hash_api_key(api_key: str) -> str:
    """Create a hash of the API key for duplicate detection"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def preview_api_key(api_key: str) -> str:
    """Create a preview of the API key (last 4 characters)"""
    if len(api_key) <= 8:
        return "****"
    return "*" * (len(api_key) - 4) + api_key[-4:]

def verify_workspace_access(workspace_id: int, user: User, db: Session, required_role: str = "admin"):
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
        raise HTTPException(status_code=403, detail=f"Requires {required_role} role or higher")
    
    return workspace

@router.post("", response_model=AIKeyResponse)
async def create_ai_key(
    key_data: AIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new AI key for a workspace"""
    # Verify workspace access (requires admin role)
    workspace = verify_workspace_access(key_data.workspace_id, current_user, db, "admin")
    
    # Validate provider
    if key_data.provider not in AI_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {key_data.provider}")
    
    # Check for duplicate key
    key_hash = hash_api_key(key_data.api_key)
    existing = db.query(AIKey).filter(
        AIKey.key_hash == key_hash,
        AIKey.workspace_id == key_data.workspace_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This API key already exists in the workspace")
    
    # If setting as default, unset other defaults
    if key_data.is_default:
        db.query(AIKey).filter(
            AIKey.workspace_id == key_data.workspace_id,
            AIKey.provider == key_data.provider
        ).update({"is_default": False})
    
    # Create the key
    ai_key = AIKey(
        workspace_id=key_data.workspace_id,
        provider=key_data.provider,
        key_name=key_data.key_name,
        encrypted_key=encrypt_api_key(key_data.api_key),
        key_hash=key_hash,
        endpoint_url=key_data.endpoint_url,
        deployment_name=key_data.deployment_name,
        model_preferences=key_data.model_preferences,
        is_default=key_data.is_default,
        usage_limit=key_data.usage_limit,
        cost_limit=key_data.cost_limit,
        created_by=current_user.id
    )
    
    db.add(ai_key)
    db.commit()
    db.refresh(ai_key)
    
    # Log activity
    activity = WorkspaceActivity(
        workspace_id=workspace.id,
        user_id=current_user.id,
        action="ai_key.created",
        resource_type="ai_key",
        resource_id=ai_key.id,
        resource_name=ai_key.key_name,
        details={"provider": ai_key.provider}
    )
    db.add(activity)
    db.commit()
    
    # Get usage stats
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage = db.query(
        AIKeyUsage
    ).filter(
        AIKeyUsage.key_id == ai_key.id,
        AIKeyUsage.date >= current_month
    ).all()
    
    requests_this_month = sum(u.requests for u in usage)
    cost_this_month = sum(u.cost for u in usage)
    
    return AIKeyResponse(
        id=ai_key.id,
        workspace_id=ai_key.workspace_id,
        provider=ai_key.provider,
        provider_name=AI_PROVIDERS[ai_key.provider]["name"],
        key_name=ai_key.key_name,
        key_preview=preview_api_key(key_data.api_key),
        endpoint_url=ai_key.endpoint_url,
        deployment_name=ai_key.deployment_name,
        model_preferences=ai_key.model_preferences,
        is_default=ai_key.is_default,
        is_active=ai_key.is_active,
        usage_limit=ai_key.usage_limit,
        cost_limit=ai_key.cost_limit,
        usage_this_month=requests_this_month,
        cost_this_month=cost_this_month,
        last_used=ai_key.last_used,
        created_at=ai_key.created_at,
        updated_at=ai_key.updated_at
    )

@router.get("", response_model=List[AIKeyResponse])
async def list_ai_keys(
    workspace_id: int,
    provider: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all AI keys for a workspace"""
    # Verify workspace access
    workspace = verify_workspace_access(workspace_id, current_user, db, "developer")
    
    query = db.query(AIKey).filter(AIKey.workspace_id == workspace_id)
    
    if provider:
        query = query.filter(AIKey.provider == provider)
    if is_active is not None:
        query = query.filter(AIKey.is_active == is_active)
    
    keys = query.all()
    
    # Get usage stats for all keys
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    results = []
    for key in keys:
        # Decrypt the key to get preview (but don't return full key)
        try:
            decrypted_key = decrypt_api_key(key.encrypted_key)
            preview = preview_api_key(decrypted_key)
        except:
            preview = "****"
        
        # Get usage stats
        usage = db.query(AIKeyUsage).filter(
            AIKeyUsage.key_id == key.id,
            AIKeyUsage.date >= current_month
        ).all()
        
        requests_this_month = sum(u.requests for u in usage)
        cost_this_month = sum(u.cost for u in usage)
        
        results.append(AIKeyResponse(
            id=key.id,
            workspace_id=key.workspace_id,
            provider=key.provider,
            provider_name=AI_PROVIDERS[key.provider]["name"],
            key_name=key.key_name,
            key_preview=preview,
            endpoint_url=key.endpoint_url,
            deployment_name=key.deployment_name,
            model_preferences=key.model_preferences,
            is_default=key.is_default,
            is_active=key.is_active,
            usage_limit=key.usage_limit,
            cost_limit=key.cost_limit,
            usage_this_month=requests_this_month,
            cost_this_month=cost_this_month,
            last_used=key.last_used,
            created_at=key.created_at,
            updated_at=key.updated_at
        ))
    
    return results

@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_user)
):
    """List all supported AI providers"""
    return AI_PROVIDERS

@router.get("/{key_id}", response_model=AIKeyResponse)
async def get_ai_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific AI key (without exposing the actual key)"""
    key = db.query(AIKey).filter(AIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="AI key not found")
    
    # Verify workspace access
    verify_workspace_access(key.workspace_id, current_user, db, "developer")
    
    # Get preview
    try:
        decrypted_key = decrypt_api_key(key.encrypted_key)
        preview = preview_api_key(decrypted_key)
    except:
        preview = "****"
    
    # Get usage stats
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage = db.query(AIKeyUsage).filter(
        AIKeyUsage.key_id == key.id,
        AIKeyUsage.date >= current_month
    ).all()
    
    requests_this_month = sum(u.requests for u in usage)
    cost_this_month = sum(u.cost for u in usage)
    
    return AIKeyResponse(
        id=key.id,
        workspace_id=key.workspace_id,
        provider=key.provider,
        provider_name=AI_PROVIDERS[key.provider]["name"],
        key_name=key.key_name,
        key_preview=preview,
        endpoint_url=key.endpoint_url,
        deployment_name=key.deployment_name,
        model_preferences=key.model_preferences,
        is_default=key.is_default,
        is_active=key.is_active,
        usage_limit=key.usage_limit,
        cost_limit=key.cost_limit,
        usage_this_month=requests_this_month,
        cost_this_month=cost_this_month,
        last_used=key.last_used,
        created_at=key.created_at,
        updated_at=key.updated_at
    )

@router.patch("/{key_id}", response_model=AIKeyResponse)
async def update_ai_key(
    key_id: int,
    key_update: AIKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an AI key"""
    key = db.query(AIKey).filter(AIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="AI key not found")
    
    # Verify workspace access (requires admin role)
    verify_workspace_access(key.workspace_id, current_user, db, "admin")
    
    # Update fields
    update_data = key_update.dict(exclude_unset=True)
    
    # Handle API key update specially
    if "api_key" in update_data:
        new_api_key = update_data.pop("api_key")
        key.encrypted_key = encrypt_api_key(new_api_key)
        key.key_hash = hash_api_key(new_api_key)
    
    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(AIKey).filter(
            AIKey.workspace_id == key.workspace_id,
            AIKey.provider == key.provider,
            AIKey.id != key_id
        ).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(key, field, value)
    
    key.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(key)
    
    # Log activity
    activity = WorkspaceActivity(
        workspace_id=key.workspace_id,
        user_id=current_user.id,
        action="ai_key.updated",
        resource_type="ai_key",
        resource_id=key.id,
        resource_name=key.key_name,
        details={"updates": list(update_data.keys())}
    )
    db.add(activity)
    db.commit()
    
    # Return response
    return await get_ai_key(key_id, db, current_user)

@router.delete("/{key_id}")
async def delete_ai_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an AI key"""
    key = db.query(AIKey).filter(AIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="AI key not found")
    
    # Verify workspace access (requires admin role)
    verify_workspace_access(key.workspace_id, current_user, db, "admin")
    
    # Log activity before deletion
    activity = WorkspaceActivity(
        workspace_id=key.workspace_id,
        user_id=current_user.id,
        action="ai_key.deleted",
        resource_type="ai_key",
        resource_id=key.id,
        resource_name=key.key_name
    )
    db.add(activity)
    
    db.delete(key)
    db.commit()
    
    return {"message": "AI key deleted successfully"}

@router.get("/{key_id}/usage", response_model=AIKeyUsageResponse)
async def get_ai_key_usage(
    key_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics for an AI key"""
    key = db.query(AIKey).filter(AIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="AI key not found")
    
    # Verify workspace access
    verify_workspace_access(key.workspace_id, current_user, db, "developer")
    
    # Get usage data
    start_date = datetime.utcnow() - timedelta(days=days)
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    usage_data = db.query(AIKeyUsage).filter(
        AIKeyUsage.key_id == key_id,
        AIKeyUsage.date >= start_date
    ).order_by(AIKeyUsage.date).all()
    
    # Calculate totals
    total_requests = sum(u.requests for u in usage_data)
    total_tokens = sum(u.tokens_input + u.tokens_output for u in usage_data)
    total_cost = sum(u.cost for u in usage_data)
    
    # Calculate this month's usage
    month_usage = [u for u in usage_data if u.date >= current_month]
    requests_this_month = sum(u.requests for u in month_usage)
    tokens_this_month = sum(u.tokens_input + u.tokens_output for u in month_usage)
    cost_this_month = sum(u.cost for u in month_usage)
    
    # Group by day
    daily_usage = []
    current_date = start_date.date()
    while current_date <= datetime.utcnow().date():
        day_usage = [u for u in usage_data if u.date.date() == current_date]
        daily_usage.append({
            "date": current_date.isoformat(),
            "requests": sum(u.requests for u in day_usage),
            "tokens": sum(u.tokens_input + u.tokens_output for u in day_usage),
            "cost": sum(u.cost for u in day_usage)
        })
        current_date = current_date + timedelta(days=1)
    
    # Model breakdown
    model_breakdown = {}
    for usage in usage_data:
        if usage.model:
            model_breakdown[usage.model] = model_breakdown.get(usage.model, 0) + usage.requests
    
    return AIKeyUsageResponse(
        key_id=key_id,
        key_name=key.key_name,
        provider=key.provider,
        total_requests=total_requests,
        total_tokens=total_tokens,
        total_cost=total_cost,
        requests_this_month=requests_this_month,
        tokens_this_month=tokens_this_month,
        cost_this_month=cost_this_month,
        daily_usage=daily_usage,
        model_breakdown=model_breakdown
    )

@router.post("/{key_id}/test")
async def test_ai_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test an AI key by making a simple API call"""
    key = db.query(AIKey).filter(AIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="AI key not found")
    
    # Verify workspace access
    verify_workspace_access(key.workspace_id, current_user, db, "developer")
    
    # Decrypt the key
    try:
        api_key = decrypt_api_key(key.encrypted_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to decrypt API key")
    
    # Test based on provider
    test_result = {"success": False, "message": "", "model": "", "response": ""}
    
    try:
        if key.provider == "openai":
            import openai
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'API key is working' in 5 words or less"}],
                max_tokens=20
            )
            test_result["success"] = True
            test_result["model"] = "gpt-3.5-turbo"
            test_result["response"] = response.choices[0].message.content
            test_result["message"] = "OpenAI API key is valid and working"
            
        elif key.provider == "anthropic":
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            response = client.completions.create(
                model="claude-2",
                prompt="Say 'API key is working' in 5 words or less",
                max_tokens_to_sample=20
            )
            test_result["success"] = True
            test_result["model"] = "claude-2"
            test_result["response"] = response.completion
            test_result["message"] = "Anthropic API key is valid and working"
            
        else:
            test_result["message"] = f"Testing for {key.provider} provider is not yet implemented"
            test_result["success"] = None  # Unknown status
            
    except Exception as e:
        test_result["message"] = f"API key test failed: {str(e)}"
        test_result["success"] = False
    
    # Update last used timestamp
    key.last_used = datetime.utcnow()
    db.commit()
    
    return test_result
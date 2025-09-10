"""
Environment Variables API Routes
Manages environment variables with hierarchical inheritance
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from src.database import get_db
from src.auth import get_current_user
from src.environment_manager import EnvironmentManager, EnvironmentVariable

router = APIRouter(prefix="/api/environments", tags=["Environments"])

class CreateEnvironmentRequest(BaseModel):
    """Request model for creating environment"""
    name: str
    variables: Dict[str, Any]
    scope: str = "workspace"
    workspace_id: Optional[int] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None

class UpdateVariableRequest(BaseModel):
    """Request model for updating a variable"""
    key: Optional[str] = None
    value: Optional[str] = None
    is_secret: Optional[bool] = None
    description: Optional[str] = None

class ResolveVariablesRequest(BaseModel):
    """Request model for resolving variables in text"""
    text: str
    workspace_id: Optional[int] = None
    collection_id: Optional[str] = None
    request_vars: Optional[Dict[str, Any]] = None

@router.post("/create")
async def create_environment(
    request: CreateEnvironmentRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new environment with variables"""
    
    try:
        environment = EnvironmentManager.create_environment(
            db=db,
            user_id=current_user.id,
            name=request.name,
            variables=request.variables,
            scope=request.scope,
            workspace_id=request.workspace_id,
            parent_id=request.parent_id
        )
        
        return {
            "success": True,
            "environment": environment
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tree")
async def get_environment_tree(
    workspace_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the complete environment variable tree with inheritance hierarchy"""
    
    tree = EnvironmentManager.get_environment_tree(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id
    )
    
    return {
        "success": True,
        "tree": tree
    }

@router.post("/resolve")
async def resolve_variables(
    request: ResolveVariablesRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Resolve variables in text with inheritance"""
    
    resolved_text = EnvironmentManager.resolve_variables(
        db=db,
        user_id=current_user.id,
        text=request.text,
        workspace_id=request.workspace_id,
        collection_id=request.collection_id,
        request_scope_vars=request.request_vars
    )
    
    return {
        "success": True,
        "original": request.text,
        "resolved": resolved_text
    }

@router.get("/list")
async def list_variables(
    scope: Optional[str] = Query(None, regex="^(global|workspace|collection|request)$"),
    workspace_id: Optional[int] = Query(None),
    collection_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List environment variables filtered by scope"""
    
    query = db.query(EnvironmentVariable).filter(
        EnvironmentVariable.user_id == current_user.id,
        EnvironmentVariable.is_active == True
    )
    
    if scope:
        query = query.filter(EnvironmentVariable.scope == scope)
    
    if workspace_id:
        query = query.filter(EnvironmentVariable.workspace_id == workspace_id)
    
    if collection_id:
        query = query.filter(EnvironmentVariable.collection_id == collection_id)
    
    variables = query.all()
    
    return {
        "success": True,
        "variables": [
            EnvironmentManager._variable_to_dict(var)
            for var in variables
        ]
    }

@router.put("/variable/{variable_id}")
async def update_variable(
    variable_id: int,
    request: UpdateVariableRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an environment variable"""
    
    try:
        updated_var = EnvironmentManager.update_variable(
            db=db,
            user_id=current_user.id,
            variable_id=variable_id,
            key=request.key,
            value=request.value,
            is_secret=request.is_secret
        )
        
        return {
            "success": True,
            "variable": updated_var
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/variable/{variable_id}")
async def delete_variable(
    variable_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an environment variable"""
    
    success = EnvironmentManager.delete_variable(
        db=db,
        user_id=current_user.id,
        variable_id=variable_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Variable not found")
    
    return {
        "success": True,
        "message": "Variable deleted successfully"
    }

@router.post("/bulk-update")
async def bulk_update_variables(
    variables: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Bulk update multiple variables"""
    
    updated = []
    errors = []
    
    for var_data in variables:
        try:
            if "id" in var_data:
                updated_var = EnvironmentManager.update_variable(
                    db=db,
                    user_id=current_user.id,
                    variable_id=var_data["id"],
                    key=var_data.get("key"),
                    value=var_data.get("value"),
                    is_secret=var_data.get("is_secret")
                )
                updated.append(updated_var)
        except Exception as e:
            errors.append({
                "variable_id": var_data.get("id"),
                "error": str(e)
            })
    
    return {
        "success": True,
        "updated": updated,
        "errors": errors
    }

@router.get("/dynamic-types")
async def get_dynamic_variable_types():
    """Get available dynamic variable types"""
    
    return {
        "success": True,
        "types": [
            {
                "name": "timestamp",
                "description": "Current Unix timestamp in seconds",
                "example": "1704067200"
            },
            {
                "name": "timestamp_ms",
                "description": "Current Unix timestamp in milliseconds",
                "example": "1704067200000"
            },
            {
                "name": "uuid",
                "description": "Random UUID (hex format)",
                "example": "a1b2c3d4e5f6"
            },
            {
                "name": "uuid_v4",
                "description": "Random UUID v4",
                "example": "123e4567-e89b-12d3-a456-426614174000"
            },
            {
                "name": "date",
                "description": "Current date (YYYY-MM-DD)",
                "example": "2024-01-01"
            },
            {
                "name": "datetime",
                "description": "Current datetime (ISO format)",
                "example": "2024-01-01T12:00:00"
            },
            {
                "name": "random_int",
                "description": "Random integer (1-1000000)",
                "example": "42"
            },
            {
                "name": "random_email",
                "description": "Random test email address",
                "example": "test_a1b2c3d4@example.com"
            }
        ]
    }

@router.post("/test-resolution")
async def test_variable_resolution(
    text: str = Query(..., description="Text containing variables to resolve"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test variable resolution with current environment"""
    
    # Show how the text would be resolved at each scope level
    results = {}
    
    # Global scope only
    global_resolved = EnvironmentManager.resolve_variables(
        db=db,
        user_id=current_user.id,
        text=text,
        workspace_id=None,
        collection_id=None,
        request_scope_vars=None
    )
    results["global"] = global_resolved
    
    # With workspace (if user has one)
    # You'd get this from user's current workspace
    workspace_resolved = EnvironmentManager.resolve_variables(
        db=db,
        user_id=current_user.id,
        text=text,
        workspace_id=1,  # Example workspace ID
        collection_id=None,
        request_scope_vars=None
    )
    results["workspace"] = workspace_resolved
    
    return {
        "success": True,
        "original": text,
        "resolutions": results
    }